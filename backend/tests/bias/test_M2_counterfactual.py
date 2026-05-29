"""Bias metric M2 — counterfactual fairness (bias-testing.md §2, strongest test).

For the same profile, flipping exactly one protected attribute must not change
the top-5 recommended career groups (≥99% of pairs identical), and the rationale
must never reference a protected attribute. Because the engine takes only the
profile (M1), this holds by construction — but we verify it end-to-end against
the deterministic engine so a future regression (e.g. someone adding a proxy
feature) would fail here.
"""

from __future__ import annotations

import re

from tests.bias.synthetic import (
    PROTECTED,
    counterfactual_pairs,
    recommend_for,
    top_groups,
)

# Concepts a rationale must never reference (protected attrs + their values).
_FORBIDDEN_TERMS: list[str] = [
    *PROTECTED.keys(),
    *[v for vals in PROTECTED.values() for v in vals],
    # Vietnamese surface words that would signal protected reasoning.
    "giới tính",
    "nam",
    "nữ",
    "nông thôn",
    "thành thị",
    "giàu",
    "nghèo",
    "hoàn cảnh",
    "học lực",
    "dân tộc",
]


def _references_protected(text: str) -> list[str]:
    """Return any forbidden term that appears in ``text`` (word-ish match)."""
    lowered = text.lower()
    hits: list[str] = []
    for term in _FORBIDDEN_TERMS:
        # Whole-token-ish match to avoid accidental substrings (e.g. "nam" in a
        # career name). Vietnamese has spaces between syllables, so boundaries work.
        if re.search(rf"(?<![\w]){re.escape(term.lower())}(?![\w])", lowered):
            hits.append(term)
    return hits


def test_counterfactual_top5_invariant() -> None:
    """Flipping one protected attr keeps the top-5 identical for ≥99% of pairs."""
    sets = counterfactual_pairs()
    total_pairs = 0
    identical_pairs = 0
    skewed: list[str] = []

    for cset in sets:
        results = [recommend_for(s) for s in cset.subjects]
        baseline = top_groups(results[0])
        for subject, result in zip(cset.subjects[1:], results[1:], strict=True):
            total_pairs += 1
            if top_groups(result) == baseline:
                identical_pairs += 1
            else:
                skewed.append(f"{cset.attribute}={subject.attrs[cset.attribute]}")

    assert total_pairs > 0
    ratio = identical_pairs / total_pairs
    assert (
        ratio >= 0.99
    ), f"counterfactual top-5 identical ratio {ratio:.4f} < 0.99; skewed={skewed}"
    # With an attribute-blind engine the ratio must in fact be a perfect 1.0.
    assert ratio == 1.0, f"unexpected counterfactual drift: {skewed}"


def test_rationale_never_references_protected_attr() -> None:
    """No career/pathway/overall rationale references a protected attribute (M2)."""
    sets = counterfactual_pairs()
    for cset in sets:
        for subject in cset.subjects:
            result = recommend_for(subject)
            assert not _references_protected(result.rationale), result.rationale
            for career in result.careers:
                hits = _references_protected(career.rationale)
                assert not hits, f"{career.rationale!r} references {hits}"
            if result.pathway is not None:
                hits = _references_protected(result.pathway.rationale)
                assert not hits, f"{result.pathway.rationale!r} references {hits}"
