"""Hard-purge tests for expired soft-deleted accounts (FR-91/92).

Exercises ``purge_expired_accounts`` directly: a user whose ``deleted_at`` is
older than the recovery window is hard-deleted along with owned data; a user
deleted within the window is retained.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app.account.purge import purge_expired_accounts
from app.assessments.models import AssessmentResult
from app.auth.models import RefreshToken, User
from app.core.audit_models import AuditLog
from app.core.database import Database
from app.core.enums import AccountStatus
from app.core.models import new_uuid, utcnow
from sqlalchemy import func, select

from tests.conftest import make_settings

pytestmark = pytest.mark.asyncio


async def _make_deleted_user(db: Database, *, email: str, deleted_days_ago: float) -> str:
    """Create a soft-deleted user whose deleted_at is ``deleted_days_ago`` in the
    past, plus one owned assessment result + a refresh token. Returns the id."""
    uid = new_uuid()
    deleted_at = utcnow() - timedelta(days=deleted_days_ago)
    async with db.session_factory() as s:
        s.add(
            User(
                id=uid,
                email=email,
                hashed_password="x",
                date_of_birth=datetime(1990, 1, 1).date(),
                age_band="adult",
                user_type="student",
                school_level="none",
                account_status=AccountStatus.DELETED,
                is_deleted=True,
                deleted_at=deleted_at,
            )
        )
        s.add(
            AssessmentResult(
                id=new_uuid(),
                user_id=uid,
                instrument_id=new_uuid(),
                result_payload="v1:ciphertext",
                key_version=1,
                is_sensitive=True,
                version=1,
            )
        )
        s.add(
            RefreshToken(
                id=new_uuid(),
                user_id=uid,
                token_hash=new_uuid().replace("-", ""),
                expires_at=utcnow() + timedelta(days=7),
                created_at=utcnow(),
            )
        )
        await s.commit()
    return uid


async def _count(db: Database, model: type, **filt: object) -> int:
    async with db.session_factory() as s:
        stmt = select(func.count()).select_from(model)
        for k, v in filt.items():
            stmt = stmt.where(getattr(model, k) == v)
        return int((await s.execute(stmt)).scalar_one())


async def test_purge_removes_expired_user_and_owned_data(db: Database) -> None:
    settings = make_settings(account_recovery_window_days=30)
    uid = await _make_deleted_user(db, email="old@example.com", deleted_days_ago=31)

    async with db.session_factory() as s:
        purged = await purge_expired_accounts(s, utcnow(), settings=settings)
        await s.commit()
    assert purged == 1

    assert await _count(db, User, id=uid) == 0
    assert await _count(db, AssessmentResult, user_id=uid) == 0
    assert await _count(db, RefreshToken, user_id=uid) == 0
    # A purge audit row was written.
    assert await _count(db, AuditLog, action="user.account_purged", target_id=uid) == 1


async def test_purge_removes_guardian_links_and_consents(db: Database) -> None:
    """A purged child's guardian link + consent are also hard-deleted."""
    from app.guardians.models import GuardianConsent, GuardianLink

    settings = make_settings(account_recovery_window_days=30)
    child_id = await _make_deleted_user(db, email="gchild@example.com", deleted_days_ago=40)
    guardian_id = new_uuid()
    link_id = new_uuid()
    async with db.session_factory() as s:
        s.add(
            User(
                id=guardian_id,
                email="gparent@example.com",
                hashed_password="x",
                date_of_birth=datetime(1980, 1, 1).date(),
                age_band="adult",
                user_type="student",
                school_level="none",
                account_status=AccountStatus.ACTIVE,
                is_deleted=False,
                deleted_at=None,
            )
        )
        s.add(
            GuardianLink(
                id=link_id,
                child_user_id=child_id,
                guardian_user_id=guardian_id,
                relationship="mother",
            )
        )
        s.add(
            GuardianConsent(
                id=new_uuid(),
                child_user_id=child_id,
                guardian_link_id=link_id,
            )
        )
        await s.commit()

    async with db.session_factory() as s:
        purged = await purge_expired_accounts(s, utcnow(), settings=settings)
        await s.commit()
    assert purged == 1
    assert await _count(db, User, id=child_id) == 0
    assert await _count(db, GuardianLink, id=link_id) == 0
    assert await _count(db, GuardianConsent, child_user_id=child_id) == 0
    # The (non-deleted) guardian user is untouched.
    assert await _count(db, User, id=guardian_id) == 1


async def test_purge_retains_within_window(db: Database) -> None:
    settings = make_settings(account_recovery_window_days=30)
    uid = await _make_deleted_user(db, email="recent@example.com", deleted_days_ago=10)

    async with db.session_factory() as s:
        purged = await purge_expired_accounts(s, utcnow(), settings=settings)
        await s.commit()
    assert purged == 0
    assert await _count(db, User, id=uid) == 1
    assert await _count(db, AssessmentResult, user_id=uid) == 1


async def test_purge_ignores_non_deleted_users(db: Database) -> None:
    settings = make_settings(account_recovery_window_days=30)
    uid = new_uuid()
    async with db.session_factory() as s:
        s.add(
            User(
                id=uid,
                email="active@example.com",
                hashed_password="x",
                date_of_birth=datetime(1990, 1, 1).date(),
                age_band="adult",
                user_type="student",
                school_level="none",
                account_status=AccountStatus.ACTIVE,
                is_deleted=False,
                deleted_at=None,
            )
        )
        await s.commit()
        purged = await purge_expired_accounts(s, utcnow(), settings=settings)
        await s.commit()
    assert purged == 0
    assert await _count(db, User, id=uid) == 1


async def test_purge_boundary_exactly_at_window(db: Database) -> None:
    """A user deleted exactly window-days ago is at/<= cutoff → purged."""
    settings = make_settings(account_recovery_window_days=30)
    uid = await _make_deleted_user(db, email="boundary@example.com", deleted_days_ago=30.001)
    async with db.session_factory() as s:
        purged = await purge_expired_accounts(s, utcnow(), settings=settings)
        await s.commit()
    assert purged == 1
    assert await _count(db, User, id=uid) == 0


async def test_purge_default_settings_path(db: Database) -> None:
    """purge_expired_accounts works with settings omitted (uses get_settings).

    get_settings() reads the process env; in tests we pass settings explicitly
    elsewhere, but this covers the default branch with a within-window user so
    nothing is purged regardless of the ambient window.
    """
    import app.account.purge as purge_mod

    uid = await _make_deleted_user(db, email="defwin@example.com", deleted_days_ago=0)

    def _fake_settings() -> object:
        return make_settings(account_recovery_window_days=30)

    original = purge_mod.get_settings
    purge_mod.get_settings = _fake_settings  # type: ignore[assignment]
    try:
        async with db.session_factory() as s:
            purged = await purge_expired_accounts(s, utcnow())
            await s.commit()
    finally:
        purge_mod.get_settings = original  # type: ignore[assignment]
    assert purged == 0
    assert await _count(db, User, id=uid) == 1
