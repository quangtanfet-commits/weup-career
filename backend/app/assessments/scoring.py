"""Pure scoring functions for RIASEC / VIPS / MBTI (FR-10, FR-13, NFR-12 / M1).

Bias rule M1 (bias-testing.md §2): the scoring functions take **only the
respondent's answers** as input. They MUST NOT accept or use any protected
attribute (gender / region / socioeconomic / academic level / ethnicity).
This is enforced structurally — the function signatures accept a single
``answers`` mapping and nothing else — and proven by the property test
``tests/bias/test_M1_scoring_invariance.py``.

These are deterministic, side-effect-free, framework-free functions (hexagonal:
the service layer calls them; they import nothing from FastAPI or the DB). The
produced payload is what the service encrypts at rest (ADR-011).

Answer model (kept deliberately simple for the MVP item bank):
    answers: Mapping[item_key -> Likert int in 1..5]
where ``item_key`` is prefixed by the dimension it loads onto, e.g.
``"R_1"`` loads onto RIASEC dimension ``R``. Unknown / malformed keys are
ignored so a partial or noisy submission can never raise.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from app.core.enums import InstrumentType

# Canonical dimension sets per instrument.
RIASEC_DIMENSIONS: Final[tuple[str, ...]] = ("R", "I", "A", "S", "E", "C")
VIPS_DIMENSIONS: Final[tuple[str, ...]] = ("V", "I", "P", "S")
# MBTI: four opposed axes; we score each pole then pick the dominant letter.
MBTI_AXES: Final[tuple[tuple[str, str], ...]] = (
    ("E", "I"),
    ("S", "N"),
    ("T", "F"),
    ("J", "P"),
)

_LIKERT_MIN: Final[int] = 1
_LIKERT_MAX: Final[int] = 5


class ScoringError(ValueError):
    """Raised when an instrument type has no scoring implementation."""


def _coerce_likert(value: object) -> int | None:
    """Return an int in [1,5] or ``None`` for anything unusable (never raises)."""
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly.
        return None
    if not isinstance(value, int):
        return None
    if value < _LIKERT_MIN or value > _LIKERT_MAX:
        return None
    return value


def _dimension_totals(
    answers: Mapping[str, object], dimensions: tuple[str, ...]
) -> dict[str, int]:
    """Sum Likert answers onto their leading-letter dimension.

    An item key ``"<DIM>_<n>"`` contributes to dimension ``<DIM>``. Keys that
    do not map onto a known dimension are ignored (robust to noisy input).
    """
    totals = {dim: 0 for dim in dimensions}
    for key, raw in answers.items():
        if not isinstance(key, str) or "_" not in key:
            continue
        dim = key.split("_", 1)[0].upper()
        if dim not in totals:
            continue
        score = _coerce_likert(raw)
        if score is None:
            continue
        totals[dim] += score
    return totals


def score_riasec(answers: Mapping[str, object]) -> dict[str, Any]:
    """Score a RIASEC (Holland) submission into per-dimension totals + code."""
    totals = _dimension_totals(answers, RIASEC_DIMENSIONS)
    # Holland code: top-3 dimensions by score (stable order on ties).
    ranked = sorted(RIASEC_DIMENSIONS, key=lambda d: (-totals[d], d))
    return {
        "type": InstrumentType.RIASEC.value,
        "scores": totals,
        "code": "".join(ranked[:3]),
    }


def score_vips(answers: Mapping[str, object]) -> dict[str, Any]:
    """Score a VIPS (Values-Interests-Personality-Skills) submission."""
    totals = _dimension_totals(answers, VIPS_DIMENSIONS)
    ranked = sorted(VIPS_DIMENSIONS, key=lambda d: (-totals[d], d))
    return {
        "type": InstrumentType.VIPS.value,
        "scores": totals,
        "dominant": ranked[0] if ranked else None,
    }


def score_mbti(answers: Mapping[str, object]) -> dict[str, Any]:
    """Score an MBTI submission into a 4-letter type + per-pole totals."""
    poles = tuple(pole for axis in MBTI_AXES for pole in axis)
    totals = _dimension_totals(answers, poles)
    letters: list[str] = []
    for left, right in MBTI_AXES:
        # Tie favours the first pole deterministically (no randomness — M1).
        letters.append(left if totals[left] >= totals[right] else right)
    return {
        "type": InstrumentType.MBTI.value,
        "scores": totals,
        "code": "".join(letters),
    }


_SCORERS = {
    InstrumentType.RIASEC: score_riasec,
    InstrumentType.VIPS: score_vips,
    InstrumentType.MBTI: score_mbti,
}


def score(instrument_type: InstrumentType, answers: Mapping[str, object]) -> dict[str, Any]:
    """Dispatch to the scorer for ``instrument_type`` (answers-only input)."""
    scorer = _SCORERS.get(instrument_type)
    if scorer is None:  # pragma: no cover - guarded by enum at call sites
        raise ScoringError(f"no scorer for instrument type: {instrument_type}")
    return scorer(answers)
