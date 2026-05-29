"""Consent Guard (CP-1/CP-2) + relational RBAC (CP-4) unit tests.

Uses in-memory fakes implementing the repository Ports — no DB needed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.authz import can_access, is_verified_guardian_of
from app.core.consent import (
    can_process_career_data,
    is_under_16,
    require_consent,
)
from app.core.enums import AgeBand
from app.core.exceptions import GuardianConsentRequiredError
from app.guardians.models import GuardianLink


class FakeGuardianRepo:
    """In-memory IGuardianRepo for guard/[CRED_A607FFB1] tests."""

    def __init__(self) -> None:
        self._active: set[str] = set()
        self._links: list[GuardianLink] = []

    def set_active(self, child_id: str) -> None:
        self._active.add(child_id)

    def add_link(self, child_id: str, guardian_id: str, *, verified: bool) -> None:
        self._links.append(
            GuardianLink(
                id=f"link-{len(self._links)}",
                child_user_id=child_id,
                guardian_user_id=guardian_id,
                relationship="parent",
                verified_at=datetime.now(UTC) if verified else None,
            )
        )

    async def has_active_consent(self, child_user_id: str) -> bool:
        return child_user_id in self._active

    async def get_link_for_child_guardian(
        self, child_user_id: str, guardian_user_id: str
    ) -> GuardianLink | None:
        for link in self._links:
            if (
                link.child_user_id == child_user_id
                and link.guardian_user_id == guardian_user_id
            ):
                return link
        return None


def test_is_under_16() -> None:
    assert is_under_16(AgeBand.UNDER_16)
    assert is_under_16("under_16")
    assert not is_under_16(AgeBand.ADULT)


@pytest.mark.asyncio
async def test_adult_always_allowed() -> None:
    repo = FakeGuardianRepo()
    assert await can_process_career_data(
        user_id="a1", age_band=AgeBand.ADULT, guardian_repo=repo
    )
    await require_consent(user_id="a1", age_band="adult", guardian_repo=repo)


@pytest.mark.asyncio
async def test_under16_blocked_without_consent_cp1() -> None:
    repo = FakeGuardianRepo()
    assert not await can_process_career_data(
        user_id="c1", age_band=AgeBand.UNDER_16, guardian_repo=repo
    )
    with pytest.raises(GuardianConsentRequiredError):
        await require_consent(user_id="c1", age_band="under_16", guardian_repo=repo)


@pytest.mark.asyncio
async def test_under16_allowed_with_active_consent() -> None:
    repo = FakeGuardianRepo()
    repo.set_active("c1")
    assert await can_process_career_data(
        user_id="c1", age_band=AgeBand.UNDER_16, guardian_repo=repo
    )
    await require_consent(user_id="c1", age_band="under_16", guardian_repo=repo)


@pytest.mark.asyncio
async def test_can_access_self() -> None:
    repo = FakeGuardianRepo()
    assert await can_access(actor_id="u1", owner_id="u1", guardian_repo=repo)


@pytest.mark.asyncio
async def test_can_access_verified_guardian() -> None:
    repo = FakeGuardianRepo()
    repo.add_link("c1", "g1", verified=True)
    assert await is_verified_guardian_of(repo, actor_id="g1", owner_id="c1")
    assert await can_access(actor_id="g1", owner_id="c1", guardian_repo=repo)


@pytest.mark.asyncio
async def test_unverified_guardian_denied() -> None:
    repo = FakeGuardianRepo()
    repo.add_link("c1", "g1", verified=False)
    assert not await is_verified_guardian_of(repo, actor_id="g1", owner_id="c1")
    assert not await can_access(actor_id="g1", owner_id="c1", guardian_repo=repo)


@pytest.mark.asyncio
async def test_stranger_denied_cp4() -> None:
    repo = FakeGuardianRepo()
    assert not await can_access(actor_id="x", owner_id="c1", guardian_repo=repo)


@pytest.mark.asyncio
async def test_counselor_check_hook() -> None:
    repo = FakeGuardianRepo()

    async def counselor_of(actor: str, owner: str) -> bool:
        return actor == "co1" and owner == "s1"

    assert await can_access(
        actor_id="co1", owner_id="s1", guardian_repo=repo, counselor_check=counselor_of
    )
    assert not await can_access(
        actor_id="co1", owner_id="s2", guardian_repo=repo, counselor_check=counselor_of
    )
