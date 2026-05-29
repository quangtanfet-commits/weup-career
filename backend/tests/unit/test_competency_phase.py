"""Unit tests for dev_phase inference (FR-23, ADR-013)."""

from __future__ import annotations

from app.competency.service import infer_student_phase
from app.core.enums import Depth, DevPhase, SchoolLevel, depth_rank


def test_depth_rank_ordering() -> None:
    # Sanity on the load-bearing ordering used by CP-8.
    assert depth_rank(Depth.K) < depth_rank(Depth.A) < depth_rank(Depth.R)


def test_lower_secondary_infers_exploration() -> None:
    assert infer_student_phase(SchoolLevel.LOWER_SECONDARY) == DevPhase.EXPLORATION


def test_upper_secondary_infers_planning() -> None:
    assert infer_student_phase(SchoolLevel.UPPER_SECONDARY) == DevPhase.PLANNING


def test_primary_infers_awareness() -> None:
    assert infer_student_phase(SchoolLevel.PRIMARY) == DevPhase.AWARENESS


def test_tertiary_falls_back_to_awareness() -> None:
    assert infer_student_phase(SchoolLevel.TERTIARY) == DevPhase.AWARENESS


def test_none_level_falls_back_to_awareness() -> None:
    assert infer_student_phase(SchoolLevel.NONE) == DevPhase.AWARENESS


def test_accepts_raw_string() -> None:
    assert infer_student_phase("lower_secondary") == DevPhase.EXPLORATION


def test_unknown_string_falls_back_to_awareness() -> None:
    assert infer_student_phase("kindergarten") == DevPhase.AWARENESS
