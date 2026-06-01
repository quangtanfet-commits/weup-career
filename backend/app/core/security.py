"""Password hashing (bcrypt) and JWT issuance/verification (HS256).

- Passwords: bcrypt cost ≥12 (FR-06, ADR-008). bcrypt pre-hashes long inputs
  via SHA-256 so the 72-byte limit never truncates a user password.
- Access tokens: short-lived HS256 JWT (ADR-008). Claims carry ``age_band`` and
  ``account_status`` for the fast Consent-Guard path (auth-design §"JWT Claims").
- Refresh tokens: opaque random strings; only their SHA-256 hash is persisted
  (ADR-008). Raw value never stored.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import Settings
from app.core.exceptions import TokenError

_BCRYPT_PREHASH = hashlib.sha256


def hash_password(password: str, *, rounds: int = 12) -> str:
    """Hash a password with bcrypt at the given cost factor (≥12)."""
    prehashed = _BCRYPT_PREHASH(password.encode("utf-8")).digest()
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(prehashed, salt).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time verify ``password`` against a stored bcrypt hash."""
    prehashed = _BCRYPT_PREHASH(password.encode("utf-8")).digest()
    try:
        return bcrypt.checkpw(prehashed, hashed.encode("ascii"))
    except ValueError:
        # Malformed stored hash — treat as non-matching, never raise to caller.
        return False


def create_access_token(
    *,
    settings: Settings,
    subject: str,
    email: str,
    user_type: str,
    age_band: str,
    account_status: str,
    roles: list[str],
    session_version: int,
    jti: str | None = None,
    now: datetime | None = None,
) -> str:
    """Issue a signed short-lived access token."""
    issued = now or datetime.now(UTC)
    expire = issued + timedelta(minutes=settings.access_token_expire_minutes)
    claims: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "user_type": user_type,
        "age_band": age_band,
        "account_status": account_status,
        "roles": roles,
        # Session epoch (H-02): rejected at validation if below the user's
        # current value (re-login / password change bump it).
        "sv": session_version,
        "iat": int(issued.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti or secrets.token_urlsafe(16),
        "iss": settings.jwt_issuer,
    }
    token: str = jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str, *, settings: Settings) -> dict[str, Any]:
    """Verify signature/expiry/issuer and return claims, else raise TokenError."""
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "iss"]},
        )
    except JWTError as exc:
        raise TokenError() from exc
    return claims


def generate_refresh_token() -> str:
    """Generate a cryptographically random opaque refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash of a refresh token for storage/lookup (hash-only)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
