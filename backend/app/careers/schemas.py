"""Pydantic schemas for the careers API (spec.md §6, FR-30..33/40..42/50..51).

v2.1 extension (FR-35, ADR-015): ``CareerDetailOut`` gains ``lmi_status`` to
signal whether structured LMI data is available, stale, or absent for the
career's sector. ``CareerSummaryOut`` gains the same field for the list view
when ``sort_by_demand=true`` is requested.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.careers.models import CareerProfile, ContentItem, Pathway
from app.careers.service import ContentDraft
from app.core.enums import (
    ContentStatus,
    Depth,
    DevPhase,
    PathwayType,
    SchoolLevel,
    TrainingLevel,
)

LmiStatus = Literal["available", "stale", "no_data"]


def _split(codes: str) -> list[str]:
    """Split a comma-joined code string into a clean list."""
    return [c for c in (part.strip() for part in codes.split(",")) if c]


class PathwayOut(BaseModel):
    id: str
    name: str
    type: PathwayType
    description: str

    @classmethod
    def from_model(cls, p: Pathway) -> PathwayOut:
        return cls(id=p.id, name=p.name, type=p.type, description=p.description)


class CareerSummaryOut(BaseModel):
    """List view of a career (Điều 5(a)).

    v2.1 extension (FR-35): ``lmi_status`` signals LMI data availability for
    this career's sector. Defaults to ``"no_data"`` for MVP where the snapshot
    table starts empty. When ``sort_by_demand=true`` is requested, careers with
    ``"available"`` LMI data are sorted to the front.
    """

    id: str
    name: str
    field: str
    riasec_codes: list[str]
    training_level: TrainingLevel
    dieu5_code: str
    version: int
    # FR-35 — LMI status for this career's sector.
    lmi_status: LmiStatus = "no_data"

    @classmethod
    def from_model(
        cls, c: CareerProfile, lmi_status: LmiStatus = "no_data"
    ) -> CareerSummaryOut:
        return cls(
            id=c.id,
            name=c.name,
            field=c.field,
            riasec_codes=_split(c.riasec_codes),
            training_level=c.training_level,
            dieu5_code=c.dieu5_code,
            version=c.version,
            lmi_status=lmi_status,
        )


class CareerDetailOut(CareerSummaryOut):
    """Detail view adds prose fields + linked pathways.

    v2.1 extension (FR-35): ``lmi_status`` signals whether structured Labor
    Market Intelligence data is available, stale, or absent for this career's
    sector.  The UI must display "chưa có dữ liệu TTLĐ" when the value is
    ``"stale"`` or ``"no_data"``.
    """

    required_competencies: list[str]
    training_paths: str
    labor_market_outlook: str
    source_ref: str
    pathways: list[PathwayOut]
    # FR-35 — LMI status for this career's sector.
    lmi_status: LmiStatus = "no_data"

    @classmethod
    def from_model(cls, c: CareerProfile, lmi_status: LmiStatus = "no_data") -> CareerDetailOut:
        return cls(
            id=c.id,
            name=c.name,
            field=c.field,
            riasec_codes=_split(c.riasec_codes),
            training_level=c.training_level,
            dieu5_code=c.dieu5_code,
            version=c.version,
            required_competencies=_split(c.required_competencies),
            training_paths=c.training_paths,
            labor_market_outlook=c.labor_market_outlook,
            source_ref=c.source_ref,
            pathways=[PathwayOut.from_model(p) for p in c.pathways],
            lmi_status=lmi_status,
        )


class ContentItemOut(BaseModel):
    """A versioned public content unit (Điều 5(c)/(d))."""

    id: str
    title: str
    body: str
    dieu5_code: str
    competency_code: str
    depth: Depth | None
    dev_phase: DevPhase | None
    school_level: SchoolLevel | None
    version: int
    status: ContentStatus
    source_ref: str

    @classmethod
    def from_model(cls, c: ContentItem) -> ContentItemOut:
        return cls(
            id=c.id,
            title=c.title,
            body=c.body,
            dieu5_code=c.dieu5_code,
            competency_code=c.competency_code,
            depth=c.depth,
            dev_phase=c.dev_phase,
            school_level=c.school_level,
            version=c.version,
            status=c.status,
            source_ref=c.source_ref,
        )


class CreateContentRequest(BaseModel):
    """Editor payload for ``POST /content`` (FR-90).

    All five tags are mandatory and non-optional here — Pydantic rejects a
    missing field with 422 before the service runs. ``depth``/``dev_phase``/
    ``school_level`` are typed enums so an invalid value is also a 422.
    """

    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="", max_length=20000)
    competency_code: str = Field(min_length=1, max_length=16)
    dieu5_code: str = Field(min_length=1, max_length=8)
    depth: Depth
    dev_phase: DevPhase
    school_level: SchoolLevel
    source_ref: str = Field(default="", max_length=255)

    def to_draft(self) -> ContentDraft:
        return ContentDraft(
            title=self.title,
            body=self.body,
            competency_code=self.competency_code,
            dieu5_code=self.dieu5_code,
            depth=self.depth,
            dev_phase=self.dev_phase,
            school_level=self.school_level,
            source_ref=self.source_ref,
        )
