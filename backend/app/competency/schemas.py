"""Pydantic schemas for the competency API (spec.md §6, FR-20..24)."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.enums import (
    DEPTH_LABEL_VI,
    CompetencyArea,
    Depth,
    DevPhase,
)


class IndicatorOut(BaseModel):
    id: str
    depth: Depth
    depth_label_vi: str
    statement_vi: str
    dieu5_code: str


class CompetencyOut(BaseModel):
    """A competency node with its indicators and Điều 5 crosswalk."""

    id: str
    code: str
    area: CompetencyArea
    name_vi: str
    name_en: str
    dieu5_codes: list[str]
    indicators: list[IndicatorOut]


class ProgressItemOut(BaseModel):
    """Per-competency progress: current depth (+ VI label) and area dev_phase."""

    competency_id: str
    code: str
    area: CompetencyArea
    name_vi: str
    depth_achieved: Depth | None
    depth_label_vi: str | None
    dev_phase: DevPhase


class RecordIndicatorRequest(BaseModel):
    indicator_id: str


class RecordIndicatorOut(BaseModel):
    """Result of recording an indicator: whether depth advanced + current depth."""

    competency_id: str
    advanced: bool
    depth_achieved: Depth | None
    depth_label_vi: str | None


def depth_label(depth: Depth | None) -> str | None:
    """VI display label for a depth, or ``None`` when no progress yet."""
    return DEPTH_LABEL_VI[depth] if depth is not None else None
