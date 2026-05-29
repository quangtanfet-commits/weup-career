"""Relational RBAC — ownership and explicit relationships (CP-4, auth-design §Lớp 3).

A user may only access another user's data through an explicitly granted
relationship: guardian↔child (verified link) or counselor↔student (same school,
out of slice-1 scope). Default is deny. Non-ownership surfaces as 404 at the API
edge to avoid existence disclosure (auth-design §"Defense in depth").
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.guardians.repository import IGuardianRepo


async def is_verified_guardian_of(
    guardian_repo: IGuardianRepo,
    *,
    actor_id: str,
    owner_id: str,
) -> bool:
    """True if ``actor_id`` is a verified guardian linked to ``owner_id``."""
    link = await guardian_repo.get_link_for_child_guardian(
        child_user_id=owner_id, guardian_user_id=actor_id
    )
    return link is not None and link.verified_at is not None


async def can_access(
    *,
    actor_id: str,
    owner_id: str,
    guardian_repo: IGuardianRepo,
    counselor_check: Callable[[str, str], Awaitable[bool]] | None = None,
) -> bool:
    """Relational access decision (CP-4).

    Allowed iff actor IS the owner, OR a verified guardian of the owner, OR
    (future) a counselor of the owner within the same school.
    """
    if actor_id == owner_id:
        return True
    if await is_verified_guardian_of(guardian_repo, actor_id=actor_id, owner_id=owner_id):
        return True
    if counselor_check is not None and await counselor_check(actor_id, owner_id):
        return True
    return False
