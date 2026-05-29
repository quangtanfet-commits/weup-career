"""Seeded synthetic-data generator for the bias suite (bias-testing.md §3).

NO real user data is ever used (BVDLCN): every profile here is fabricated from a
fixed seed so runs are reproducible. The module produces three things the
metrics need:

- :func:`base_profiles` — diverse ``RecoProfile`` snapshots (varied RIASEC /
  VIPS / [CRED_44A453BA] + competency depth). These are the engine inputs; they carry NO
  protected attribute (the engine has none — M1).
- :func:`counterfactual_pairs` — for each base profile, a set of *cohort
  members* that share the identical profile but differ in exactly one protected
  attribute (M2). Because the engine input is the profile only, the protected
  attribute rides *alongside* the profile in a :class:`Subject`, never inside it.
- :func:`matched_cohort` — subjects whose **profiles are matched** (drawn from
  the same profile pool) across protected groups, so any output skew (M3/M4/M5)
  could only come from the algorithm, not from differing inputs.

The synthetic career/pathway reference data mirrors the shape of the seeded
library (RIASEC tags + required competencies + pathway types) but is defined
here so the bias tests do not depend on the DB.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import product

from app.core.enums import Depth, PathwayType
from app.reco.engine import (
    CareerCandidate,
    PathwayCandidate,
    RecoProfile,
    RecoResult,
    recommend,
)

# Protected attributes + their values (bias-testing.md §1). NEVER an engine input.
PROTECTED: dict[str, list[str]] = {
    "gender": ["nam", "nu", "khac"],
    "region": ["thanh_thi", "nong_thon"],
    "socioeconomic": ["thap", "trung_binh", "cao"],
    "academic_level": ["yeu", "trung_binh", "kha_gioi"],
}

_RIASEC_LETTERS = ("R", "I", "A", "S", "E", "C")
_COMP_CODES = tuple(f"NL{i}" for i in range(1, 13))
_DEPTHS = (Depth.K, Depth.A, Depth.R)


@dataclass(frozen=True)
class Subject:
    """A synthetic person: an engine ``profile`` + protected attrs kept *outside*.

    The protected attrs live here purely so the fairness metrics can group/flip
    them. They are NEVER passed to :func:`app.reco.engine.recommend` — that is
    the whole point of M1/M2 (the engine cannot see them).
    """

    profile: RecoProfile
    attrs: dict[str, str]


def synthetic_careers() -> list[CareerCandidate]:
    """A fixed, diverse synthetic career library (independent of the DB)."""
    return [
        CareerCandidate(
            id="c-software",
            name="Kỹ sư phần mềm",
            field="technology",
            riasec_codes=("I", "R"),
            required_competencies=("NL5", "NL6"),
            pathway_types=(PathwayType.ACADEMIC, PathwayType.GDNN),
        ),
        CareerCandidate(
            id="c-nurse",
            name="Điều dưỡng viên",
            field="health",
            riasec_codes=("S", "I"),
            required_competencies=("NL3", "NL4"),
            pathway_types=(PathwayType.ACADEMIC, PathwayType.GDNN),
        ),
        CareerCandidate(
            id="c-mechanic",
            name="Kỹ thuật viên cơ khí",
            field="engineering",
            riasec_codes=("R", "C"),
            required_competencies=("NL5", "NL9"),
            pathway_types=(
                PathwayType.VOCATIONAL_SECONDARY,
                PathwayType.GDNN,
                PathwayType.LABOR,
            ),
        ),
        CareerCandidate(
            id="c-designer",
            name="Nhà thiết kế đồ họa",
            field="creative",
            riasec_codes=("A", "E"),
            required_competencies=("NL1", "NL10"),
            pathway_types=(PathwayType.ACADEMIC, PathwayType.GDNN),
        ),
        CareerCandidate(
            id="c-teacher",
            name="Giáo viên",
            field="education",
            riasec_codes=("S", "A"),
            required_competencies=("NL2", "NL7"),
            pathway_types=(PathwayType.ACADEMIC,),
        ),
        CareerCandidate(
            id="c-accountant",
            name="Kế toán viên",
            field="business",
            riasec_codes=("C", "E"),
            required_competencies=("NL6", "NL11"),
            pathway_types=(PathwayType.ACADEMIC, PathwayType.GDNN),
        ),
        CareerCandidate(
            id="c-electrician",
            name="Thợ điện",
            field="trades",
            riasec_codes=("R", "I"),
            required_competencies=("NL9", "NL5"),
            pathway_types=(
                PathwayType.VOCATIONAL_SECONDARY,
                PathwayType.GDNN,
                PathwayType.LABOR,
            ),
        ),
        CareerCandidate(
            id="c-marketer",
            name="Chuyên viên marketing",
            field="business",
            riasec_codes=("E", "A"),
            required_competencies=("NL10", "NL12"),
            pathway_types=(PathwayType.ACADEMIC,),
        ),
    ]


def synthetic_pathways() -> list[PathwayCandidate]:
    """A fixed synthetic set covering all four phân luồng types."""
    return [
        PathwayCandidate(id="p-academic", name="Học tiếp ĐH", type=PathwayType.ACADEMIC),
        PathwayCandidate(
            id="p-voc-sec",
            name="Trường trung học nghề",
            type=PathwayType.VOCATIONAL_SECONDARY,
        ),
        PathwayCandidate(id="p-gdnn", name="GDNN", type=PathwayType.GDNN),
        PathwayCandidate(id="p-labor", name="Lao động", type=PathwayType.LABOR),
    ]


def _make_profile(rng: random.Random) -> RecoProfile:
    """One random-but-seeded engine profile (no protected attribute)."""
    n_letters = rng.randint(2, 4)
    code = "".join(rng.sample(_RIASEC_LETTERS, n_letters))
    n_comps = rng.randint(0, 4)
    comps = rng.sample(_COMP_CODES, n_comps)
    competency_depth = {c: rng.choice(_DEPTHS) for c in comps}
    return RecoProfile(riasec_code=code, competency_depth=competency_depth)


def base_profiles(*, count: int = 40, seed: int = 1234) -> list[RecoProfile]:
    """``count`` diverse, reproducible engine profiles (no protected attrs)."""
    rng = random.Random(seed)
    return [_make_profile(rng) for _ in range(count)]


@dataclass
class CounterfactualSet:
    """A base profile + every single-attribute variant of one protected attr."""

    profile: RecoProfile
    attribute: str
    subjects: list[Subject] = field(default_factory=list)


def counterfactual_pairs(*, count: int = 30, seed: int = 99) -> list[CounterfactualSet]:
    """For each profile and each protected attr, all single-flip variants (M2).

    Every subject in a set shares the *same* profile and differs only in the one
    protected attribute being varied — the classic counterfactual construction.
    Because the profile is identical, the engine (which ignores the attribute)
    must return identical recommendations for all members.
    """
    rng = random.Random(seed)
    profiles = [_make_profile(rng) for _ in range(count)]
    out: list[CounterfactualSet] = []
    for profile in profiles:
        baseline_attrs = {attr: values[0] for attr, values in PROTECTED.items()}
        for attr, values in PROTECTED.items():
            cset = CounterfactualSet(profile=profile, attribute=attr)
            for value in values:
                attrs = dict(baseline_attrs)
                attrs[attr] = value
                cset.subjects.append(Subject(profile=profile, attrs=attrs))
            out.append(cset)
    return out


def matched_cohort(*, per_group: int = 60, seed: int = 7) -> list[Subject]:
    """A cohort whose profiles are *matched* across every protected group (M3/M4/M5).

    We build a shared pool of profiles and assign the SAME pool to every value
    of every protected attribute, so the profile distribution is identical
    across groups. Any output disparity therefore isolates the algorithm.
    """
    rng = random.Random(seed)
    pool = [_make_profile(rng) for _ in range(per_group)]
    subjects: list[Subject] = []
    # Cartesian assignment keeps each group's profile distribution identical.
    for combo in product(*PROTECTED.values()):
        attrs = dict(zip(PROTECTED.keys(), combo, strict=True))
        for profile in pool:
            subjects.append(Subject(profile=profile, attrs=dict(attrs)))
    return subjects


def recommend_for(subject: Subject) -> RecoResult:
    """Run the engine for a subject — passing ONLY the profile (M1 by construction).

    This helper is the single choke point the bias tests use, making it obvious
    that ``subject.attrs`` never reaches :func:`recommend`.
    """
    return recommend(
        subject.profile,
        careers=synthetic_careers(),
        pathways=synthetic_pathways(),
    )


def top_groups(result: RecoResult, n: int = 5) -> list[str]:
    """The top-``n`` recommended career ids (the 'career groups' compared in M2/M3)."""
    return [c.career_id for c in result.careers[:n]]
