"""Database operations for items."""

import logging
from typing import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.models.item import ItemRecord

logger = logging.getLogger(__name__)


async def read_items(session: AsyncSession) -> list[ItemRecord]:
    """Read all items from the database."""
    try:
        logger.info(
            "db_query",
            extra={"event": "db_query", "table": "item", "operation": "select"},
        )
        result = await session.exec(select(ItemRecord))
        return list(result.all())
    except Exception as exc:
        logger.error(
            "db_query",
            extra={
                "event": "db_query",
                "table": "item",
                "operation": "select",
                "error": str(exc),
            },
        )
        raise


async def read_labs(
    session: AsyncSession, *, include_hidden: bool = False
) -> list[ItemRecord]:
    """Read lab items from the database."""
    result = await session.exec(select(ItemRecord).where(ItemRecord.type == "lab"))
    labs = list(result.all())
    if include_hidden:
        return labs
    return [lab for lab in labs if not bool(lab.attributes.get("hidden", False))]


async def read_item(session: AsyncSession, item_id: int) -> ItemRecord | None:
    """Read a single item by id."""
    return await session.get(ItemRecord, item_id)


async def create_item(
    session: AsyncSession,
    type: str,
    parent_id: int | None,
    title: str,
    description: str,
) -> ItemRecord:
    """Create a new item in the database."""
    item = ItemRecord(
        type=type, parent_id=parent_id, title=title, description=description
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def create_lab_with_tasks(
    session: AsyncSession,
    *,
    title: str,
    description: str,
    tasks: Sequence[str],
) -> tuple[ItemRecord, list[ItemRecord]]:
    """Create a lab and child tasks in a single transaction."""
    lab = ItemRecord(type="lab", parent_id=None, title=title, description=description)
    session.add(lab)
    await session.flush()

    created_tasks: list[ItemRecord] = []
    for index, task_title in enumerate(tasks, start=1):
        task = ItemRecord(
            type="task",
            parent_id=lab.id,
            title=f"Task {index} — {task_title}",
            description=f"Work package {index} for {title}.",
        )
        session.add(task)
        created_tasks.append(task)

    await session.commit()
    await session.refresh(lab)
    for task in created_tasks:
        await session.refresh(task)
    return lab, created_tasks


async def set_lab_hidden(
    session: AsyncSession, *, lab_id: int, hidden: bool = True
) -> ItemRecord | None:
    """Set or unset the hidden flag for a lab item."""
    lab = await session.get(ItemRecord, lab_id)
    if lab is None or lab.type != "lab":
        return None

    attrs = dict(lab.attributes)
    attrs["hidden"] = hidden
    lab.attributes = attrs

    session.add(lab)
    await session.commit()
    await session.refresh(lab)
    return lab


async def update_item(
    session: AsyncSession, item_id: int, title: str, description: str
) -> ItemRecord | None:
    """Update an existing item in the database."""
    item = await session.get(ItemRecord, item_id)
    if item is None:
        return None
    item.title = title
    item.description = description
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
