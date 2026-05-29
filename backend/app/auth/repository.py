"""User & RefreshToken repositories — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): services depend on the Protocol, not on SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, User


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
