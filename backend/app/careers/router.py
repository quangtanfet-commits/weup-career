"""Careers HTTP routes (spec.md §6, FR-30..33/40..42/50..51).

**Public content — anonymous-readable, NOT consent-gated.** The career library
and the 5c/5d learning content are public information under TT 16/2026 Điều
5(a). The frontend serves them as public SEO pages, so the GET routes here are
readable WITHOUT a login (BE-1; ADR-001 §Consequences — Điều-5a là công khai).
They depend on ``optional_current_user`` (Bearer optional) — never
``require_career_data_consent``. This is the deliberate distinction from
assessments/progress, which are sensitive personal data and *do* pass the
consent gate. An under-16 account still in ``pending_guardian_consent`` may also
read them (the consent gate never applies to Điều-5a).

**Published-only invariant.** Every caller — anonymous or authenticated — only
ever sees ``published`` content. An anonymous caller may NOT override the
``status`` filter to surface ``draft``/``archived`` items: when the request is
unauthenticated, ``status`` is forced to ``published``. Editor write/inspection
routes (POST /content, POST /content/{id}/versions, GET /content/{id}) stay
``require_content_editor`` (Bearer + DB-derived editor authority).

- ``GET /careers``      — public library; filter by RIASEC group, field,
  training level, pathway type (incl. the GDNN / trường-trung-học-nghề branch).
- ``GET /careers/{id}`` — one career; 404 if unknown.
- ``GET /content``      — public 5c/5d content; filter by dieu5/competency/
  dev_phase/school_level (published-only by default; forced for anon).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentUser,
    career_service,
    get_session,
    optional_current_user,
    require_content_editor,
)
from app.careers.schemas import (
    CareerDetailOut,
    CareerSummaryOut,
    ContentItemOut,
    CreateContentRequest,
    LmiStatus,
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
from app.labor_market.repository import SqlLaborMarketRepo
from app.labor_market.service import LaborMarketService

router = APIRouter(tags=["careers"])


def _lmi_service(session: AsyncSession = Depends(get_session)) -> LaborMarketService:
    """Build a LaborMarketService for the FR-35 LMI-status enrichment."""
    return LaborMarketService(repo=SqlLaborMarketRepo(session))


@router.get("/careers", response_model=list[CareerSummaryOut])
async def list_careers(
    riasec: RiasecCode | None = Query(None, description="Lọc theo nhóm RIASEC (FR-32)"),
    field: str | None = Query(None, description="Lọc theo lĩnh vực nghề"),
    training_level: TrainingLevel | None = Query(None, description="Lọc theo trình độ đào tạo"),
    pathway_type: PathwayType | None = Query(
        None, description="Lọc theo nhánh phân luồng (gồm GDNN/trường trung học nghề)"
    ),
    sort_by_demand: bool = Query(
        False,
        description=(
            "FR-35: khi true, sắp xếp nghề có dữ liệu TTLĐ mới lên đầu. "
            "Nghề không có snapshot (hoặc quá hạn) xuống cuối."
        ),
    ),
    _current: CurrentUser | None = Depends(optional_current_user),
    service: CareerService = Depends(career_service),
    lmi: LaborMarketService = Depends(_lmi_service),
) -> list[CareerSummaryOut]:
    """Career library, optionally filtered and sorted by labor demand (FR-32, FR-35).

    When ``sort_by_demand=true``, each career gains an ``lmi_status`` field and
    careers with "available" LMI data appear first. Careers without data or with
    stale snapshots follow, clearly signalling "chưa có dữ liệu TTLĐ" (FR-35).
    """
    careers = await service.list_careers(
        riasec=riasec,
        field=field,
        training_level=training_level,
        pathway_type=pathway_type,
    )
    # Resolve LMI status for each career's sector (FR-35).
    # Only resolve if the caller asked for demand-sort (avoids N+1 for the common path).
    summaries: list[CareerSummaryOut]
    if sort_by_demand:
        items: list[tuple[LmiStatus, CareerSummaryOut]] = []
        for c in careers:
            lmi_status: LmiStatus = await lmi.lmi_status_for_sector(c.field)
            items.append((lmi_status, CareerSummaryOut.from_model(c, lmi_status=lmi_status)))
        # Sort: "available" first, then "stale", then "no_data".
        _order = {"available": 0, "stale": 1, "no_data": 2}
        items.sort(key=lambda x: _order[x[0]])
        summaries = [s for _, s in items]
    else:
        summaries = [CareerSummaryOut.from_model(c) for c in careers]
    return summaries


@router.get("/careers/{career_id}", response_model=CareerDetailOut)
async def get_career(
    career_id: str = Path(...),
    _current: CurrentUser | None = Depends(optional_current_user),
    service: CareerService = Depends(career_service),
    lmi: LaborMarketService = Depends(_lmi_service),
) -> CareerDetailOut:
    """Career detail; includes ``lmi_status`` for the career's sector (FR-35).

    ``lmi_status`` is always present:
    - ``"available"`` — fresh structured LMI snapshot exists for this sector.
    - ``"stale"`` — snapshot exists but is beyond the 365-day threshold.
    - ``"no_data"`` — no snapshot at all (expected MVP state for most careers).

    The UI must display "chưa có dữ liệu TTLĐ" for ``stale`` or ``no_data``.
    """
    career = await service.get_career(career_id)
    lmi_status: LmiStatus = await lmi.lmi_status_for_sector(career.field)
    return CareerDetailOut.from_model(career, lmi_status=lmi_status)


@router.get("/content", response_model=list[ContentItemOut])
async def list_content(
    dieu5_code: str | None = Query(None, description="Lọc theo mã Điều 5 (a/b/c/d/đ)"),
    competency_code: str | None = Query(None, description="Lọc theo mã năng lực (NL1..NL12)"),
    dev_phase: DevPhase | None = Query(None, description="Lọc theo giai đoạn phát triển"),
    school_level: SchoolLevel | None = Query(None, description="Lọc theo cấp học"),
    status: ContentStatus | None = Query(
        ContentStatus.PUBLISHED, description="Trạng thái xuất bản (mặc định: published)"
    ),
    current: CurrentUser | None = Depends(optional_current_user),
    service: CareerService = Depends(career_service),
) -> list[ContentItemOut]:
    # Published-only invariant: an anonymous caller can never override ``status``
    # to surface draft/archived content. Force published when unauthenticated.
    effective_status = status if current is not None else ContentStatus.PUBLISHED
    items = await service.list_content(
        dieu5_code=dieu5_code,
        competency_code=competency_code,
        dev_phase=dev_phase,
        school_level=school_level,
        status=effective_status,
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
