"""Bias metric M1 — scoring invariance (bias-testing.md §2, NFR-12).

M1 is a HARD 100% gate: the RIASEC/VIPS/MBTI scoring functions must be
completely independent of protected attributes (gender / [CRED_FA1D26C6] / [CRED_C9C9D52B] /
academic level / [CRED_BDB22C0C]. Enforced two ways:

  1. Structural — the scorer signatures accept exactly one parameter
     (``answers``) and nothing else; no protected attribute can even be passed.
  2. Behavioural — for the same answers, injecting any protected-attribute
     key/value into the input mapping never changes the score (Hypothesis).

A single failing case = fail (no threshold to relax).
"""

from __future__ import annotations

import inspect

from app.assessments.scoring import score_mbti, score_riasec, score_vips
from hypothesis import given
from hypothesis import strategies as st

_SCORERS = [score_riasec, score_vips, score_mbti]

# Protected attributes that MUST never influence scoring (bias-testing.md §1).
_PROTECTED = {
    "gender": ["nam", "nu", "khac"],
    "region": ["thanh_thi", "nong_thon"],
    "socioeconomic": ["thap", "trung_binh", "cao"],
    "academic_level": ["yeu", "trung_binh", "kha_gioi"],
    "ethnicity": ["kinh", "dan_toc_thieu_so"],
}


def test_scorer_signatures_take_only_answers() -> None:
    """No scorer accepts a protected attribute as a parameter (M1 structural)."""
    for scorer in _SCORERS:
        params = list(inspect.signature(scorer).parameters)
        assert params == ["answers"], f"{scorer.__name__} signature: {params}"
        for attr in _PROTECTED:
            assert attr not in params


# Likert answers keyed by realistic item keys across all instruments.
_item_keys = st.sampled_from(
    ["R_1", "I_1", "A_1", "S_1", "E_1", "C_1", "V_1", "P_1", "N_1", "T_1", "J_1"]
)
_answers = st.dictionaries(_item_keys, st.integers(min_value=1, max_value=5), max_size=11)
_protected_pairs = st.dictionaries(
    st.sampled_from(list(_PROTECTED)),
    st.sampled_from([v for vals in _PROTECTED.values() for v in vals]),
    max_size=5,
)


@given(answers=_answers, injected=_protected_pairs)
def test_injecting_protected_attrs_does_not_change_score(
    answers: dict[str, int], injected: dict[str, str]
) -> None:
    """Adding protected-attribute keys to the input never alters any score."""
    polluted: dict[str, object] = {**answers, **injected}
    for scorer in _SCORERS:
        assert scorer(answers) == scorer(polluted)


@given(answers=_answers)
def test_score_stable_across_all_protected_value_flips(answers: dict[str, int]) -> None:
    """Flipping each protected attribute through all its values yields one score."""
    for scorer in _SCORERS:
        baseline = scorer(answers)
        for attr, values in _PROTECTED.items():
            for value in values:
                polluted: dict[str, object] = {**answers, attr: value}
                assert scorer(polluted) == baseline
