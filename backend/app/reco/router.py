"""Recommendations HTTP routes (spec.md §6, FR-60..63, CP-5/CP-6).

- ``POST /recommendations`` — **Bearer + consent-gated**
  (``require_career_data_consent``). Generating a recommendation processes the
  learner's sensitive profile, so an under-16 without active guardian consent
  gets 403 GUARDIAN_CONSENT_REQUIRED (CP-1). Returns the proposed recommendation
  with payload + rationale + ``requires_human_confirmation=true`` (CP-5/CP-6).
- ``POST /recommendations/{id}/confirm`` — Bearer; body carries the human
  ``decision`` (accepted/rejected/deferred). This is the ONLY way a
  recommendation becomes effective (CP-5). A recommendation the caller does not
  own is 404 (CP-4) — no cross-user confirm.

Confirming is a data-subject action on the caller's own recommendation, not new
career-data processing, so it is Bearer + ownership only (mirrors how
DELETE /me/assessments/{id} stays exercisable without re-gating consent).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status

from app.api.deps import (
    CurrentUser,
    get_current_user,
    reco_service,
    require_career_data_consent,
)
from app.reco.schemas import ConfirmRequest, RecommendationOut
from app.reco.service import RecoService

router = APIRouter(tags=["recommendations"])


@router.post(
    "/recommendations",
    response_model=RecommendationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_recommendation(
    current: CurrentUser = Depends(require_career_data_consent),
    service: RecoService = Depends(reco_service),
) -> RecommendationOut:
    reco = await service.generate(user_id=current.id)
    return RecommendationOut.from_model(reco)


@router.post(
    "/recommendations/{reco_id}/confirm",
    response_model=RecommendationOut,
)
async def confirm_recommendation(
    payload: ConfirmRequest,
    reco_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: RecoService = Depends(reco_service),
) -> RecommendationOut:
    reco = await service.confirm(user_id=current.id, reco_id=reco_id, decision=payload.decision)
    return RecommendationOut.from_model(reco)
