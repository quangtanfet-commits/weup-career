"""Assessment HTTP routes (spec.md §6, FR-10..15).

CP-1 wiring: ``/assessments/{type}/submit`` and ``GET /me/assessments/{id}``
process career data, so they depend on ``require_career_data_consent`` — an
under-16 without active guardian consent gets 403 GUARDIAN_CONSENT_REQUIRED.

GET /assessments only lists instruments (no personal data) → auth only.
DELETE /me/assessments/{id} is a data-subject right (FR-14) the owner may
exercise even after consent is revoked → auth + ownership only (no consent gate).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Response, status

from app.api.deps import (
    CurrentUser,
    assessment_service,
    get_current_user,
    require_career_data_consent,
)
from app.assessments.schemas import (
    InstrumentOut,
    ResultDetailOut,
    ResultMetaOut,
    SubmitRequest,
)
from app.assessments.service import AssessmentService
from app.core.enums import InstrumentType

router = APIRouter(tags=["assessments"])


@router.get("/assessments", response_model=list[InstrumentOut])
async def list_instruments(
    _current: CurrentUser = Depends(get_current_user),
    service: AssessmentService = Depends(assessment_service),
) -> list[InstrumentOut]:
    instruments = await service.list_instruments()
    return [InstrumentOut.model_validate(i) for i in instruments]


@router.post(
    "/assessments/{instrument_type}/submit",
    response_model=ResultMetaOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit(
    payload: SubmitRequest,
    instrument_type: InstrumentType = Path(...),
    current: CurrentUser = Depends(require_career_data_consent),
    service: AssessmentService = Depends(assessment_service),
) -> ResultMetaOut:
    result = await service.submit(
        user_id=current.id,
        age_band=current.age_band,
        instrument_type=instrument_type,
        answers=payload.answers,
    )
    return ResultMetaOut.model_validate(result)


@router.get("/me/assessments/{result_id}", response_model=ResultDetailOut)
async def get_result(
    result_id: str = Path(...),
    current: CurrentUser = Depends(require_career_data_consent),
    service: AssessmentService = Depends(assessment_service),
) -> ResultDetailOut:
    result, payload = await service.read_result(
        user_id=current.id, result_id=result_id
    )
    return ResultDetailOut(
        id=result.id,
        instrument_id=result.instrument_id,
        is_sensitive=result.is_sensitive,
        version=result.version,
        created_at=result.created_at,
        payload=payload,
    )


@router.delete(
    "/me/assessments/{result_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_result(
    result_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: AssessmentService = Depends(assessment_service),
) -> Response:
    await service.delete_result(user_id=current.id, result_id=result_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
