"""Natural-language assistant for lab progress insights."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import base64
import re
from typing import Any
from typing import Literal
from urllib.parse import quote, unquote, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import cast, func, Numeric
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.models.interaction import InteractionLog
from lms_backend.models.item import ItemRecord
from lms_backend.models.learner import Learner
from lms_backend.routers.analytics import _find_lab_and_tasks
from lms_backend.settings import settings

router = APIRouter()


class AssistantRequest(BaseModel):
    lab: str = Field(..., description="Lab identifier, e.g. lab-08")
    question: str = Field(
        default="What should I focus on next?",
        description="Question from the student",
    )
    language: Literal["ru", "en"] = Field(
        default="en",
        description="Assistant response language",
    )
    github_url: str | None = Field(
        default=None,
        description="Optional GitHub profile or repository URL to inspect",
    )


class AssistantMetrics(BaseModel):
    lab: str
    lab_title: str
    completion_rate: float
    passed: int
    total: int
    weakest_task: str | None = None
    weakest_task_score: float | None = None
    strongest_group: str | None = None
    strongest_group_score: float | None = None
    recent_submissions: int
    previous_submissions: int


class AssistantResponse(BaseModel):
    answer: str
    focus_points: list[str]
    metrics: AssistantMetrics
    sources: list[str]
    mode: Literal["llm", "fallback"]


class GitHubFileContext(BaseModel):
    repo: str
    path: str
    excerpt: str


class GitHubRepoContext(BaseModel):
    name: str
    url: str
    description: str | None = None
    files: list[GitHubFileContext] = Field(default_factory=list)


async def _task_scores(session: AsyncSession, task_ids: list[int]) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    for task_id in task_ids:
        task = await session.get(ItemRecord, task_id)
        if task is None:
            continue

        stmt = select(
            func.round(cast(func.avg(InteractionLog.score), Numeric), 1).label("avg_score"),
            func.count().label("attempts"),
        ).where(
            InteractionLog.item_id == task_id,
            col(InteractionLog.score).is_not(None),
        )
        row = (await session.exec(stmt)).first()
        avg_score = float(row[0]) if row and row[0] is not None else 0.0
        attempts = int(row[1]) if row and row[1] is not None else 0
        scores.append({"title": task.title, "avg_score": avg_score, "attempts": attempts})

    return scores


async def _group_scores(session: AsyncSession, item_ids: list[int]) -> list[dict[str, Any]]:
    stmt = (
        select(
            Learner.student_group,
            func.round(cast(func.avg(InteractionLog.score), Numeric), 1).label("avg_score"),
            func.count(func.distinct(InteractionLog.learner_id)).label("students"),
        )
        .join(Learner, col(InteractionLog.learner_id) == col(Learner.id))
        .where(
            col(InteractionLog.item_id).in_(item_ids),
            col(InteractionLog.score).is_not(None),
        )
        .group_by(col(Learner.student_group))
        .order_by(col(Learner.student_group))
    )
    rows = (await session.exec(stmt)).all()
    return [
        {
            "group": group or "Unknown",
            "avg_score": float(avg_score) if avg_score is not None else 0.0,
            "students": int(students),
        }
        for group, avg_score, students in rows
    ]


async def _submission_trend(session: AsyncSession, item_ids: list[int]) -> tuple[int, int]:
    now = datetime.now(UTC).replace(tzinfo=None)
    recent_cutoff = now - timedelta(days=7)
    previous_cutoff = now - timedelta(days=14)

    recent_stmt = select(func.count()).where(
        col(InteractionLog.item_id).in_(item_ids),
        col(InteractionLog.created_at) >= recent_cutoff,
    )
    previous_stmt = select(func.count()).where(
        col(InteractionLog.item_id).in_(item_ids),
        col(InteractionLog.created_at) >= previous_cutoff,
        col(InteractionLog.created_at) < recent_cutoff,
    )
    recent = int((await session.exec(recent_stmt)).one())
    previous = int((await session.exec(previous_stmt)).one())
    return recent, previous


def _normalize_github_url(value: str) -> str | None:
    try:
        parsed = urlparse(value.strip())
    except Exception:
        return None

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None
    if parts[0] == "orgs" and len(parts) >= 2:
        return f"orgs/{parts[1]}"
    if parts[0] in {"users", "u"} and len(parts) >= 2:
        return parts[1]
    if len(parts) >= 2 and parts[0] != "tab":
        return "/".join(parts[:2])
    return parts[0]


def _extract_username_from_profile(url: str) -> str | None:
    normalized = _normalize_github_url(url)
    if not normalized:
        return None
    if normalized.startswith("orgs/"):
        return normalized.split("/", 1)[1]
    if normalized.startswith("tab="):
        return None
    parts = normalized.split("/")
    if len(parts) == 1:
        return parts[0]
    if len(parts) >= 2:
        return parts[0]
    return None


def _extract_owner_repo(url: str) -> tuple[str | None, str | None]:
    normalized = _normalize_github_url(url)
    if not normalized:
        return None, None
    if normalized.startswith("orgs/"):
        return None, None
    parts = normalized.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def _extract_org_name(url: str) -> str | None:
    normalized = _normalize_github_url(url)
    if not normalized:
        return None
    if normalized.startswith("orgs/"):
        return normalized.split("/", 1)[1]
    return None


async def _github_get_json(url: str) -> Any:
    async with httpx.AsyncClient(
        timeout=20.0,
        verify=False,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "LabLens"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def _github_get_text(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=20.0,
        verify=False,
        headers={"User-Agent": "LabLens"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def _excerpt_text(content: str, *, max_lines: int = 12, max_chars: int = 1200) -> str:
    lines = [line.rstrip() for line in content.splitlines() if line.strip()]
    if not lines:
        return ""
    picked: list[str] = []
    for line in lines:
        if len(picked) >= max_lines:
            break
        if re.match(r"^(#{1,6}\s+|\d+[.)]\s+|[-*]\s+|Step\s+\d+[:.]?)", line, flags=re.IGNORECASE):
            picked.append(line)
    if not picked:
        picked = lines[:max_lines]
    excerpt = "\n".join(picked)
    return excerpt[:max_chars]


def _extract_step_lines(text: str) -> list[str]:
    steps: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(#{1,6}\s+|\d+[.)]\s+|[-*]\s+|Step\s+\d+[:.]?)", line, flags=re.IGNORECASE):
            cleaned = re.sub(r"^#{1,6}\s+", "", line)
            steps.append(cleaned)
    return steps


def _repo_relevance_score(repo_data: dict[str, Any]) -> tuple[int, str]:
    name = str(repo_data.get("name", "")).lower()
    description = str(repo_data.get("description", "") or "").lower()
    tokens = f"{name} {description}"

    if "all-labs" in tokens:
        priority = 0
    elif re.search(r"lab[-_ ]?\d+", tokens):
        priority = 1
    elif any(token in tokens for token in ["lab", "labs", "task", "exercise", "instruction", "guide"]):
        priority = 2
    else:
        priority = 3

    return priority, name


async def _probe_common_repo_files(owner: str, repo: str) -> list[GitHubFileContext]:
    common_paths = [
        "README.md",
        "README",
        "docs/README.md",
        "docs/Question bank.md",
        "docs/question bank.md",
        "docs/task.md",
        "docs/tasks.md",
        "docs/guide.md",
        "docs/instructions.md",
        "instruction.md",
        "instructions.md",
        "task.md",
        "tasks.md",
        "guide.md",
        "spec.md",
        "lab.md",
    ]
    branches = ["main", "master"]

    results: list[GitHubFileContext] = []
    for branch in branches:
        for path in common_paths:
            try:
                encoded_path = quote(path)
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded_path}"
                async with httpx.AsyncClient(timeout=20.0, verify=False, headers={"User-Agent": "LabLens"}) as client:
                    response = await client.get(raw_url)
                    if response.status_code >= 400:
                        continue
                    excerpt = _excerpt_text(response.text)
                    if excerpt:
                        results.append(
                            GitHubFileContext(
                                repo=f"{owner}/{repo}",
                                path=path,
                                excerpt=excerpt,
                            )
                        )
            except Exception:
                continue
            if len(results) >= 3:
                return results
    return results


async def _fetch_repo_files(owner: str, repo: str) -> list[GitHubFileContext]:
    repo_data = await _github_get_json(f"https://api.github.com/repos/{owner}/{repo}")
    default_branch = repo_data.get("default_branch") or "main"
    tree_data = await _github_get_json(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    )
    tree = tree_data.get("tree", []) if isinstance(tree_data, dict) else []
    paths = [
        item.get("path")
        for item in tree
        if item.get("type") == "blob" and item.get("path")
    ]
    priority = [
        path
        for path in paths
        if re.search(r"(^|/)(README|readme|docs?|guide|lab|task|exercise|steps?|instruction)\.(md|txt)$", path)
        or re.search(r"(^|/)(README|readme)(\.[^/]+)?$", path)
    ]
    if not priority:
        priority = [path for path in paths if path.lower().endswith((".md", ".txt"))]

    selected = priority[:3]
    results: list[GitHubFileContext] = []
    for path in selected:
        try:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path}"
            async with httpx.AsyncClient(timeout=20.0, verify=False, headers={"User-Agent": "LabLens"}) as client:
                response = await client.get(raw_url)
                response.raise_for_status()
                excerpt = _excerpt_text(response.text)
                if excerpt:
                    results.append(
                        GitHubFileContext(
                            repo=f"{owner}/{repo}",
                            path=path,
                            excerpt=excerpt,
                        )
                    )
        except Exception:
            continue
    return results


async def _fetch_repo_files_from_html(owner: str, repo: str) -> list[GitHubFileContext]:
    results = await _probe_common_repo_files(owner, repo)
    if results:
        return results

    try:
        html = await _github_get_text(f"https://github.com/{owner}/{repo}")
    except Exception:
        return []

    candidate_files: list[tuple[str, str]] = []
    visited_pages: set[str] = set()
    pages_to_visit: list[str] = [f"https://github.com/{owner}/{repo}"]

    while pages_to_visit and len(visited_pages) < 8:
        page_url = pages_to_visit.pop(0)
        if page_url in visited_pages:
            continue
        visited_pages.add(page_url)

        try:
            page_html = html if page_url.endswith(f"/{owner}/{repo}") else await _github_get_text(page_url)
        except Exception:
            continue

        for match in re.finditer(rf'href="/{re.escape(owner)}/{re.escape(repo)}/(blob|tree)/([^\"]+)"', page_html):
            kind = match.group(1)
            path = unquote(match.group(2))
            if kind == "tree":
                tree_url = f"https://github.com/{owner}/{repo}/tree/{path}"
                if tree_url not in visited_pages and tree_url not in pages_to_visit:
                    pages_to_visit.append(tree_url)
                continue

            blob_path = path
            if "/" not in blob_path:
                continue
            branch, file_path = blob_path.split("/", 1)
            if file_path and (file_path, branch) not in candidate_files:
                candidate_files.append((file_path, branch))

    priority = [
        (path, branch)
        for path, branch in candidate_files
        if re.search(r"(^|/)(README|readme|docs?|guide|lab|task|exercise|steps?|instruction)(\.[^/]+)?$", path)
        or re.search(r"(^|/)(README|readme)(\.[^/]+)?$", path)
    ]
    if not priority:
        priority = [
            (path, branch)
            for path, branch in candidate_files
            if path.lower().endswith((".md", ".txt", ".rst", ".adoc"))
        ]
    if not priority:
        priority = candidate_files

    selected = priority[:5]
    results: list[GitHubFileContext] = []
    for path, branch in selected:
        try:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            async with httpx.AsyncClient(timeout=20.0, verify=False, headers={"User-Agent": "LabLens"}) as client:
                response = await client.get(raw_url)
                response.raise_for_status()
                excerpt = _excerpt_text(response.text)
                if excerpt:
                    results.append(GitHubFileContext(repo=f"{owner}/{repo}", path=path, excerpt=excerpt))
        except Exception:
            continue
    return results


async def _fetch_org_repo_names_from_html(org_name: str) -> list[str]:
    try:
        html = await _github_get_text(f"https://github.com/orgs/{org_name}/repositories")
    except Exception:
        return []

    repo_names: list[str] = []
    for match in re.finditer(rf'href="/{re.escape(org_name)}/([^"]+)"', html):
        repo_name = match.group(1)
        if repo_name and repo_name not in repo_names and not repo_name.startswith("?"):
            repo_names.append(repo_name)

    # Filter obvious non-repo and navigation links.
    filtered: list[str] = []
    for name in repo_names:
        if "/" in name:
            continue
        if not re.match(r"^[A-Za-z0-9_.-]+$", name):
            continue
        if any(token in name.lower() for token in ["settings", "members", "projects", "sponsors", "repositories", "stargazers", "watchers", "issues", "pulls", "forks"]):
            continue
        filtered.append(name)
    return filtered


async def _fetch_github_context(github_url: str) -> list[GitHubRepoContext]:
    org_name = _extract_org_name(github_url)
    username = _extract_username_from_profile(github_url)
    owner, repo = _extract_owner_repo(github_url)
    contexts: list[GitHubRepoContext] = []

    if owner and repo:
        try:
            files = await _fetch_repo_files(owner, repo)
            if not files:
                files = await _fetch_repo_files_from_html(owner, repo)
            repo_data = await _github_get_json(f"https://api.github.com/repos/{owner}/{repo}")
            contexts.append(
                GitHubRepoContext(
                    name=f"{owner}/{repo}",
                    url=f"https://github.com/{owner}/{repo}",
                    description=repo_data.get("description"),
                    files=files,
                )
            )
        except Exception:
            contexts.append(
                GitHubRepoContext(
                    name=f"{owner}/{repo}",
                    url=f"https://github.com/{owner}/{repo}",
                    description=None,
                    files=[],
                )
            )
        return contexts

    if org_name:
        repos: list[dict[str, Any]] = []
        try:
            github_repos = await _github_get_json(f"https://api.github.com/orgs/{org_name}/repos?per_page=8&sort=updated")
            if isinstance(github_repos, list):
                repos = github_repos
        except Exception:
            repos = []

        if not repos:
            repo_names = await _fetch_org_repo_names_from_html(org_name)
            repos = [{"name": repo_name, "owner": {"login": org_name}, "html_url": f"https://github.com/{org_name}/{repo_name}"} for repo_name in repo_names]

        if not repos:
            return contexts

        ranked_repos = sorted(repos, key=_repo_relevance_score)

        for repo_data in ranked_repos[:4]:
            repo_name = repo_data.get("name")
            owner_login = repo_data.get("owner", {}).get("login", org_name)
            if not repo_name:
                continue
            try:
                files = await _fetch_repo_files(owner_login, repo_name)
                if not files:
                    files = await _fetch_repo_files_from_html(owner_login, repo_name)
            except Exception:
                files = []
            contexts.append(
                GitHubRepoContext(
                    name=f"{owner_login}/{repo_name}",
                    url=str(repo_data.get("html_url") or f"https://github.com/{owner_login}/{repo_name}"),
                    description=repo_data.get("description"),
                    files=files,
                )
            )
        return contexts

    if not username:
        return contexts

    repos = await _github_get_json(f"https://api.github.com/users/{username}/repos?per_page=6&sort=updated")
    if not isinstance(repos, list):
        return contexts

    ranked_repos = sorted(
        repos,
        key=lambda repo_data: (
            0
            if any(token in str(repo_data.get("name", "")).lower() for token in ["lab", "all-labs", "labs"])
            else 1,
            str(repo_data.get("name", "")),
        ),
    )

    for repo_data in ranked_repos[:4]:
        repo_name = repo_data.get("name")
        owner_login = repo_data.get("owner", {}).get("login", username)
        if not repo_name:
            continue
        try:
            files = await _fetch_repo_files(owner_login, repo_name)
            if not files:
                files = await _fetch_repo_files_from_html(owner_login, repo_name)
            description = repo_data.get("description")
        except Exception:
            files = []
            description = repo_data.get("description")
        contexts.append(
            GitHubRepoContext(
                name=f"{owner_login}/{repo_name}",
                url=str(repo_data.get("html_url") or f"https://github.com/{owner_login}/{repo_name}"),
                description=description,
                files=files,
            )
        )

    return contexts


def _build_github_summary(contexts: list[GitHubRepoContext], *, language: Literal["ru", "en"] = "ru") -> str:
    if not contexts:
        return ""

    is_ru = language == "ru"
    lines = ["GitHub review:"]
    if is_ru:
        lines.append("Я посмотрел репозитории и взял из них файлы с инструкциями, README и шагами.")
    else:
        lines.append("I checked the repositories and pulled files with instructions, README files, and steps.")

    for repo_context in contexts:
        lines.append(f"- {repo_context.name}")
        if repo_context.files:
            for file_context in repo_context.files[:3]:
                lines.append(f"  - {file_context.path}")

    return "\n".join(lines).strip()


def _build_github_walkthrough(contexts: list[GitHubRepoContext], *, language: Literal["ru", "en"] = "ru") -> str:
    if not contexts:
        return ""

    is_ru = language == "ru"
    lines: list[str] = []
    if is_ru:
        lines.append("GitHub walkthrough:")
        lines.append("Я открыл репозитории, нашел файлы с инструкциями и выписал, что делать первым делом.")
    else:
        lines.append("GitHub walkthrough:")
        lines.append("I opened the repositories, found the instruction files, and pulled out what to do first.")

    for index, repo_context in enumerate(contexts[:4], start=1):
        lines.append(f"{index}. Repository: {repo_context.name}")
        if repo_context.description:
            lines.append(f"   Description: {repo_context.description}")
        lines.append(f"   Open: {repo_context.url}")

        if not repo_context.files:
            lines.append(
                "   No instruction file was found automatically; open README.md, docs/, or any file named lab/task/guide/instruction first."
                if language == "en"
                else "   Автоматически не найден файл с инструкцией; сначала откройте README.md, docs/ или любой файл с названием lab/task/guide/instruction."
            )
            continue

        primary_file = repo_context.files[0]
        lines.append(f"   First file to open: {primary_file.path}")

        step_lines = _extract_step_lines(primary_file.excerpt)
        if not step_lines:
            for extra_file in repo_context.files[1:]:
                step_lines = _extract_step_lines(extra_file.excerpt)
                if step_lines:
                    primary_file = extra_file
                    lines[-1] = f"   First file to open: {primary_file.path}"
                    break

        if step_lines:
            lines.append("   What the file says to do:")
            for step in step_lines[:4]:
                lines.append(f"   - {step}")
        else:
            lines.append(
                "   The file has no explicit numbered steps, so use the headings and README sections in order."
                if language == "en"
                else "   В файле нет явных нумерованных шагов, поэтому идите по заголовкам и разделам README по порядку."
            )

    return "\n".join(lines).strip()


def _format_github_context(contexts: list[GitHubRepoContext]) -> str:
    if not contexts:
        return ""

    lines: list[str] = ["GitHub context:"]
    for repo_context in contexts:
        lines.append(f"Repository: {repo_context.name}")
        if repo_context.description:
            lines.append(f"Description: {repo_context.description}")
        lines.append(f"URL: {repo_context.url}")
        for file_context in repo_context.files:
            lines.append(f"File: {file_context.path}")
            lines.append(file_context.excerpt)
        lines.append("")
    return "\n".join(lines).strip()


def _build_focus_points(
    question: str,
    language: Literal["ru", "en"],
    completion_rate: float,
    weakest_task: dict[str, Any] | None,
    strongest_group: dict[str, Any] | None,
    recent_submissions: int,
    previous_submissions: int,
) -> list[str]:
    normalized = question.lower().strip()
    asks_ops = any(
        word in normalized
        for word in ["виртуал", "vm", "ssh", "remote-ssh", "deploy", "деплой", "docker", "server", "сервер"]
    )
    asks_plan = any(word in normalized for word in ["plan", "steps", "roadmap", "план", "шаг", "по дням"])
    asks_risks = any(word in normalized for word in ["risk", "problem", "issue", "риск", "проблем"])
    asks_compare = any(word in normalized for word in ["compare", "benchmark", "group", "срав", "группа"])
    is_ru = language == "ru"

    focus_points: list[str] = []

    if asks_ops:
        if is_ru:
            return [
                "Проверьте доступ: адрес хоста, логин и SSH-ключ.",
                "Подключитесь через ssh user@host или VS Code Remote-SSH.",
                "После входа проверьте окружение: pwd, ls, docker ps и логи сервисов.",
            ]
        return [
            "Verify access basics: host address, username, and SSH key.",
            "Connect via ssh user@host or VS Code Remote-SSH.",
            "After login, validate environment with pwd, ls, docker ps, and service logs.",
        ]

    if asks_plan and weakest_task is not None:
        if is_ru:
            focus_points.append(
                f"Шаг 1: разберите {weakest_task['title']} (средний балл {weakest_task['avg_score']:.1f}) и закройте все очевидные пробелы."
            )
            focus_points.append("Шаг 2: выполните тренировочную попытку с ограничением по времени и сразу сравните результат с графиками.")
            focus_points.append("Шаг 3: пройдитесь по краевым случаям, исправьте ошибки и только потом переходите дальше.")
        else:
            focus_points.append(
                f"Step 1: work through {weakest_task['title']} ({weakest_task['avg_score']:.1f} avg) and close the obvious gaps."
            )
            focus_points.append("Step 2: run a timed practice submission and compare the result with the charts immediately.")
            focus_points.append("Step 3: check edge cases, fix mistakes, and only then move on to the next task.")
        return focus_points[:3]
    elif asks_risks and weakest_task is not None:
        if is_ru:
            focus_points.append(
                f"Главный риск: у {weakest_task['title']} самый низкий балл ({weakest_task['avg_score']:.1f})."
            )
        else:
            focus_points.append(
                f"Primary risk: {weakest_task['title']} has the lowest score ({weakest_task['avg_score']:.1f})."
            )
        if recent_submissions < previous_submissions:
            focus_points.append(
                "Вторичный риск: активность снизилась неделя к неделе, это может ухудшить закрепление материала."
                if is_ru
                else "Secondary risk: activity dropped week-over-week, which can hurt retention."
            )
        else:
            focus_points.append(
                "Вторичный риск: высокий темп может скрыть регрессии, если пропускать проверки."
                if is_ru
                else "Secondary risk: high pace can hide regressions if checks are skipped."
            )
    elif asks_compare and strongest_group is not None:
        focus_points.append(
            f"Референсная группа: {strongest_group['group']} со средним баллом {strongest_group['avg_score']:.1f}."
            if is_ru
            else f"Benchmark group: {strongest_group['group']} at {strongest_group['avg_score']:.1f} average score."
        )
        if weakest_task is not None:
            focus_points.append(
                f"Главный разрыв относительно референса: сначала улучшите {weakest_task['title']}."
                if is_ru
                else f"Main gap vs benchmark: improve {weakest_task['title']} first."
            )
    elif weakest_task is not None:
        focus_points.append(
            f"Начните с {weakest_task['title']} — у нее самый низкий средний балл ({weakest_task['avg_score']:.1f})."
            if is_ru
            else f"Start with {weakest_task['title']} — it has the lowest average score ({weakest_task['avg_score']:.1f})."
        )

    if completion_rate < 60:
        focus_points.append(
            "Лаба пока в риск-зоне, сделайте короткий обзорный прогон перед следующей сдачей."
            if is_ru
            else "The lab is still risky overall, so aim for one short review pass before the next submission."
        )
    elif completion_rate < 80:
        focus_points.append(
            "Динамика хорошая, но есть запас для роста: вернитесь к самой слабой задаче."
            if is_ru
            else "The lab is moving well, but there is still room to raise the score by revisiting the weak task."
        )
    else:
        focus_points.append(
            "Лаба в хорошем состоянии. Держите темп и используйте дашборд, чтобы не допустить регрессий."
            if is_ru
            else "This lab is in good shape. Keep the current pace and use the dashboard to avoid regressions."
        )

    if strongest_group is not None:
        focus_points.append(
            f"{strongest_group['group']} сейчас впереди со средним баллом {strongest_group['avg_score']:.1f}."
            if is_ru
            else f"{strongest_group['group']} is currently ahead with an average of {strongest_group['avg_score']:.1f}."
        )

    if recent_submissions < previous_submissions:
        focus_points.append(
            "Активность сдач снизилась на этой неделе, запланируйте следующий практический блок раньше."
            if is_ru
            else "Submission activity dropped this week, so schedule the next practice block sooner."
        )
    elif recent_submissions > previous_submissions:
        focus_points.append(
            "Недавняя активность выросла — это хороший сигнал для закрепления и завершения лабы."
            if is_ru
            else "Recent activity is up, which is a good sign for retention and completion."
        )

    return focus_points[:4]


def _compose_fallback_answer(
    question: str,
    language: Literal["ru", "en"],
    lab_title: str,
    completion_rate: float,
    weakest_task: dict[str, Any] | None,
    strongest_group: dict[str, Any] | None,
    task_scores: list[dict[str, Any]],
) -> str:
    normalized = question.lower().strip()
    is_ru = language == "ru"

    asks_vm = any(
        word in normalized
        for word in ["виртуал", "vm", "ssh", "подключ", "connect", "remote-ssh", "сервер"]
    )
    asks_deploy = any(
        word in normalized
        for word in ["deploy", "деплой", "docker", "compose", "backend", "запуск"]
    )

    if asks_vm:
        return (
            "Подключение к VM обычно выглядит так: (1) проверьте SSH-ключ и адрес хоста; "
            "(2) выполните ssh user@host в терминале или подключитесь через VS Code Remote-SSH; "
            "(3) после входа проверьте окружение командами pwd, ls, docker ps. "
            "Если доступ не работает, проверьте порт 22, firewall и правильность ключа."
            if is_ru
            else "Typical VM connection flow: (1) verify your SSH key and host address; "
            "(2) run ssh user@host in terminal or connect via VS Code Remote-SSH; "
            "(3) after login, validate environment with pwd, ls, docker ps. "
            "If access fails, check port 22, firewall rules, and the correct key."
        )

    if asks_deploy:
        return (
            "Быстрый план деплоя: (1) обновите репозиторий и .env на VM; "
            "(2) поднимите сервисы через docker compose up -d --build; "
            "(3) проверьте логи (docker compose logs -f) и доступность API/фронтенда. "
            "При ошибках сначала смотрите переменные окружения и занятые порты."
            if is_ru
            else "Quick deployment plan: (1) update repo and .env on VM; "
            "(2) start services with docker compose up -d --build; "
            "(3) check logs (docker compose logs -f) and verify API/frontend availability. "
            "For failures, first inspect env vars and port conflicts."
        )

    asks_how_to_do = any(
        word in normalized
        for word in ["как", "выполн", "сделать", "сдать", "complete", "finish", "how to", "steps"]
    )

    if asks_how_to_do and task_scores:
        ranked = sorted(task_scores, key=lambda t: t["avg_score"])[:3]
        if is_ru:
            checklist = "; ".join(
                [
                    f"{index + 1}) {task['title']} (текущий средний балл {task['avg_score']:.1f})"
                    for index, task in enumerate(ranked)
                ]
            )
            return (
                f"Для текущей лабы {lab_title} действуйте по шагам: {checklist}. "
                "Начните с просмотра структуры лабы и задач, затем выполните первую задачу, "
                "проверьте результат, исправьте ошибки и переходите к следующей задаче только после этого."
            )
        checklist = "; ".join(
            [
                f"{index + 1}) {task['title']} (current avg {task['avg_score']:.1f})"
                for index, task in enumerate(ranked)
            ]
        )
        return (
            f"For the selected lab {lab_title}, follow this order: {checklist}. "
            "Start by reviewing the lab structure, finish the first task, re-check the result, then move to the next one."
        )

    if any(word in normalized for word in ["next", "focus", "what should i do", "что делать", "с чего начать"]):
        if weakest_task is not None:
            return (
                f"Сначала сфокусируйтесь на {weakest_task['title']}. У {lab_title} сейчас {completion_rate:.1f}% завершения, "
                f"и у этой задачи самый низкий средний балл ({weakest_task['avg_score']:.1f})."
                if is_ru
                else f"Focus on {weakest_task['title']} first. {lab_title} is at {completion_rate:.1f}% completion, "
                f"and this task has the lowest average score ({weakest_task['avg_score']:.1f})."
            )

    if any(word in normalized for word in ["weak", "risk", "problem", "самый слабый", "риск"]):
        if weakest_task is not None:
            return (
                f"Самая слабая часть {lab_title} — {weakest_task['title']}. Ее нужно подтянуть в первую очередь."
                if is_ru
                else f"The weakest part of {lab_title} is {weakest_task['title']}. It needs attention before the rest of the lab."
            )

    if any(word in normalized for word in ["group", "группа"]):
        if strongest_group is not None:
            return (
                f"Лидирует группа {strongest_group['group']} со средним баллом {strongest_group['avg_score']:.1f}."
                if is_ru
                else f"{strongest_group['group']} is leading with an average score of {strongest_group['avg_score']:.1f}."
            )

    if any(word in normalized for word in ["plan", "steps", "roadmap", "план", "шаг", "по дням"]):
        if weakest_task is not None:
            return (
                f"План: (1) сначала улучшите {weakest_task['title']}; "
                f"(2) сделайте полный тренировочный прогон; "
                f"(3) проверьте слабые места и финализируйте перед дедлайном."
                if is_ru
                else f"Plan: (1) Improve {weakest_task['title']} first; "
                f"(2) run a full practice submission; "
                f"(3) review weak checks and finalize before deadline."
            )

    return (
        f"{lab_title} сейчас на уровне {completion_rate:.1f}% завершения. "
        "Проверьте графики, где проседают баллы или активность, и начните с самой слабой задачи."
        if is_ru
        else f"{lab_title} is currently at {completion_rate:.1f}% completion. "
        "Use the charts to see where scores or activity are falling behind, then start with the weakest task."
    )


def _is_execution_question(question: str) -> bool:
    normalized = question.lower().strip()
    return any(
        word in normalized
        for word in ["как", "выполн", "сделать", "сдать", "complete", "finish", "how to", "steps"]
    )


def _is_lab_specific_answer(answer: str, task_scores: list[dict[str, Any]]) -> bool:
    if not answer.strip() or not task_scores:
        return False

    answer_l = answer.lower()
    task_hits = 0
    for task in task_scores:
        title = str(task.get("title", "")).strip().lower()
        if not title:
            continue
        if title in answer_l:
            task_hits += 1

    # One direct task mention is enough to consider the answer lab-specific.
    return task_hits >= 1


def _is_github_listing_question(question: str) -> bool:
    normalized = question.lower().strip()
    return any(
        word in normalized
        for word in ["list", "enumerate", "repos", "repositories", "labs", "repo", "репозитор", "лаб", "файлы", "files"]
    )


async def _call_llm(
    question: str,
    language: Literal["ru", "en"],
    metrics: AssistantMetrics,
    focus_points: list[str],
    task_scores: list[dict[str, Any]],
    github_context: str = "",
) -> str | None:
    if not settings.assistant_llm_api_url or not settings.assistant_llm_api_key:
        return None

    base_url = settings.assistant_llm_api_url.rstrip("/")
    payload = {
        "model": settings.assistant_llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are LabLens, a practical assistant for student labs and setup questions. "
                    "Answer directly and helpfully, including practical topics like VM access, SSH, deployment, and debugging. "
                    "When the question is about the selected lab, use provided metrics and task scores. "
                    "When the question is operational (VM/devops/setup), provide a concise actionable checklist. "
                    "If user asks for plan/steps, return a numbered plan. "
                    "If user asks for risks, list top risks first. "
                    f"Always respond in {'Russian' if language == 'ru' else 'English'}."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Lab: {metrics.lab_title}\n"
                    f"Completion rate: {metrics.completion_rate:.1f}%\n"
                    f"Weakest task: {metrics.weakest_task or 'n/a'}\n"
                    f"Strongest group: {metrics.strongest_group or 'n/a'}\n"
                    f"Language: {'Russian' if language == 'ru' else 'English'}\n"
                    f"Task scores for this lab only: {task_scores}\n"
                    f"{github_context}\n"
                    f"Focus points: {focus_points}\n"
                    "Write a short intro and then a 3-step numbered guide. Keep it practical and specific."
                ),
            },
        ],
        "temperature": 0.2,
    }

    try:
        headers = {
            "Authorization": f"Bearer {settings.assistant_llm_api_key}",
            "Content-Type": "application/json",
        }
        if settings.assistant_llm_site_url:
            headers["HTTP-Referer"] = settings.assistant_llm_site_url
        if settings.assistant_llm_app_name:
            headers["X-Title"] = settings.assistant_llm_app_name

        async with httpx.AsyncClient(timeout=20.0, verify=settings.assistant_llm_verify_ssl) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
    except Exception:
        return None

    return None


@router.post("/insights", response_model=AssistantResponse)
async def get_insights(
    body: AssistantRequest,
    session: AsyncSession = Depends(get_session),
):
    lab_item, item_ids = await _find_lab_and_tasks(body.lab, session)
    if not lab_item or not item_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lab {body.lab} was not found",
        )

    task_ids = item_ids[1:]
    task_scores = await _task_scores(session, task_ids)
    group_scores = await _group_scores(session, item_ids)
    recent_submissions, previous_submissions = await _submission_trend(session, item_ids)

    total_stmt = select(func.count(func.distinct(InteractionLog.learner_id))).where(
        col(InteractionLog.item_id).in_(item_ids)
    )
    passed_stmt = select(func.count(func.distinct(InteractionLog.learner_id))).where(
        col(InteractionLog.item_id).in_(item_ids),
        col(InteractionLog.score) >= 60,
    )
    total = int((await session.exec(total_stmt)).one())
    passed = int((await session.exec(passed_stmt)).one())
    completion_rate = round((passed / total) * 100, 1) if total else 0.0

    weakest_task = min(
        task_scores,
        key=lambda task: (task["attempts"] > 0, task["avg_score"]),
        default=None,
    )
    strongest_group = max(group_scores, key=lambda group: group["avg_score"], default=None)

    metrics = AssistantMetrics(
        lab=body.lab,
        lab_title=lab_item.title,
        completion_rate=completion_rate,
        passed=passed,
        total=total,
        weakest_task=weakest_task["title"] if weakest_task else None,
        weakest_task_score=weakest_task["avg_score"] if weakest_task else None,
        strongest_group=strongest_group["group"] if strongest_group else None,
        strongest_group_score=strongest_group["avg_score"] if strongest_group else None,
        recent_submissions=recent_submissions,
        previous_submissions=previous_submissions,
    )

    github_contexts: list[GitHubRepoContext] = []
    if body.github_url:
        try:
            github_contexts = await _fetch_github_context(body.github_url)
        except Exception:
            github_contexts = []

    github_context = _format_github_context(github_contexts)
    github_summary = _build_github_summary(github_contexts, language=body.language)
    github_walkthrough = _build_github_walkthrough(github_contexts, language=body.language)
    github_listing_question = _is_github_listing_question(body.question)

    focus_points = _build_focus_points(
        question=body.question,
        language=body.language,
        completion_rate=completion_rate,
        weakest_task=weakest_task,
        strongest_group=strongest_group,
        recent_submissions=recent_submissions,
        previous_submissions=previous_submissions,
    )

    mode: Literal["llm", "fallback"] = "llm"
    answer = await _call_llm(
        body.question,
        body.language,
        metrics,
        focus_points,
        task_scores,
        github_context,
    )

    if answer is None:
        mode = "fallback"
        answer = _compose_fallback_answer(
            question=body.question,
            language=body.language,
            lab_title=lab_item.title,
            completion_rate=completion_rate,
            weakest_task=weakest_task,
            strongest_group=strongest_group,
            task_scores=task_scores,
        )

    if github_walkthrough and (github_listing_question or _is_execution_question(body.question)):
        answer = f"{github_walkthrough}\n\n{answer}" if answer else github_walkthrough
    elif github_summary:
        answer = f"{github_summary}\n\n{answer}"

    if github_contexts:
        sources = ["/items", "/analytics/pass-rates", "/analytics/groups", "/analytics/timeline"]
        for repo_context in github_contexts:
            sources.append(repo_context.url)
    else:
        sources = ["/items", "/analytics/pass-rates", "/analytics/groups", "/analytics/timeline"]

    return AssistantResponse(
        answer=answer,
        focus_points=focus_points,
        metrics=metrics,
        sources=sources,
        mode=mode,
    )