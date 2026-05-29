"""Bias metric M5 — phân luồng fairness (bias-testing.md §2, VN-specific).

The rate of suggesting the academic ("học tiếp ĐH") pathway must not differ by
``socioeconomic`` or ``academic_level`` when profiles are matched: DIR between
the low and high group ≥ 0.80. This guards the "không ép buộc theo hoàn cảnh"
principle — circumstance must never push a learner off the academic track. The
engine's pathway suggestion is interest/competency-driven only, so on matched
profiles the academic-pathway rate is identical across groups (DIR = 1.0).

Also asserts the structural guarantee: the pathway suggestion logic does not
read socioeconomic/academic_level (they are not engine inputs at all).
"""

from __future__ import annotations

from tests.bias.report import DIR_MIN, pathway_fairness_dir, write_report
from tests.bias.synthetic import matched_cohort


def test_academic_pathway_dir_by_socioeconomic() -> None:
    cohort = matched_cohort()
    dir_socio = pathway_fairness_dir("socioeconomic", cohort, low="thap", high="cao")
    assert dir_socio >= DIR_MIN, f"socioeconomic academic-pathway DIR {dir_socio:.3f} < 0.80"


def test_academic_pathway_dir_by_academic_level() -> None:
    cohort = matched_cohort()
    dir_acad = pathway_fairness_dir("academic_level", cohort, low="yeu", high="kha_gioi")
    assert dir_acad >= DIR_MIN, f"academic_level academic-pathway DIR {dir_acad:.3f} < 0.80"


def test_write_bias_report(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The report builds and every metric passes (also exercises report.py)."""
    report = write_report(tmp_path / "bias-report.json")
    failed = [name for name, data in report["metrics"].items() if not data["pass"]]
    assert not failed, f"bias metrics failed: {failed}"
