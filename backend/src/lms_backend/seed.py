"""Seed demo content for local development."""

from __future__ import annotations

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.db.interactions import create_interaction
from lms_backend.db.items import create_item
from lms_backend.db.learners import create_learner
from lms_backend.models.interaction import InteractionLog
from lms_backend.models.item import ItemRecord
from lms_backend.models.learner import Learner


async def _get_or_create_item(
    session: AsyncSession,
    *,
    type: str,
    parent_id: int | None,
    title: str,
    description: str,
) -> ItemRecord:
    statement = select(ItemRecord).where(
        ItemRecord.type == type,
        ItemRecord.parent_id == parent_id,
        ItemRecord.title == title,
    )
    existing = (await session.exec(statement)).first()
    if existing is not None:
        return existing
    return await create_item(session, type=type, parent_id=parent_id, title=title, description=description)


async def _get_or_create_learner(
    session: AsyncSession,
    external_id: str,
    student_group: str,
) -> Learner:
    statement = select(Learner).where(Learner.external_id == external_id)
    existing = (await session.exec(statement)).first()
    if existing is not None:
        return existing
    return await create_learner(session, external_id, student_group)


async def seed_demo_data(session: AsyncSession) -> None:
    course = await _get_or_create_item(
        session,
        type="course",
        parent_id=None,
        title="LabLens Demo Course",
        description="A small demo course for the local se-toolkit-hackathon launch.",
    )

    lab_topics = {
        1: "Market Product and Git",
        2: "Fix and Deploy Existing Service",
        3: "REST Backend and Testing",
        4: "Testing, Frontend, and AI Agents",
        5: "Data Pipeline and Analytics Dashboard",
        6: "Build an Agent",
        7: "Telegram Bot",
        8: "The Agent is the Interface",
    }

    tasks_by_lab: dict[int, list[ItemRecord]] = {}
    for lab_number, topic in lab_topics.items():
        lab = await _get_or_create_item(
            session,
            type="lab",
            parent_id=course.id,
            title=f"Lab {lab_number:02d} — {topic}",
            description=f"Progress overview for lab {lab_number:02d}.",
        )

        lab_tasks: list[ItemRecord] = []
        for task_number in range(1, 4):
            task = await _get_or_create_item(
                session,
                type="task",
                parent_id=lab.id,
                title=f"Task {task_number} — Core milestone",
                description=f"Milestone {task_number} for lab {lab_number:02d}.",
            )
            lab_tasks.append(task)
        tasks_by_lab[lab_number] = lab_tasks

    learners = [
        await _get_or_create_learner(session, "alice", "M1-11"),
        await _get_or_create_learner(session, "bob", "M1-11"),
        await _get_or_create_learner(session, "carol", "M1-12"),
        await _get_or_create_learner(session, "dmitry", "M1-12"),
    ]

    for learner_index, learner in enumerate(learners):
        for lab_number, lab_tasks in tasks_by_lab.items():
            for task_index, task in enumerate(lab_tasks):
                # Deterministic score spread per learner/lab/task for stable analytics.
                score = max(
                    40,
                    min(100, 62 + learner_index * 10 + task_index * 4 + (lab_number % 3) * 3),
                )

                item_id = task.id
                statement = select(InteractionLog).where(
                    InteractionLog.learner_id == learner.id,
                    InteractionLog.item_id == item_id,
                    InteractionLog.kind == "attempt",
                )
                existing = (await session.exec(statement)).first()
                if existing is not None:
                    continue
                interaction = await create_interaction(
                    session,
                    learner_id=learner.id,
                    item_id=item_id,
                    kind="attempt",
                )
                interaction.score = score
                interaction.checks_passed = int(score // 10)
                interaction.checks_total = 10
                session.add(interaction)
                await session.commit()
