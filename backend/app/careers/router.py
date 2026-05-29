"""Careers HTTP routes (spec.md §6, FR-30..33/40..42/50..51).

**Public content — NOT consent-gated.** The career library and the 5c/5d
learning content are public information under TT 16/2026 Điều 5(a). An under-16
account still in ``pending_guardian_consent`` may read them (ADR-001 note,
guardian-verification.md). So every route here depends on ``get_current_user``
(Bearer auth) **only** — never ``require_career_data_consent``. This is the
deliberate distinction from assessments/progress, which are sensitive personal
data and *do* pass the consent gate.

- ``GET /careers``      — public library; filter by RIASEC group, field,
  training level, pathway type (incl. the GDNN / trường-trung-học-nghề branch).
- ``GET /careers/{id}`` — one career; 404 if unknown.
- ``GET /content``      — public 5c/5d content; filter by dieu5/competency/
  dev_phase/school_level (published-only by default).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import (
    CurrentUser,
    career_service,
    get_current_user,
    require_content_editor,
)
from app.careers.schemas import (
    CareerDetailOut,
    CareerSummaryOut,
    ContentItemOut,
    CreateContentRequest,
)
from app.careers.service import CareerService
from app.core.enums import (
    ContentStatus,
    DevPhase,
    PathwayType,
    RiasecCode,
    SchoolLevel,
    TrainingLevel,
)

router = APIRouter(tags=["careers"])


@router.get("/careers", response_model=list[CareerSummaryOut])
async def list_careers(
    riasec: RiasecCode | None = Query(None, description="Lọc theo nhóm RIASEC (FR-32)"),
    field: str | None = Query(None, description="Lọc theo lĩnh vực nghề"),
    training_level: TrainingLevel | None = Query(None, description="Lọc theo trình độ đào tạo"),
    pathway_type: PathwayType | None = Query(
        None, description="Lọc theo nhánh phân luồng (gồm GDNN/trường trung học nghề)"
    ),
    _current: CurrentUser = Depends(get_current_user),
    service: CareerService = Depends(career_service),
) -> list[CareerSummaryOut]:
    careers = await service.list_careers(
        riasec=riasec,
        field=field,
        training_level=training_level,
        pathway_type=pathway_type,
    )
    return [CareerSummaryOut.from_model(c) for c in careers]


@router.get("/careers/{career_id}", response_model=CareerDetailOut)
async def get_career(
    career_id: str = Path(...),
    _current: CurrentUser = Depends(get_current_user),
    service: CareerService = Depends(career_service),
) -> CareerDetailOut:
    career = await service.get_career(career_id)
    return CareerDetailOut.from_model(career)


@router.get("/content", response_model=list[ContentItemOut])
async def list_content(
    dieu5_code: str | None = Query(None, description="Lọc theo mã Điều 5 (a/b/c/d/đ)"),
    competency_code: str | None = Query(None, description="Lọc theo mã năng lực (NL1..NL12)"),
    dev_phase: DevPhase | None = Query(None, description="Lọc theo giai đoạn phát triển"),
    school_level: SchoolLevel | None = Query(None, description="Lọc theo cấp học"),
    status: ContentStatus | None = Query(
        ContentStatus.PUBLISHED, description="Trạng thái xuất bản (mặc định: published)"
    ),
    _current: CurrentUser = Depends(get_current_user),
    service: CareerService = Depends(career_service),
) -> list[ContentItemOut]:
    items = await service.list_content(
        dieu5_code=dieu5_code,
        competency_code=competency_code,
        dev_phase=dev_phase,
        school_level=school_level,
        status=status,
    )
    return [ContentItemOut.from_model(c) for c in items]


# -- content_editor management (FR-90) ------------------------------------
# Global/internal content_editor only (re-derived from User.is_content_editor);
# a non-editor → 403. Public GET /content above stays Bearer-only.


@router.post(
    "/content",
    response_model=ContentItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_content(
    payload: CreateContentRequest,
    current: CurrentUser = Depends(require_content_editor),
    service: CareerService = Depends(career_service),
) -> ContentItemOut:
    item = await service.create_content(editor_id=current.id, draft=payload.to_draft())
    return ContentItemOut.from_model(item)


@router.get("/content/{content_id}", response_model=ContentItemOut)
async def get_content_item(
    content_id: str = Path(...),
    current: CurrentUser = Depends(require_content_editor),
    service: CareerService = Depends(career_service),
) -> ContentItemOut:
    """Fetch a specific content row by id, any status (editor traceability)."""
    item = await service.get_content_item(content_id)
    return ContentItemOut.from_model(item)


@router.post(
    "/content/{content_id}/versions",
    response_model=ContentItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def publish_content_version(
    content_id: str = Path(...),
    current: CurrentUser = Depends(require_content_editor),
    service: CareerService = Depends(career_service),
) -> ContentItemOut:
    """Publish a new version; the prior published version is archived (FR-90)."""
    item = await service.publish_new_version(editor_id=current.id, content_id=content_id)
    return ContentItemOut.from_model(item)
