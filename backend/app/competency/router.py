"""Competency HTTP routes (spec.md §6, FR-20..24).

- ``GET /competencies`` — the fixed 12-competency tree + indicators. Reference
  data, no personal data → auth only (mirrors ``GET /assessments``).
- ``GET /me/progress`` — the caller's per-competency depth + dev_phase. This is
  the learner's own career-progress data, so it goes through the consent gate
  (CP-1/CP-2): an under-16 without active guardian consent gets 403.
- ``POST /me/progress/indicators`` — record attainment of an indicator,
  advancing depth only (CP-8). Also consent-gated (it writes career data).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    competency_service,
    get_current_user,
    require_career_data_consent,
)
from app.competency.schemas import (
    CompetencyOut,
    IndicatorOut,
    ProgressItemOut,
    RecordIndicatorOut,
    RecordIndicatorRequest,
    depth_label,
)
from app.competency.service import CompetencyService

router = APIRouter(tags=["competency"])


def _split_dieu5(codes: str) -> list[str]:
    return [c for c in (part.strip() for part in codes.split(",")) if c]


@router.get("/competencies", response_model=list[CompetencyOut])
async def list_competencies(
    _current: CurrentUser = Depends(get_current_user),
    service: CompetencyService = Depends(competency_service),
) -> list[CompetencyOut]:
    comps, by_comp = await service.list_tree()
    return [
        CompetencyOut(
            id=comp.id,
            code=comp.code,
            area=comp.area,
            name_vi=comp.name_vi,
            name_en=comp.name_en,
            dieu5_codes=_split_dieu5(comp.dieu5_codes),
            indicators=[
                IndicatorOut(
                    id=ind.id,
                    depth=ind.depth,
                    depth_label_vi=depth_label(ind.depth) or "",
                    statement_vi=ind.statement_vi,
                    dieu5_code=ind.dieu5_code,
                )
                for ind in by_comp.get(comp.id, [])
            ],
        )
        for comp in comps
    ]


@router.get("/me/progress", response_model=list[ProgressItemOut])
async def my_progress(
    current: CurrentUser = Depends(require_career_data_consent),
    service: CompetencyService = Depends(competency_service),
) -> list[ProgressItemOut]:
    items = await service.get_progress(user_id=current.id)
    return [
        ProgressItemOut(
            competency_id=item.competency.id,
            code=item.competency.code,
            area=item.competency.area,
            name_vi=item.competency.name_vi,
            depth_achieved=item.depth_achieved,
            depth_label_vi=depth_label(item.depth_achieved),
            dev_phase=item.dev_phase,
        )
        for item in items
    ]


@router.post(
    "/me/progress/indicators",
    response_model=RecordIndicatorOut,
    status_code=status.HTTP_201_CREATED,
)
async def record_indicator(
    payload: RecordIndicatorRequest,
    current: CurrentUser = Depends(require_career_data_consent),
    service: CompetencyService = Depends(competency_service),
) -> RecordIndicatorOut:
    outcome = await service.record_indicator(user_id=current.id, indicator_id=payload.indicator_id)
    return RecordIndicatorOut(
        competency_id=outcome.competency_id,
        advanced=outcome.advanced,
        depth_achieved=outcome.depth_achieved,
        depth_label_vi=depth_label(outcome.depth_achieved),
    )
