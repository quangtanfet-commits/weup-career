"""Bias-report emitter (bias-testing.md §5) — shared metric helpers + JSON/table.

Computes the per-metric verdicts (M1..M5) against the deterministic engine over
the synthetic cohorts, writes ``bias-report.json`` (machine-readable, attached
to each release per Gate C) and a human-readable table. The test modules import
the metric helpers here so the report and the gating tests use one code path.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tests.bias.synthetic import (
    PROTECTED,
    Subject,
    counterfactual_pairs,
    matched_cohort,
    recommend_for,
    synthetic_careers,
    top_groups,
)

# Fairness thresholds (bias-testing.md §2). Do NOT loosen to pass.
DIR_MIN = 0.80  # M3/M5 — 4/5ths rule
PARITY_MAX_DELTA = 0.10  # M4
COUNTERFACTUAL_MIN = 0.99  # M2

# Direction we treat as "học tiếp ĐH" for the M5 pathway-fairness check.
ACADEMIC_PATHWAY_TYPE = "academic"


def _rate(values: Iterable[bool]) -> float:
    items = list(values)
    return sum(1 for v in items if v) / len(items) if items else 0.0


def _group_subjects_by(attr: str, subjects: list[Subject]) -> dict[str, list[Subject]]:
    grouped: dict[str, list[Subject]] = defaultdict(list)
    for s in subjects:
        grouped[s.attrs[attr]].append(s)
    return grouped


def career_recommended_rates(attr: str, subjects: list[Subject]) -> dict[str, dict[str, float]]:
    """``{career_id: {group_value: rate-in-top5}}`` for one protected attribute."""
    grouped = _group_subjects_by(attr, subjects)
    career_ids = [c.id for c in synthetic_careers()]
    rates: dict[str, dict[str, float]] = {}
    for cid in career_ids:
        rates[cid] = {}
        for group, members in grouped.items():
            tops = [top_groups(recommend_for(s)) for s in members]
            rates[cid][group] = _rate(cid in t for t in tops)
    return rates


def disparate_impact(attr: str, subjects: list[Subject]) -> dict[str, dict[str, Any]]:
    """M3 — DIR per (career x group) = rate(group) / rate(best group)."""
    rates = career_recommended_rates(attr, subjects)
    out: dict[str, dict[str, Any]] = {}
    for cid, by_group in rates.items():
        best = max(by_group.values()) if by_group else 0.0
        dirs = {group: (rate / best if best > 0 else 1.0) for group, rate in by_group.items()}
        out[cid] = {"rates": by_group, "dir": dirs, "min_dir": min(dirs.values()) if dirs else 1.0}
    return out


def demographic_parity(attr: str, subjects: list[Subject]) -> dict[str, dict[str, Any]]:
    """M4 — max |Δ rate| across groups, per career."""
    rates = career_recommended_rates(attr, subjects)
    out: dict[str, dict[str, Any]] = {}
    for cid, by_group in rates.items():
        vals = list(by_group.values())
        delta = (max(vals) - min(vals)) if vals else 0.0
        out[cid] = {"rates": by_group, "max_delta": delta}
    return out


def academic_pathway_rate(subjects: list[Subject]) -> float:
    """Fraction of subjects whose suggested pathway is the academic ('học tiếp') one."""
    flags: list[bool] = []
    for s in subjects:
        result = recommend_for(s)
        is_academic = result.pathway is not None and result.pathway.type.value == (
            ACADEMIC_PATHWAY_TYPE
        )
        flags.append(is_academic)
    return _rate(flags)


def pathway_fairness_dir(attr: str, subjects: list[Subject], low: str, high: str) -> float:
    """M5 — DIR of academic-pathway suggestion between two groups (low vs high)."""
    grouped = _group_subjects_by(attr, subjects)
    rate_low = academic_pathway_rate(grouped.get(low, []))
    rate_high = academic_pathway_rate(grouped.get(high, []))
    best = max(rate_low, rate_high)
    if best == 0:
        return 1.0
    return min(rate_low, rate_high) / best


def counterfactual_ratio() -> tuple[float, list[str]]:
    """M2 — fraction of single-flip pairs whose top-5 is identical + skew list."""
    sets = counterfactual_pairs()
    total = 0
    identical = 0
    skewed: list[str] = []
    for cset in sets:
        results = [recommend_for(s) for s in cset.subjects]
        baseline = top_groups(results[0])
        for subject, result in zip(cset.subjects[1:], results[1:], strict=True):
            total += 1
            if top_groups(result) == baseline:
                identical += 1
            else:
                skewed.append(f"{cset.attribute}={subject.attrs[cset.attribute]}")
    return (identical / total if total else 1.0), skewed


def build_report() -> dict[str, Any]:
    """Run every metric and assemble the report structure (per-metric pass/fail)."""
    cohort = matched_cohort()

    cf_ratio, skewed = counterfactual_ratio()

    m3: dict[str, Any] = {}
    m4: dict[str, Any] = {}
    for attr in PROTECTED:
        di = disparate_impact(attr, cohort)
        dp = demographic_parity(attr, cohort)
        m3[attr] = {
            "min_dir": min(v["min_dir"] for v in di.values()),
            "per_career": di,
        }
        m4[attr] = {
            "max_delta": max(v["max_delta"] for v in dp.values()),
            "per_career": dp,
        }

    m5_dir = pathway_fairness_dir("socioeconomic", cohort, low="thap", high="cao")
    m5_dir_academic = pathway_fairness_dir("academic_level", cohort, low="yeu", high="kha_gioi")

    m3_pass = all(v["min_dir"] >= DIR_MIN for v in m3.values())
    m4_pass = all(v["max_delta"] <= PARITY_MAX_DELTA for v in m4.values())
    m5_pass = m5_dir >= DIR_MIN and m5_dir_academic >= DIR_MIN

    return {
        "thresholds": {
            "DIR_MIN": DIR_MIN,
            "PARITY_MAX_DELTA": PARITY_MAX_DELTA,
            "COUNTERFACTUAL_MIN": COUNTERFACTUAL_MIN,
        },
        "metrics": {
            "M1": {"pass": True, "note": "engine/scoring take no protected attr (structural)"},
            "M2": {
                "pass": cf_ratio >= COUNTERFACTUAL_MIN,
                "counterfactual_identical_ratio": cf_ratio,
                "skewed_pairs": skewed,
            },
            "M3": {"pass": m3_pass, "by_attribute": {a: m3[a]["min_dir"] for a in m3}},
            "M4": {"pass": m4_pass, "by_attribute": {a: m4[a]["max_delta"] for a in m4}},
            "M5": {
                "pass": m5_pass,
                "socioeconomic_academic_pathway_dir": m5_dir,
                "academic_level_academic_pathway_dir": m5_dir_academic,
            },
        },
    }


def _human_table(report: dict[str, Any]) -> str:
    lines = ["Bias report (M1-M5) — WeUp Career Recommendation Engine", "=" * 56]
    for name, data in report["metrics"].items():
        verdict = "PASS" if data["pass"] else "FAIL"
        lines.append(f"{name}: {verdict}")
    return "\n".join(lines)


def write_report(path: str | Path = "bias-report.json") -> dict[str, Any]:
    """Build the report, write JSON next to a printed table; return the report."""
    report = build_report()
    Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(_human_table(report))
    return report


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    write_report()
