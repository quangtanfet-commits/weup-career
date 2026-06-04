"""Pydantic schemas for the counselor-competency API (spec.md §6, FR-100..103).

Kept minimal and purposeful. Scores are exposed as a dict[str, int] at the API
layer; the service/model layer handles encoding/decoding to the semicolon string.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.counselor_competency.models import CounselorCompetency
from app.counselor_competency.service import SelfAssessmentResult


class CounselorCompetencyOut(BaseModel):
    """One competency in the counseling-practice framework (FR-100)."""

    id: str
    code: str
    name_vi: str
    name_en: str
    description: str
    source_ref: str

    @classmethod
    def from_model(cls, m: CounselorCompetency) -> "CounselorCompetencyOut":
        return cls(
            id=m.id,
            code=m.code,
            name_vi=m.name_vi,
            name_en=m.name_en,
            description=m.description,
            source_ref=m.source_ref,
        )


class CreateSelfAssessmentRequest(BaseModel):
    """Submit a self-assessment: per-competency scores (1–5 each)."""

    scores: dict[str, int] = Field(
        min_length=1,
        description="Mapping of competency code → self-rating (1–5).",
    )


class SelfAssessmentOut(BaseModel):
    """One counselor self-assessment snapshot (FR-101/102)."""

    id: str
    counselor_id: str
    version: int
    scores: dict[str, int]
    suggested_development_path: str
    created_at: datetime

    @classmethod
    def from_result(cls, r: SelfAssessmentResult) -> "SelfAssessmentOut":
        return cls(
            id=r.id,
            counselor_id=r.counselor_id,
            version=r.version,
            scores=r.scores,
            suggested_development_path=r.suggested_development_path,
            created_at=r.created_at,
        )
