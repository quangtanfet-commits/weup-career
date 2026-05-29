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

from dataclasses import dataclass

from app.careers.models import CareerProfile, ContentItem
from app.careers.repository import ICareerRepo
from app.core.audit import IAuditRepo
from app.core.enums import (
    ContentStatus,
    Depth,
    DevPhase,
    PathwayType,
    RiasecCode,
    SchoolLevel,
    TrainingLevel,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.models import new_uuid

# Mandatory content tags (FR-90): a content_editor MUST supply all of these or
# the create is rejected (422). They are the two-axis (ADR-013) + targeting tags
# that make a unit of content discoverable and legally traceable.
_REQUIRED_TAGS = ("competency_code", "dieu5_code", "depth", "dev_phase", "school_level")


@dataclass(frozen=True)
class ContentDraft:
    """The editor-supplied fields for a new ContentItem (FR-90).

    All five tags are mandatory; ``title``/``body``/``source_ref`` are content.
    """

    title: str
    body: str
    competency_code: str
    dieu5_code: str
    depth: Depth
    dev_phase: DevPhase
    school_level: SchoolLevel
    source_ref: str = ""


class CareerService:
    def __init__(self, *, careers: ICareerRepo, audit: IAuditRepo | None = None) -> None:
        self._careers = careers
        self._audit = audit

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

    async def get_content_item(self, content_id: str) -> ContentItem:
        """One content item by id, any status, or 404 (FR-90 traceability).

        Unlike the public ``list_content`` (published-only by default), this
        fetches a specific row regardless of status so an editor can still
        retrieve an archived prior version by id.
        """
        item = await self._careers.get_content(content_id)
        if item is None:
            raise NotFoundError("Không tìm thấy nội dung")
        return item

    async def create_content(self, *, editor_id: str, draft: ContentDraft) -> ContentItem:
        """Create a v1 ContentItem with all mandatory tags (FR-90).

        version=1, status=draft. The five mandatory tags are enforced here as
        defence-in-depth (the schema also requires them): a missing/empty tag
        raises ``ValidationError`` (422). The new row anchors its own lineage.
        Audited.
        """
        self._require_tags(draft)
        item = ContentItem(
            id=new_uuid(),
            title=draft.title,
            body=draft.body,
            dieu5_code=draft.dieu5_code,
            competency_code=draft.competency_code,
            depth=draft.depth,
            dev_phase=draft.dev_phase,
            school_level=draft.school_level,
            version=1,
            status=ContentStatus.DRAFT,
            source_ref=draft.source_ref,
        )
        item.lineage_id = item.id
        await self._careers.add_content(item)
        await self._audit_content("content.created", editor_id=editor_id, content_id=item.id)
        return item

    async def publish_new_version(self, *, editor_id: str, content_id: str) -> ContentItem:
        """Publish a new version, archiving the prior published one (FR-90).

        Inserts a NEW row (``version`` = prev+1, ``status`` = published) in the
        same lineage as ``content_id`` and flips the previously-published row in
        that lineage to ``archived``. The old row stays in the DB (traceable) and
        is still fetchable by id. The new version copies the prior row's tags +
        content. Returns the freshly published row. Audited.

        ``content_id`` may reference any version in the lineage. 404 if unknown.
        """
        base = await self._careers.get_content(content_id)
        if base is None:
            raise NotFoundError("Không tìm thấy nội dung")
        lineage = base.lineage_id or base.id

        prior_published = await self._careers.latest_published_version(content_id)
        next_version = max(base.version, prior_published.version if prior_published else 0) + 1

        new_item = ContentItem(
            id=new_uuid(),
            title=base.title,
            body=base.body,
            dieu5_code=base.dieu5_code,
            competency_code=base.competency_code,
            depth=base.depth,
            dev_phase=base.dev_phase,
            school_level=base.school_level,
            version=next_version,
            status=ContentStatus.PUBLISHED,
            source_ref=base.source_ref,
            lineage_id=lineage,
        )
        await self._careers.add_content(new_item)
        # Archive the prior published version (supersession) AFTER the new row
        # exists, so the lineage always has a published row mid-flight.
        if prior_published is not None and prior_published.id != new_item.id:
            prior_published.status = ContentStatus.ARCHIVED
        await self._audit_content(
            "content.version.published", editor_id=editor_id, content_id=new_item.id
        )
        return new_item

    def _require_tags(self, draft: ContentDraft) -> None:
        missing = [tag for tag in _REQUIRED_TAGS if not getattr(draft, tag)]
        if missing:
            raise ValidationError(
                "Thiếu nhãn bắt buộc cho nội dung",
                details={"missing_tags": missing},
            )

    async def _audit_content(self, action: str, *, editor_id: str, content_id: str) -> None:
        if self._audit is not None:
            await self._audit.record(
                action=action,
                actor_id=editor_id,
                target_type="ContentItem",
                target_id=content_id,
            )
