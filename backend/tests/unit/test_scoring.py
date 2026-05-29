"""Unit tests for the pure scoring functions (FR-10, scoring.py)."""

from __future__ import annotations

import pytest
from app.assessments.scoring import (
    ScoringError,
    score,
    score_mbti,
    score_riasec,
    score_vips,
)
from app.core.enums import InstrumentType


def test_riasec_totals_and_code() -> None:
    answers = {"R_1": 5, "R_2": 5, "I_1": 4, "A_1": 1, "S_1": 3, "E_1": 2, "C_1": 1}
    result = score_riasec(answers)
    assert result["type"] == "riasec"
    assert result["scores"]["R"] == 10
    assert result["scores"]["I"] == 4
    # Top-3 by score: R(10), I(4), S(3) → "RIS".
    assert result["code"] == "RIS"


def test_riasec_ignores_unknown_and_out_of_range() -> None:
    answers = {"R_1": 5, "Z_9": 5, "R_2": 99, "bad": 3, "I_1": 0}
    result = score_riasec(answers)
    assert result["scores"]["R"] == 5  # R_2=99 out of range ignored
    assert result["scores"]["I"] == 0  # I_1=0 out of range ignored
    assert "Z" not in result["scores"]


def test_riasec_rejects_bool_answers() -> None:
    # bool is an int subclass; must not be counted as a Likert value.
    result = score_riasec({"R_1": True, "R_2": 4})
    assert result["scores"]["R"] == 4


def test_riasec_ignores_non_int_answer_values() -> None:
    # Non-int values (str/float/None) are ignored, never raise.
    result = score_riasec({"R_1": "5", "R_2": 4, "I_1": None, "A_1": 2.5})
    assert result["scores"]["R"] == 4  # only R_2=4 counts
    assert result["scores"]["I"] == 0
    assert result["scores"]["A"] == 0


def test_vips_dominant() -> None:
    result = score_vips({"V_1": 5, "I_1": 1, "P_1": 2, "S_1": 1})
    assert result["type"] == "vips"
    assert result["dominant"] == "V"


def test_mbti_four_letter_code() -> None:
    answers = {
        "E_1": 5,
        "I_1": 1,  # E
        "S_1": 1,
        "N_1": 5,  # N
        "T_1": 5,
        "F_1": 1,  # T
        "J_1": 1,
        "P_1": 5,  # P
    }
    result = score_mbti(answers)
    assert result["type"] == "mbti"
    assert result["code"] == "ENTP"


def test_mbti_tie_favours_first_pole_deterministic() -> None:
    # Equal scores on every axis → first pole of each axis (E,S,T,J).
    answers = {"E_1": 3, "I_1": 3, "S_1": 3, "N_1": 3, "T_1": 3, "F_1": 3, "J_1": 3, "P_1": 3}
    assert score_mbti(answers)["code"] == "ESTJ"


def test_dispatch_matches_direct_scorers() -> None:
    answers = {"R_1": 4, "I_1": 2}
    assert score(InstrumentType.RIASEC, answers) == score_riasec(answers)


def test_empty_answers_do_not_raise() -> None:
    assert score_riasec({})["scores"]["R"] == 0
    assert score_mbti({})["code"] == "ESTJ"
    assert score_vips({})["dominant"] == "I"


def test_score_unknown_type_raises() -> None:
    with pytest.raises(ScoringError):
        score("nope", {})  # type: ignore[arg-type]
