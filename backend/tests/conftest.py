"""Shared pytest fixtures: in-memory SQLite, app, async client, factories."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import date

import pytest
import pytest_asyncio
from app.core.audit import SqlAuditRepo
from app.core.config import Settings
from app.core.database import Base, Database
from app.main import create_app
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def make_settings(**overrides: object) -> Settings:
    base = {
        "environment": "test",
        "secret_key": "test-secret-key-0123456789abcdef0123456789abcdef",
        "field_encryption_key": "test-field-key-0123456789abcdef0123456789abcdef",
        "database_url": "sqlite+aiosqlite:///:memory:",
        "bcrypt_rounds": 4,  # fast hashing in tests
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest_asyncio.fixture
async def db(settings: Settings) -> AsyncGenerator[Database, None]:
    """A Database backed by a single shared in-memory SQLite connection."""
    # StaticPool keeps one connection so the schema persists across sessions.
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    database = Database.__new__(Database)
    database.engine = engine
    database.session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    yield database
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db: Database) -> AsyncGenerator[AsyncSession, None]:
    async with db.session_factory() as s:
        yield s
        await s.commit()


@pytest_asyncio.fixture
async def audit(session: AsyncSession) -> SqlAuditRepo:
    return SqlAuditRepo(session)


@pytest_asyncio.fixture
async def seeded_instruments(db: Database) -> dict[str, str]:
    """Seed one active instrument per type; return {type_value: instrument_id}."""
    from app.assessments.models import AssessmentInstrument, AssessmentItem
    from app.assessments.seed import INSTRUMENT_VERSION, ITEMS_BY_TYPE
    from app.core.enums import InstrumentType
    from app.core.models import new_uuid

    ids: dict[str, str] = {}
    async with db.session_factory() as s:
        for itype in InstrumentType:
            inst = AssessmentInstrument(
                id=new_uuid(), type=itype, version=INSTRUMENT_VERSION, is_active=True
            )
            s.add(inst)
            await s.flush()
            for key in ITEMS_BY_TYPE[itype]:
                s.add(
                    AssessmentItem(
                        id=new_uuid(),
                        instrument_id=inst.id,
                        item_key=key,
                        competency_code="NL1",
                        dieu5_code="b",
                        prompt_vi=ITEMS_BY_TYPE[itype][key],
                    )
                )
            ids[itype.value] = inst.id
        await s.commit()
    return ids


@pytest_asyncio.fixture
async def client(settings: Settings, db: Database) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(settings)
    app.state.db = db
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        # Re-attach our test DB (lifespan creates its own otherwise).
        app.state.db = db
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# -- payload factories ----------------------------------------------------


def register_payload(
    *,
    email: str = "adult@example.com",
    password: str = "Password123",
    dob: str = "2000-01-01",
    user_type: str = "student",
    school_level: str = "upper_secondary",
) -> dict[str, str]:
    return {
        "email": email,
        "password": password,
        "date_of_birth": dob,
        "user_type": user_type,
        "school_level": school_level,
    }


def child_dob(years: int = 12) -> str:
    today = date.today()
    return date(today.year - years, today.month, max(1, today.day - 1)).isoformat()
