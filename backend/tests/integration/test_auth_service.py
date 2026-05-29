"""Service-level tests for AuthService edge paths (CP-7 internals) + repos.

These drive branches that are awkward to reach through HTTP: unknown/[CRED_55BB0BBF]
tokens, a token whose user vanished, naive-datetime normalisation, logout
no-ops, and the audit count helpers (CP-3 monitoring).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.auth.models import RefreshToken, User
from app.auth.repository import SqlRefreshTokenRepo, SqlUserRepo
from app.auth.schemas import LoginRequest, RegisterRequest
from app.auth.service import AuthService, _as_utc
from app.core.audit import SqlAuditRepo
from app.core.config import Settings
from app.core.enums import AccountStatus, AgeBand, UserType
from app.core.exceptions import TokenError
from app.core.models import new_uuid, utcnow
from app.core.security import hash_refresh_token
from sqlalchemy.ext.asyncio import AsyncSession


def _service(session: AsyncSession, settings: Settings) -> AuthService:
    return AuthService(
        settings=settings,
        users=SqlUserRepo(session),
        tokens=SqlRefreshTokenRepo(session),
        audit=SqlAuditRepo(session),
    )


async def _make_user(session: AsyncSession) -> User:
    user = User(
        id=new_uuid(),
        email=f"{new_uuid()}@example.com",
        hashed_password="x",
        date_of_birth=datetime(2000, 1, 1).date(),
        age_band=AgeBand.ADULT,
        user_type=UserType.STUDENT,
        account_status=AccountStatus.ACTIVE,
    )
    session.add(user)
    await session.flush()
    return user


async def test_refresh_unknown_token_raises(
    session: AsyncSession, settings: Settings
) -> None:
    svc = _service(session, settings)
    with pytest.raises(TokenError):
        await svc.refresh("never-issued-token")


async def test_refresh_expired_token_raises(
    session: AsyncSession, settings: Settings
) -> None:
    svc = _service(session, settings)
    user = await _make_user(session)
    raw = "expired-raw-token"
    session.add(
        RefreshToken(
            id=new_uuid(),
            user_id=user.id,
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            created_at=utcnow(),
        )
    )
    await session.flush()
    with pytest.raises(TokenError):
        await svc.refresh(raw)


async def test_refresh_with_missing_user_raises(
    session: AsyncSession, settings: Settings
) -> None:
    svc = _service(session, settings)
    raw = "orphan-token"
    session.add(
        RefreshToken(
            id=new_uuid(),
            user_id="nonexistent-user-id",
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            created_at=utcnow(),
        )
    )
    await session.flush()
    with pytest.raises(TokenError):
        await svc.refresh(raw)


async def test_logout_noop_on_empty_token(
    session: AsyncSession, settings: Settings
) -> None:
    svc = _service(session, settings)
    await svc.logout(None)
    await svc.logout("")  # both are no-ops, no exception


async def test_logout_noop_on_unknown_token(
    session: AsyncSession, settings: Settings
) -> None:
    svc = _service(session, settings)
    await svc.logout("not-a-real-token")


async def test_full_register_login_refresh_cycle(
    session: AsyncSession, settings: Settings
) -> None:
    svc = _service(session, settings)
    user = await svc.register(
        RegisterRequest(
            email="cycle@example.com",
            password="Password123",
            date_of_birth=datetime(2000, 1, 1).date(),
            user_type=UserType.STUDENT,
        )
    )
    assert user.account_status == AccountStatus.ACTIVE
    issued = await svc.login(
        LoginRequest(email="cycle@example.com", password="Password123"),
        user_agent="pytest",
        ip_address="127.0.0.1",
    )
    rotated = await svc.refresh(issued.refresh_token)
    assert rotated.access_token
    # Old token now revoked → reuse triggers family revocation + raises.
    with pytest.raises(TokenError):
        await svc.refresh(issued.refresh_token)


def test_as_utc_normalises_naive() -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)
    assert _as_utc(naive).tzinfo is UTC
    aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert _as_utc(aware) == aware


async def test_audit_count_helpers(session: AsyncSession, settings: Settings) -> None:
    audit = SqlAuditRepo(session)
    assert await audit.count() == 0
    await audit.record(action="x.event", actor_id="u1")
    await audit.record(action="x.read", actor_id="u1", is_sensitive_access=True)
    assert await audit.count() == 2
    assert await audit.count_sensitive() == 1


async def test_revoke_all_for_user(session: AsyncSession, settings: Settings) -> None:
    repo = SqlRefreshTokenRepo(session)
    user = await _make_user(session)
    for i in range(3):
        await repo.add(
            RefreshToken(
                id=new_uuid(),
                user_id=user.id,
                token_hash=hash_refresh_token(f"t{i}"),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                created_at=utcnow(),
            )
        )
    revoked = await repo.revoke_all_for_user(user.id, when=datetime.now(UTC))
    assert revoked == 3
    # Idempotent: nothing left active to revoke.
    assert await repo.revoke_all_for_user(user.id, when=datetime.now(UTC)) == 0
