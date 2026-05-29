"""Wellbeing HTTP routes (FR-71).

- ``POST /wellbeing/support-request`` — an authenticated student asks for
  support; the system records a Tier-3 referral routed to a counselor in their
  school (or unrouted if none). NO diagnosis / when-to-seek-help) content (NG-03).
- ``GET /wellbeing/support-requests`` — the student's own referral records.

Consent-gated (``require_career_data_consent``): an under-16 account without an
active guardian consent may not have its personal data processed (NFR-11 / CP-1
spirit), so the safe-pathway request is held behind the same consent guard as
other personal-data routes. A ≥16 user passes through. The wellbeing *content*
(FR-70) is served by the public ``GET /content`` route, not here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    require_career_data_consent,
    wellbeing_service,
)
from app.wellbeing.schemas import SupportRequestCreate, SupportRequestOut
from app.wellbeing.service import WellbeingService

router = APIRouter(tags=["wellbeing"])


@router.post(
    "/wellbeing/support-request",
    response_model=SupportRequestOut,
    status_code=status.HTTP_201_CREATED,
)
async def request_support(
    payload: SupportRequestCreate,
    current: CurrentUser = Depends(require_career_data_consent),
    service: WellbeingService = Depends(wellbeing_service),
) -> SupportRequestOut:
    request = await service.request_support(student_id=current.id, message=payload.message)
    return SupportRequestOut.from_model(request)


@router.get(
    "/wellbeing/support-requests",
    response_model=list[SupportRequestOut],
)
async def list_my_support_requests(
    current: CurrentUser = Depends(require_career_data_consent),
    service: WellbeingService = Depends(wellbeing_service),
) -> list[SupportRequestOut]:
    requests = await service.list_my_requests(student_id=current.id)
    return [SupportRequestOut.from_model(r) for r in requests]
