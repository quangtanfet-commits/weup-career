"""Email-verification (N-3) service-level unit tests — spec §6.2.

Drives ``AuthService`` directly against the real SQL repos + in-memory SQLite,
exercising the four token guarantees the integration suite only covers
indirectly: tokens are stored hash-only with a bounded TTL, a link is
single-use, an expired link is rejected, and a resend retires every prior
unconsumed link.
"""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from app.auth.models import EmailVerificationToken
from app.auth.repository import (
    SqlEmailVerificationTokenRepo,
    SqlRefreshTokenRepo,
    SqlRevokedTokenRepo,
    SqlUserRepo,
)
from app.auth.schemas import RegisterRequest
from app.auth.service import AuthService
from app.core.audit import SqlAuditRepo
from app.core.database import Database
from app.core.exceptions import TokenError
from app.core.mailer import CapturingMailer
from app.core.security import hash_refresh_token
from sqlalchemy import select

from tests.conftest import make_settings

pytestmark = pytest.mark.asyncio


def _service(session: object, mailer: CapturingMailer, settings: object) -> AuthService:
    return AuthService(
        settings=settings,  # type: ignore[arg-type]
        users=SqlUserRepo(session),  # type: ignore[arg-type]
        tokens=SqlRefreshTokenRepo(session),  # type: ignore[arg-type]
        revoked=SqlRevokedTokenRepo(session),  # type: ignore[arg-type]
        email_tokens=SqlEmailVerificationTokenRepo(session),  # type: ignore[arg-type]
        mailer=mailer,
        audit=SqlAuditRepo(session),  # type: ignore[arg-type]
    )


def _payload(email: str = "adult@example.com") -> RegisterRequest:
    return RegisterRequest(email=email, password="Password123", date_of_birth=date(1990, 1, 1))


def _raw_token(mailer: CapturingMailer, email: str) -> str:
    """The raw token from the most recent verification mail for ``email`` — the
    only place the un-hashed token is ever exposed (the email link)."""
    sent = [m for m in mailer.sent if m.to == email][-1]
    return parse_qs(urlsplit(sent.verify_url).query)["token"][0]


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def test_issued_token_is_hash_only_with_bounded_ttl(db: Database) -> None:
    """Registration mints exactly one token; the raw value never touches the DB,
    and the row expires ``verification_token_ttl_hours`` after issuance."""
    settings = make_settings()
    mailer = CapturingMailer()
    async with db.session_factory() as s:
        await _service(s, mailer, settings).register(_payload())

        rows = list((await s.execute(select(EmailVerificationToken))).scalars().all())
        assert len(rows) == 1
        row = rows[0]

        raw = _raw_token(mailer, "adult@example.com")
        # Hash-only at rest: the stored value is the SHA-256 of the raw token,
        # never the token itself.
        assert row.token_hash != raw
        assert row.token_hash == hash_refresh_token(raw)
        assert len(row.token_hash) == 64

        ttl = timedelta(hours=settings.verification_token_ttl_hours)
        assert _as_utc(row.expires_at) - _as_utc(row.created_at) == ttl


async def test_token_is_single_use(db: Database) -> None:
    """A successful verify stamps ``consumed_at``; replaying the same link is
    rejected as a generic TokenError (spec §5)."""
    mailer = CapturingMailer()
    async with db.session_factory() as s:
        svc = _service(s, mailer, make_settings())
        await svc.register(_payload())
        raw = _raw_token(mailer, "adult@example.com")

        await svc.verify_email(raw)
        user = await SqlUserRepo(s).get_by_email("adult@example.com")  # type: ignore[union-attr]
        assert user is not None and user.email_verified_at is not None

        with pytest.raises(TokenError):
            await svc.verify_email(raw)


async def test_expired_token_is_rejected(db: Database) -> None:
    """A token whose ``expires_at`` is in the past fails closed."""
    mailer = CapturingMailer()
    async with db.session_factory() as s:
        svc = _service(s, mailer, make_settings())
        await svc.register(_payload())
        user = await SqlUserRepo(s).get_by_email("adult@example.com")
        assert user is not None

        raw = secrets.token_urlsafe(32)
        past = datetime.now(UTC) - timedelta(hours=1)
        await SqlEmailVerificationTokenRepo(s).add(
            user_id=user.id,
            token_hash=hash_refresh_token(raw),
            expires_at=past,
            created_at=past - timedelta(hours=24),
        )

        with pytest.raises(TokenError):
            await svc.verify_email(raw)


async def test_token_for_missing_user_is_rejected(db: Database) -> None:
    """Defence in depth: a live token whose user row is absent (the FK-cascade
    'impossible' case) collapses to a generic TokenError, never a 500."""
    mailer = CapturingMailer()
    async with db.session_factory() as s:
        svc = _service(s, mailer, make_settings())
        raw = secrets.token_urlsafe(32)
        # Insert an orphan token directly (no matching user row).
        await SqlEmailVerificationTokenRepo(s).add(
            user_id="ghost-user-id",
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            created_at=datetime.now(UTC),
        )
        with pytest.raises(TokenError):
            await svc.verify_email(raw)


async def test_resend_invalidates_prior_unconsumed_tokens(db: Database) -> None:
    """Resend retires every still-open link for the account so only the newest
    one works (bounds live single-use tokens per user)."""
    mailer = CapturingMailer()
    async with db.session_factory() as s:
        svc = _service(s, mailer, make_settings())
        await svc.register(_payload())
        raw_old = _raw_token(mailer, "adult@example.com")

        await svc.resend_verification("adult@example.com")
        raw_new = _raw_token(mailer, "adult@example.com")
        assert raw_old != raw_new

        # The superseded link is dead...
        with pytest.raises(TokenError):
            await svc.verify_email(raw_old)
        # ...and the freshly issued one verifies.
        await svc.verify_email(raw_new)
        user = await SqlUserRepo(s).get_by_email("adult@example.com")
        assert user is not None and user.email_verified_at is not None
