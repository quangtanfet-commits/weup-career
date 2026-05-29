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
async def seeded_competencies(db: Database) -> dict[str, str]:
    """Seed the 12-competency tree + indicators; return {code: competency_id}."""
    from app.competency.seed import seed_competencies as _seed

    async with db.session_factory() as s:
        ids = await _seed(s)
        await s.commit()
    return ids


@pytest_asyncio.fixture
async def seeded_careers(db: Database) -> dict[str, int]:
    """Seed pathways + careers (+ links) + content; return the seed counts."""
    from app.careers.seed import seed_careers as _seed

    async with db.session_factory() as s:
        counts = await _seed(s)
        await s.commit()
    return counts


@pytest_asyncio.fixture
async def seeded_wellbeing(db: Database) -> dict[str, int]:
    """Seed NL4 / [TOKEN_2dc34b67890fa1e5] wellbeing content; return the seed counts."""
    from app.wellbeing.seed import seed_wellbeing as _seed

    async with db.session_factory() as s:
        counts = await _seed(s)
        await s.commit()
    return counts


@pytest_asyncio.fixture
async def seeded_school(db: Database) -> dict[str, str]:
    """Seed the demo school + class; return {"school": id, "class": id}."""
    from app.school.seed import seed_schools as _seed

    async with db.session_factory() as s:
        ids = await _seed(s)
        await s.commit()
    return ids


async def enroll_membership(
    db: Database,
    *,
    user_id: str,
    school_id: str,
    role: str,
    class_id: str | None = None,
) -> str:
    """Create a SchoolMembership directly (school_admin enroll flow stand-in).

    Returns the membership id. Used by school-channel tests to set up the
    relational scoping that ``counselor_check`` (CP-4) decides on.
    """
    from app.core.enums import SchoolRole
    from app.core.models import new_uuid
    from app.school.models import SchoolMembership

    mid = new_uuid()
    async with db.session_factory() as s:
        s.add(
            SchoolMembership(
                id=mid,
                user_id=user_id,
                school_id=school_id,
                role=SchoolRole(role),
                class_id=class_id,
            )
        )
        await s.commit()
    return mid


async def grant_content_editor(db: Database, *, user_id: str) -> None:
    """Flip ``User.is_content_editor`` on (operator/seed grant stand-in).

    Used by content-editor tests; the user must re-login afterwards so the new
    JWT carries the ``content_editor`` role (the route still re-derives from the
    DB flag, so this also covers the stale-claim path).
    """
    from app.auth.models import User

    async with db.session_factory() as s:
        user = await s.get(User, user_id)
        assert user is not None
        user.is_content_editor = True
        await s.commit()


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
