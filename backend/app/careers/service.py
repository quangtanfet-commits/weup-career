"""CareerService — public career library + 5c/5d content (FR-30..33/40..42/50..51).

Pure business logic, no FastAPI imports (hexagonal, ADR-009).

Everything served here is **public content** (Điều 5(a)): no consent gate and no
per-user ownership scoping — the router enforces Bearer auth only. The service
just forwards filter criteria to the repository and raises ``NotFoundError`` for
an unknown career id (404).

By default ``list_content`` returns only ``published`` items so draft/archived
content is not exposed publicly (FR-90, NFR-26); a caller may pass an explicit
status to override.
"""

from __future__ import annotations

from app.careers.models import CareerProfile, ContentItem
from app.careers.repository import ICareerRepo
from app.core.enums import (
    ContentStatus,
    DevPhase,
    PathwayType,
    RiasecCode,
    SchoolLevel,
    TrainingLevel,
)
from app.core.exceptions import NotFoundError


class CareerService:
    def __init__(self, *, careers: ICareerRepo) -> None:
        self._careers = careers

    async def list_careers(
        self,
        *,
        riasec: RiasecCode | None = None,
        field: str | None = None,
        training_level: TrainingLevel | None = None,
        pathway_type: PathwayType | None = None,
    ) -> list[CareerProfile]:
        """Public career library, optionally filtered (FR-32).

        ``riasec`` links assessment results → related careers; ``field`` and
        ``training_level`` narrow by occupational area / training required;
        ``pathway_type`` surfaces e.g. the GDNN / trường-trung-học-nghề branch.
        """
        return await self._careers.list_careers(
            riasec=riasec,
            field=field,
            training_level=training_level,
            pathway_type=pathway_type,
        )

    async def get_career(self, career_id: str) -> CareerProfile:
        """One career profile, or 404 if it does not exist (FR-30)."""
        career = await self._careers.get_career(career_id)
        if career is None:
            raise NotFoundError("Không tìm thấy thông tin nghề")
        return career

    async def list_content(
        self,
        *,
        dieu5_code: str | None = None,
        competency_code: str | None = None,
        dev_phase: DevPhase | None = None,
        school_level: SchoolLevel | None = None,
        status: ContentStatus | None = ContentStatus.PUBLISHED,
    ) -> list[ContentItem]:
        """Public 5c/5d learning content, filtered (FR-40..42/50..51).

        Defaults to ``published`` only so unpublished drafts stay private.
        """
        return await self._careers.list_content(
            dieu5_code=dieu5_code,
            competency_code=competency_code,
            dev_phase=dev_phase,
            school_level=school_level,
            status=status,
        )
