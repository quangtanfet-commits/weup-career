"""User & RefreshToken repositories — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): services depend on the Protocol, not on SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, RevokedAccessToken, User
from app.core.models import new_uuid, utcnow


class IUserRepo(Protocol):
    async def add(self, user: User) -> User: ...
    async def get_by_id(self, user_id: str) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def update(self, user: User) -> User: ...


class IRefreshTokenRepo(Protocol):
    async def add(self, token: RefreshToken) -> RefreshToken: ...
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...
    async def revoke(self, token: RefreshToken, *, when: datetime) -> None: ...
    async def revoke_all_for_user(self, user_id: str, *, when: datetime) -> int: ...


class IRevokedTokenRepo(Protocol):
    async def add(self, *, jti: str, user_id: str, expires_at: datetime) -> None: ...
    async def is_revoked(self, jti: str, *, now: datetime) -> bool: ...


class SqlUserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        await self._session.flush()
        return user


class SqlRefreshTokenRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken, *, when: datetime) -> None:
        token.revoked_at = when
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: str, *, when: datetime) -> int:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = list(result.scalars().all())
        for token in tokens:
            token.revoked_at = when
        # Security-critical: persist family revocation immediately so it
        # survives even when the surrounding request fails with 401 (CP-7
        # re-use detection). The unit of work for this call is committed here.
        await self._session.commit()
        return len(tokens)


class SqlRevokedTokenRepo:
    """Access-token ``jti`` denylist (H-01)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, *, jti: str, user_id: str, expires_at: datetime) -> None:
        # Drop inert (already-expired) rows so the table stays bounded by the
        # access-token TTL rather than growing per logout forever.
        await self._session.execute(
            delete(RevokedAccessToken).where(RevokedAccessToken.expires_at <= utcnow())
        )
        # Idempotent: a double logout reuses the same jti, and the column is
        # unique — re-inserting would raise. Skip if already denylisted.
        existing = await self._session.execute(
            select(RevokedAccessToken.id).where(RevokedAccessToken.jti == jti)
        )
        if existing.scalar_one_or_none() is not None:
            return
        self._session.add(
            RevokedAccessToken(
                id=new_uuid(),
                jti=jti,
                user_id=user_id,
                expires_at=expires_at,
                created_at=utcnow(),
            )
        )
        await self._session.flush()

    async def is_revoked(self, jti: str, *, now: datetime) -> bool:
        # Filter on expiry so correctness never depends on pruning having run:
        # an entry past its expires_at is treated as absent.
        result = await self._session.execute(
            select(RevokedAccessToken.id).where(
                RevokedAccessToken.jti == jti,
                RevokedAccessToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none() is not None
