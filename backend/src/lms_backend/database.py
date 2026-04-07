"""Database connection management."""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from lms_backend.settings import settings


def get_database_url() -> str:
    if settings.database_url:
        return settings.database_url

    root_dir = Path(__file__).resolve().parents[3]
    fallback_path = root_dir / "lablens.db"
    return f"sqlite+aiosqlite:///{fallback_path}"


def _engine_options() -> dict[str, object]:
    if get_database_url().startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


database_url = get_database_url()

engine = create_async_engine(database_url, **_engine_options())

async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
