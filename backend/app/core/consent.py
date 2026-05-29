"""Consent Guard — the single control point for under-16 career-data access.

Implements CP-1 (no career-data processing for under-16 without an active
GuardianConsent) and CP-2 (revocation stops new processing immediately).

Mirrors the TLA+ `CanProcess(u)` predicate (tla/ConsentLifecycle): a user may
process career data iff they are NOT under-16, OR they have an active consent.
Re-validated against the DB on every sensitive route (auth-design §Lớp 2) — the
JWT claim is only a fast hint and may be up to 15 min stale.
"""

from __future__ import annotations

from app.core.enums import AgeBand
from app.core.exceptions import GuardianConsentRequiredError
from app.guardians.repository import IGuardianRepo


def is_under_16(age_band: AgeBand | str) -> bool:
    return str(age_band) == AgeBand.UNDER_16.value


async def can_process_career_data(
    *,
    user_id: str,
    age_band: AgeBand | str,
    guardian_repo: IGuardianRepo,
) -> bool:
    """Return True iff career-data processing is permitted for this user (CP-1)."""
    if not is_under_16(age_band):
        return True
    return await guardian_repo.has_active_consent(user_id)


async def require_consent(
    *,
    user_id: str,
    age_band: AgeBand | str,
    guardian_repo: IGuardianRepo,
) -> None:
    """Raise GuardianConsentRequiredError (403) when consent is missing (CP-1/CP-2)."""
    if not await can_process_career_data(
        user_id=user_id, age_band=age_band, guardian_repo=guardian_repo
    ):
        raise GuardianConsentRequiredError()
