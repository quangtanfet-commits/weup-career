"""Pydantic schemas for the careers API (spec.md §6, FR-30..33/40..42/50..51)."""

from __future__ import annotations

from pydantic import BaseModel

from app.careers.models import CareerProfile, ContentItem, Pathway
from app.core.enums import (
    ContentStatus,
    Depth,
    DevPhase,
    PathwayType,
    SchoolLevel,
    TrainingLevel,
)


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
    """List view of a career (Điều 5(a))."""

    id: str
    name: str
    field: str
    riasec_codes: list[str]
    training_level: TrainingLevel
    dieu5_code: str
    version: int

    @classmethod
    def from_model(cls, c: CareerProfile) -> CareerSummaryOut:
        return cls(
            id=c.id,
            name=c.name,
            field=c.field,
            riasec_codes=_split(c.riasec_codes),
            training_level=c.training_level,
            dieu5_code=c.dieu5_code,
            version=c.version,
        )


class CareerDetailOut(CareerSummaryOut):
    """Detail view adds prose fields + linked pathways."""

    required_competencies: list[str]
    training_paths: str
    labor_market_outlook: str
    source_ref: str
    pathways: list[PathwayOut]

    @classmethod
    def from_model(cls, c: CareerProfile) -> CareerDetailOut:
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
