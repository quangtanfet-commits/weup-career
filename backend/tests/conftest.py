"""Shared pytest fixtures: in-memory SQLite, app, async client, factories."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from datetime import date
from typing import cast
from urllib.parse import parse_qs, urlsplit

import pytest
import pytest_asyncio
from app.api.deps import mailer as mailer_dep
from app.core.audit import SqlAuditRepo
from app.core.config import Settings
from app.core.database import Base, Database
from app.core.mailer import CapturingMailer
from app.main import create_app
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.applications import Starlette

# Hypothesis profiles. The `ci` profile runs deeper fuzz (max_examples=500) for
# the FR-103 property tests; activated by HYPOTHESIS_PROFILE=ci in the CI job env
# (docs/assurance/counselor-competency-fr103.md, Gate 4). Local runs default to
# `dev` (~50 examples) for speed. function_scoped_fixture is suppressed because
# the DB-backed version property builds a fresh engine per example by design.
hypothesis_settings.register_profile("dev", max_examples=50, deadline=None)
hypothesis_settings.register_profile(
    "ci",
    max_examples=500,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
hypothesis_settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


def make_settings(**overrides: object) -> Settings:
    base = {
        "environment": "test",
        "secret_key": "test-secret-key-0123456789abcdef0123456789abcdef",
        "field_encryption_key": "test-field-key-0123456789abcdef0123456789abcdef",
        "database_url": "sqlite+aiosqlite:///:memory:",
        "bcrypt_rounds": 4,  # fast hashing in tests
        "rate_limit_enabled": False,  # opt-in per test; keeps the suite deterministic
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


@pytest.fixture
def mailer() -> CapturingMailer:
    """The test mailer the ``client`` app captures verification links into.

    A single shared instance per test so ``register_and_verify`` can pull the
    token straight back out of the captured link (N-3 §6.1).
    """
    return CapturingMailer()


@pytest_asyncio.fixture
async def client(
    settings: Settings, db: Database, mailer: CapturingMailer
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(settings)
    app.state.db = db
    # N-3: no real SMTP in tests — capture verification mail in-memory so the
    # token can be replayed through /auth/verify-email (see register_and_verify).
    # Also parked on app.state so mailer_of(client) can recover it for the legacy
    # per-suite _register helpers without threading the fixture through every call.
    app.state.captured_mailer = mailer
    app.dependency_overrides[mailer_dep] = lambda: mailer
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


async def register_and_verify(
    client: AsyncClient,
    mailer: CapturingMailer,
    **kw: str,
) -> dict[str, str]:
    """Register (202) → pull the token from the captured mail → verify (204) → login.

    The single shared seam for the ~dozen suites that used to ``POST /register``
    and expect an immediate session. N-3 made register enumeration-safe (always
    202, no session) and gated login on a verified email, so every such suite now
    routes through here (email-verification §6.1). Returns the login TokenResponse
    body (``access_token`` + ``user``), matching the old ``_register`` contract.
    """
    payload = register_payload(**kw)
    email = payload["email"].strip().lower()

    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 202, resp.text

    sent = mailer.last_for(email)
    assert sent is not None, f"no verification email captured for {email}"
    token = parse_qs(urlsplit(sent.verify_url).query)["token"][0]

    verify = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify.status_code == 204, verify.text

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    return login.json()


def mailer_of(client: AsyncClient) -> CapturingMailer:
    """Recover the CapturingMailer the ``client`` app captures into.

    The app and the test share one instance via ``app.state`` (set in the
    ``client`` fixture), so the legacy per-suite ``_register`` helpers can
    delegate to ``register_and_verify`` without threading the ``mailer`` fixture
    through ~60 call sites.
    """
    transport = client._transport
    assert isinstance(transport, ASGITransport)
    app = cast(Starlette, transport.app)
    mailer = app.state.captured_mailer
    assert isinstance(mailer, CapturingMailer)
    return mailer
