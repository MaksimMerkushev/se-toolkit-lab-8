"""Router for item endpoints — reference implementation."""

import json
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.database import get_session
from lms_backend.db.items import (
    create_item,
    create_lab_with_tasks,
    read_item,
    read_items,
    read_labs,
    set_lab_hidden,
    update_item,
)
from lms_backend.models.item import ItemCreate, ItemRecord, ItemUpdate
from lms_backend.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class LabCreateRequest(ItemCreate):
    title: str
    description: str = ""
    task_count: int = 5
    generate_with_ai: bool = False
    split_prompt: str = ""


class LabSplitRequest(ItemCreate):
    title: str
    description: str = ""
    task_count: int = 5
    split_prompt: str = ""


class LabSummary(ItemCreate):
    id: int
    hidden: bool


class LabCreateResponse(ItemCreate):
    lab: ItemRecord
    tasks: list[ItemRecord]


def _fallback_split_tasks(title: str, task_count: int) -> list[str]:
    base = [
        "Clarify requirements and constraints",
        "Design architecture and data model",
        "Implement core backend endpoints",
        "Build client flow and validations",
        "Test, polish, and prepare deployment notes",
    ]
    if task_count <= len(base):
        return base[:task_count]
    extra = [f"Extend feature set part {i}" for i in range(1, task_count - len(base) + 1)]
    return base + extra


async def _split_tasks_with_ai(
    *,
    title: str,
    description: str,
    split_prompt: str,
    task_count: int,
) -> list[str] | None:
    if not settings.assistant_llm_api_key:
        return None

    prompt = split_prompt.strip() or f"Split lab '{title}' into practical tasks."
    payload = {
        "model": settings.assistant_llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a curriculum planner. Return ONLY a JSON array of task titles. "
                    f"Array length must be exactly {task_count}. Keep each item short and actionable."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Lab title: {title}\n"
                    f"Lab description: {description}\n"
                    f"Request: {prompt}\n"
                    f"Need exactly {task_count} tasks."
                ),
            },
        ],
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {settings.assistant_llm_api_key}",
        "Content-Type": "application/json",
    }
    if settings.assistant_llm_site_url:
        headers["HTTP-Referer"] = settings.assistant_llm_site_url
    if settings.assistant_llm_app_name:
        headers["X-Title"] = settings.assistant_llm_app_name

    try:
        async with httpx.AsyncClient(
            timeout=25.0, verify=settings.assistant_llm_verify_ssl
        ) as client:
            response = await client.post(
                f"{settings.assistant_llm_api_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            parsed = json.loads(content)
            if not isinstance(parsed, list):
                return None

            tasks = [str(item).strip() for item in parsed if str(item).strip()]
            if len(tasks) != task_count:
                return None
            return tasks
    except Exception:
        return None


@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    return await read_items(session)


@router.get("/labs", response_model=list[LabSummary])
async def get_labs(
    include_hidden: bool = Query(False),
    session: AsyncSession = Depends(get_session),
):
    """Get labs, optionally including hidden ones."""
    labs = await read_labs(session, include_hidden=include_hidden)
    return [
        LabSummary(
            id=lab.id or 0,
            type=lab.type,
            parent_id=lab.parent_id,
            title=lab.title,
            description=lab.description,
            hidden=bool(lab.attributes.get("hidden", False)),
        )
        for lab in labs
    ]


@router.post("/labs", response_model=LabCreateResponse, status_code=201)
async def create_lab(
    body: LabCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a lab and auto-generate tasks (AI or fallback)."""
    task_count = max(1, min(body.task_count, 12))

    task_titles: list[str] | None = None
    if body.generate_with_ai:
        task_titles = await _split_tasks_with_ai(
            title=body.title,
            description=body.description,
            split_prompt=body.split_prompt,
            task_count=task_count,
        )

    if not task_titles:
        task_titles = _fallback_split_tasks(body.title, task_count)

    lab, tasks = await create_lab_with_tasks(
        session,
        title=body.title,
        description=body.description,
        tasks=task_titles,
    )
    return LabCreateResponse(type=lab.type, parent_id=lab.parent_id, title=lab.title, description=lab.description, lab=lab, tasks=tasks)


@router.post("/labs/split", response_model=list[str])
async def split_lab(
    body: LabSplitRequest,
    session: AsyncSession = Depends(get_session),
):
    """Return task suggestions for a lab title without creating DB records."""
    task_count = max(1, min(body.task_count, 12))
    task_titles = await _split_tasks_with_ai(
        title=body.title,
        description=body.description,
        split_prompt=body.split_prompt,
        task_count=task_count,
    )
    return task_titles or _fallback_split_tasks(body.title, task_count)


@router.post("/labs/{lab_id}/hide", response_model=LabSummary)
async def hide_lab(
    lab_id: int,
    hidden: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    """Hide (or unhide) a lab without hard deletion."""
    lab = await set_lab_hidden(session, lab_id=lab_id, hidden=hidden)
    if lab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")

    return LabSummary(
        id=lab.id or 0,
        type=lab.type,
        parent_id=lab.parent_id,
        title=lab.title,
        description=lab.description,
        hidden=bool(lab.attributes.get("hidden", False)),
    )


@router.get("/{item_id}", response_model=ItemRecord)
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific item by its id."""
    item = await read_item(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item


@router.post("/", response_model=ItemRecord, status_code=201)
async def post_item(body: ItemCreate, session: AsyncSession = Depends(get_session)):
    """Create a new item."""
    try:
        return await create_item(
            session,
            type=body.type,
            parent_id=body.parent_id,
            title=body.title,
            description=body.description,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="parent_id does not reference an existing item",
        )


@router.put("/{item_id}", response_model=ItemRecord)
async def put_item(
    item_id: int, body: ItemUpdate, session: AsyncSession = Depends(get_session)
):
    """Update an existing item."""
    item = await update_item(
        session, item_id=item_id, title=body.title, description=body.description
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item
