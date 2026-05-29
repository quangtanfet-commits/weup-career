"""Bias metric M3 — disparate impact ratio (bias-testing.md §2, 4/5ths rule).

On a matched cohort (identical profile distribution across protected groups),
the recommendation rate of every (career x protected-group) must satisfy
``DIR = rate(group) / best(group) >= 0.80``. A matched-cohort DIR below 0.80
would mean the algorithm itself introduces disparity (a proxy feature). With an
attribute-blind engine and matched inputs, every DIR is in fact 1.0.
"""

from __future__ import annotations

from tests.bias.report import DIR_MIN, disparate_impact
from tests.bias.synthetic import PROTECTED, matched_cohort


def test_disparate_impact_ratio_at_least_four_fifths() -> None:
    cohort = matched_cohort()
    failures: list[str] = []
    for attr in PROTECTED:
        di = disparate_impact(attr, cohort)
        for cid, data in di.items():
            if data["min_dir"] < DIR_MIN:
                failures.append(f"{attr}/{cid}: min_dir={data['min_dir']:.3f} dirs={data['dir']}")
    assert not failures, "DIR < 0.80 on matched cohort:\n" + "\n".join(failures)
