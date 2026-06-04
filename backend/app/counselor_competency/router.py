"""Counselor-competency HTTP routes (spec.md §6, FR-100..103, ADR-016).

All routes require a Bearer token AND a counselor ``SchoolMembership``.
Authority is re-derived from ``SchoolMembership`` per request in the service.

Routes:
- ``GET /counselor/competencies``           — the counseling-practice framework.
- ``POST /me/counselor/self-assessments``   — submit own self-assessment.
- ``GET  /me/counselor/self-assessments``   — own assessment history.

CP-1 note: these routes NEVER invoke ``require_career_data_consent`` (the
guardian-consent gate for under-16 student career data, CP-1). A counselor's
self-assessment is their own professional data; it is a different legal
category (FR-103).

CP-4 note: the new endpoints do not widen counselor authority over students.
The only data accessible is the calling counselor's own self-assessment.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, counselor_competency_service, get_current_user
from app.counselor_competency.schemas import (
    CounselorCompetencyOut,
    CreateSelfAssessmentRequest,
    SelfAssessmentOut,
)
from app.counselor_competency.service import CounselorCompetencyService

router = APIRouter(tags=["counselor-competency"])


@router.get(
    "/counselor/competencies",
    response_model=list[CounselorCompetencyOut],
    summary="List counseling-practice competency framework (FR-100)",
)
async def list_counselor_competencies(
    current: CurrentUser = Depends(get_current_user),
    service: CounselorCompetencyService = Depends(counselor_competency_service),
) -> list[CounselorCompetencyOut]:
    """Return all framework entries ordered by code.

    Requires a counselor ``SchoolMembership``; any other authenticated user
    gets 403.
    """
    competencies = await service.list_competencies(actor_id=current.id)
    return [CounselorCompetencyOut.from_model(c) for c in competencies]


@router.post(
    "/me/counselor/self-assessments",
    response_model=SelfAssessmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit counselor self-assessment (FR-101/102)",
)
async def create_self_assessment(
    payload: CreateSelfAssessmentRequest,
    current: CurrentUser = Depends(get_current_user),
    service: CounselorCompetencyService = Depends(counselor_competency_service),
) -> SelfAssessmentOut:
    """Record a new versioned self-assessment for the calling counselor.

    Returns the created record including the development-path suggestion
    and explanation (FR-102). Does NOT go through CP-5/CP-6.
    """
    result = await service.create_self_assessment(
        counselor_id=current.id,
        scores=payload.scores,
    )
    return SelfAssessmentOut.from_result(result)


@router.get(
    "/me/counselor/self-assessments",
    response_model=list[SelfAssessmentOut],
    summary="List own self-assessment history (FR-101)",
)
async def list_self_assessments(
    current: CurrentUser = Depends(get_current_user),
    service: CounselorCompetencyService = Depends(counselor_competency_service),
) -> list[SelfAssessmentOut]:
    """Return the calling counselor's own assessment history, latest first."""
    results = await service.list_self_assessments(counselor_id=current.id)
    return [SelfAssessmentOut.from_result(r) for r in results]
