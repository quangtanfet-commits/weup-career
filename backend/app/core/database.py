"""Async database engine, session factory, and declarative base (ADR-002).

All access goes through SQLAlchemy async — no SQLite-specific API in app code,
so migrating to PostgreSQL is a `DATABASE_URL` change only. SQLite connections
get WAL + foreign-keys pragmas applied at connect time.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the async engine, applying SQLite pragmas when applicable."""
    connect_args: dict[str, Any] = {}
    if _is_sqlite(settings.database_url):
        connect_args["check_same_thread"] = False

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )

    if _is_sqlite(settings.database_url):

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn: Any, _record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build a session factory bound to ``engine``."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


class Database:
    """Holds engine + session factory for the process lifetime."""

    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_engine(settings)
        self.session_factory = create_session_factory(self.engine)

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a session, committing on success and rolling back on error."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def ping(self) -> bool:
        """Readiness check — returns True if the DB answers a trivial query."""
        from sqlalchemy import text

        async with self.session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True

    async def dispose(self) -> None:
        await self.engine.dispose()
