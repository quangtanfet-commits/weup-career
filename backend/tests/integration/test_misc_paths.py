"""Tests for remaining branches: readiness failure, consent dependency, DB,
logging, and the /me missing-user edge."""

from __future__ import annotations

import pytest
from app.api.deps import CurrentUser, require_career_data_consent
from app.core.config import Settings
from app.core.consent import is_under_16
from app.core.database import Database
from app.core.enums import AgeBand, UserType
from app.core.exceptions import GuardianConsentRequiredError
from app.core.logging import configure_logging, correlation_id_var, get_logger
from app.core.models import new_uuid
from app.guardians.repository import SqlGuardianRepo
from app.main import create_app
from httpx import ASGITransport, AsyncClient

from tests.conftest import child_dob, mailer_of, register_and_verify


async def test_ready_returns_503_when_db_down(settings: Settings) -> None:
    """Readiness flips to 503 when the DB ping fails (ADR-009)."""

    class BrokenDB:
        async def ping(self) -> bool:
            raise RuntimeError("db down")

    app = create_app(settings)
    app.state.db = BrokenDB()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/ready")
    assert resp.status_code == 503
    assert resp.json()["database"] == "down"


async def test_consent_dependency_blocks_under16(session, settings) -> None:  # type: ignore[no-untyped-def]
    """require_career_data_consent raises 403 for under-16 without consent."""
    guardians = SqlGuardianRepo(session)
    current = CurrentUser(
        id=new_uuid(),
        email="kid@example.com",
        user_type="student",
        age_band=AgeBand.UNDER_16.value,
        account_status="pending_guardian_consent",
        roles=["student"],
    )
    with pytest.raises(GuardianConsentRequiredError):
        await require_career_data_consent(current=current, guardians=guardians)


async def test_consent_dependency_allows_adult(session, settings) -> None:  # type: ignore[no-untyped-def]
    guardians = SqlGuardianRepo(session)
    current = CurrentUser(
        id=new_uuid(),
        email="a@example.com",
        user_type="student",
        age_band=AgeBand.ADULT.value,
        account_status="active",
        roles=["student"],
    )
    result = await require_career_data_consent(current=current, guardians=guardians)
    assert result is current


async def test_database_ping_and_dispose(settings: Settings) -> None:
    db = Database(settings)
    assert await db.ping() is True
    await db.dispose()


async def test_database_session_rolls_back_on_error(db) -> None:  # type: ignore[no-untyped-def]
    """The session generator rolls back and re-raises on error (ADR-009).

    Drive the generator manually and throw into it — this mirrors how FastAPI
    propagates a handler exception back into a dependency generator.
    """
    gen = db.session()
    await gen.__anext__()  # enter, yields the session
    with pytest.raises(RuntimeError, match="boom"):
        await gen.athrow(RuntimeError("boom"))


async def test_database_session_commits_on_success(db) -> None:  # type: ignore[no-untyped-def]
    """The happy path commits and closes the session cleanly."""
    gen = db.session()
    await gen.__anext__()
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()  # resumes past yield → commit → return


def test_is_sqlite_branch_detection() -> None:
    """The SQLite-only pragma path is gated on the URL scheme (ADR-002)."""
    from app.core.database import _is_sqlite

    assert _is_sqlite("sqlite+aiosqlite:///:memory:") is True
    assert _is_sqlite("postgresql+asyncpg://u:p@localhost/db") is False


def test_logging_redacts_and_binds_correlation(capsys) -> None:  # type: ignore[no-untyped-def]
    configure_logging("info")
    token = correlation_id_var.set("req_test_1")
    try:
        get_logger().info("auth.login", password="supersecret", token="abc", ok=True)
    finally:
        correlation_id_var.reset(token)
    out = capsys.readouterr().out
    assert "supersecret" not in out
    assert "[REDACTED]" in out
    assert "req_test_1" in out


def test_is_under_16_variants() -> None:
    assert is_under_16(AgeBand.UNDER_16)
    assert not is_under_16(UserType.STUDENT.value)  # any non-under_16 string


async def test_me_missing_user_after_delete(client: AsyncClient, db) -> None:  # type: ignore[no-untyped-def]
    """/me returns 404 if the token is valid but the user row is gone."""
    from app.auth.models import User
    from sqlalchemy import delete

    token = (await register_and_verify(client, mailer_of(client)))["access_token"]
    # Delete the user (and its tokens) directly via the shared test DB.
    async with db.session_factory() as s:
        await s.execute(delete(User).where(User.email == "adult@example.com"))
        await s.commit()
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 404


async def test_register_under16_then_invite_unverified_consent_paths(
    client: AsyncClient,
) -> None:
    """Cover guardian-service: child-not-found is unreachable via API, but the
    duplicate/[CRED_C2EBF1F6] branches are exercised elsewhere; here we ensure an
    under-16 invite to a real guardian succeeds end to end."""
    mailer = mailer_of(client)
    ctoken = (
        await register_and_verify(
            client,
            mailer,
            email="c3@example.com",
            dob=child_dob(13),
            school_level="lower_secondary",
        )
    )["access_token"]
    await register_and_verify(client, mailer, email="g3@example.com", dob="1980-01-01")
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "g3@example.com", "relationship": "father"},
        headers={"Authorization": f"Bearer {ctoken}"},
    )
    assert invite.status_code == 201
    assert invite.json()["assurance_level"] == "low"
