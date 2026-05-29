"""Bias metric M4 — demographic parity difference (bias-testing.md §2).

On matched profiles, the absolute difference in a career's recommendation rate
between any two protected groups must be ``|Δ| ≤ 0.10``. An attribute-blind
engine on matched inputs yields Δ = 0 for every career and attribute.
"""

from __future__ import annotations

from tests.bias.report import PARITY_MAX_DELTA, demographic_parity
from tests.bias.synthetic import PROTECTED, matched_cohort


def test_demographic_parity_difference_within_threshold() -> None:
    cohort = matched_cohort()
    failures: list[str] = []
    for attr in PROTECTED:
        dp = demographic_parity(attr, cohort)
        for cid, data in dp.items():
            if data["max_delta"] > PARITY_MAX_DELTA:
                failures.append(f"{attr}/{cid}: max_delta={data['max_delta']:.3f}")
    assert not failures, "|Δ rate| > 0.10 on matched cohort:\n" + "\n".join(failures)
