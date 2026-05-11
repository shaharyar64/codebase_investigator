"""Database engine, session factory, and initialization."""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config.settings import get_settings
from app.database.base import Base

settings = get_settings()

connect_args = (
    {"check_same_thread": False}
    if settings.async_database_url.startswith("sqlite+aiosqlite")
    else {}
)

engine = create_async_engine(
    settings.async_database_url,
    connect_args=connect_args,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_database() -> None:
    """Create database tables for the configured database."""
    if settings.async_database_url.startswith("sqlite+aiosqlite"):
        db_path = settings.async_database_url.replace("sqlite+aiosqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    import app.models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
