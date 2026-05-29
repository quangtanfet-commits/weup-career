"""Deterministic, explainable recommendation engine (FR-60..62, CP-6, NFR-12).

This module is the value core of the slice and is held to the strictest fairness
bar in the codebase (bias-testing.md §2):

**M1 — fairness by construction.** Neither :func:`recommend` nor any helper
here accepts or references a protected attribute (gender / [CRED_BFB94EAE] /
socioeconomic / [CRED_4FDFC169] level / [CRED_C0FA77AC]. They are simply not parameters of
``RecoProfile``. This makes a counterfactual flip (M2) a *structural* no-op:
there is no input to flip, so the output cannot change. The disparate-impact /
parity metrics (M3/M4/M5) therefore measure an engine that is provably blind to
those attributes — any residual skew would have to come from a *proxy* feature,
and there are none here (inputs are RIASEC/VIPS/MBTI + competency depth +
school level/dev phase only).

**Determinism.** No randomness, no I/O, no clock. Ordering is fully determined
by the score and a stable tie-break on career id, so the same profile always
yields the same ranking (reproducible — no seeding needed).

**Explainability (CP-6).** Every ranked career and the overall recommendation
carries a non-empty, human-readable Vietnamese ``rationale`` saying *why*, in
terms of the matched RIASEC letters and competency evidence. The rationale never
mentions a protected attribute (M2) — it cannot, since none are inputs.

The engine matches an immutable profile snapshot against ``CareerCandidate`` and
``PathwayCandidate`` rows the service builds from seeded ``CareerProfile`` /
``Pathway`` reference data, so the engine itself stays free of DB/ORM imports
(hexagonal, ADR-009).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from app.core.enums import (
    DEPTH_LABEL_VI,
    Depth,
    DevPhase,
    PathwayType,
    SchoolLevel,
    depth_rank,
)

# How many careers the engine returns in the ranked list (top-N). Kept >= 5 so
# the M2 counterfactual check (top-5 identical) has a full slice to compare.
TOP_N: int = 5

# Vietnamese display names for pathway types, used only inside rationale prose.
_PATHWAY_LABEL_VI: dict[PathwayType, str] = {
    PathwayType.ACADEMIC: "học tiếp (THPT → Đại học)",
    PathwayType.VOCATIONAL_SECONDARY: "trường trung học nghề",
    PathwayType.GDNN: "giáo dục nghề nghiệp (TC/CĐ nghề)",
    PathwayType.LABOR: "tham gia thị trường lao động",
}


@dataclass(frozen=True)
class CareerCandidate:
    """An immutable view of a seeded ``CareerProfile`` the engine scores.

    Only the fields the engine reasons over are included — deliberately NOT any
    protected attribute. ``riasec_codes`` and ``required_competencies`` are the
    parsed (list) forms of the comma-joined DB columns.
    """

    id: str
    name: str
    field: str
    riasec_codes: tuple[str, ...]
    required_competencies: tuple[str, ...]
    pathway_types: tuple[PathwayType, ...]


@dataclass(frozen=True)
class PathwayCandidate:
    """An immutable view of a seeded ``Pathway`` the engine may suggest."""

    id: str
    name: str
    type: PathwayType


@dataclass(frozen=True)
class RecoProfile:
    """Immutable input snapshot for the engine — NO protected attributes (M1).

    - ``riasec_code`` — the learner's Holland code (e.g. ``"IRA"``); leading
      letters are the dominant interests.
    - ``riasec_scores`` — per-dimension RIASEC totals (optional refinement).
    - ``vips_dominant`` / ``mbti_code`` — carried for explainability/context;
      they do not gate matching in the MVP rule set.
    - ``competency_depth`` — current attained depth per competency code
      (``{"NL5": Depth.A, ...}``); absence = not yet attained.
    - ``school_level`` / ``dev_phase`` — used only to bias the *pathway*
      suggestion (e.g. lower-secondary leans exploration), never the career
      ranking, and never a protected attribute.
    """

    riasec_code: str = ""
    riasec_scores: Mapping[str, int] = field(default_factory=dict)
    vips_dominant: str | None = None
    mbti_code: str | None = None
    competency_depth: Mapping[str, Depth] = field(default_factory=dict)
    school_level: SchoolLevel | None = None
    dev_phase: DevPhase | None = None


@dataclass(frozen=True)
class ScoredCareer:
    """One ranked career with its score and explainable rationale (CP-6)."""

    career_id: str
    name: str
    field: str
    score: float
    matched_riasec: tuple[str, ...]
    matched_competencies: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class PathwaySuggestion:
    """The single suggested pathway with its rationale (FR-62, non-coercive)."""

    pathway_id: str
    name: str
    type: PathwayType
    rationale: str


@dataclass(frozen=True)
class RecoResult:
    """Engine output: ranked careers + a pathway suggestion + overall rationale.

    ``rationale`` (overall) is guaranteed non-empty (CP-6). ``careers`` is the
    deterministic top-N by score with a stable id tie-break.
    """

    careers: tuple[ScoredCareer, ...]
    pathway: PathwaySuggestion | None
    rationale: str


# Scoring weights (deterministic, documented). RIASEC interest match dominates;
# competency evidence is a secondary signal. No protected-attribute term exists.
_W_RIASEC_PRIMARY: float = 3.0  # match on a leading (dominant) RIASEC letter
_W_RIASEC_SECONDARY: float = 1.0  # match on a non-leading RIASEC letter
_W_COMPETENCY_ATTAINED: float = 1.5  # learner has any depth on a required comp
_W_COMPETENCY_DEPTH: float = 0.5  # extra per depth-rank attained (K<A<R)


def _primary_letters(riasec_code: str) -> set[str]:
    """The dominant (leading-3) RIASEC letters of a Holland code."""
    return {c.upper() for c in riasec_code[:3] if c.strip()}


def _all_letters(riasec_code: str) -> set[str]:
    return {c.upper() for c in riasec_code if c.strip()}


def _score_career(profile: RecoProfile, career: CareerCandidate) -> tuple[float, ScoredCareer]:
    """Score one career against the profile and build its rationale (pure)."""
    primary = _primary_letters(profile.riasec_code)
    every = _all_letters(profile.riasec_code)
    career_letters = {c.upper() for c in career.riasec_codes}

    matched_primary = sorted(primary & career_letters)
    matched_secondary = sorted((every - primary) & career_letters)
    matched_riasec = tuple(matched_primary + matched_secondary)

    score = 0.0
    score += _W_RIASEC_PRIMARY * len(matched_primary)
    score += _W_RIASEC_SECONDARY * len(matched_secondary)

    matched_comps: list[tuple[str, Depth]] = []
    for comp in career.required_competencies:
        depth = profile.competency_depth.get(comp)
        if depth is not None:
            matched_comps.append((comp, depth))
            score += _W_COMPETENCY_ATTAINED
            score += _W_COMPETENCY_DEPTH * depth_rank(depth)

    rationale = _career_rationale(career, matched_riasec, matched_comps)
    scored = ScoredCareer(
        career_id=career.id,
        name=career.name,
        field=career.field,
        score=score,
        matched_riasec=matched_riasec,
        matched_competencies=tuple(comp for comp, _ in matched_comps),
        rationale=rationale,
    )
    return score, scored


def _career_rationale(
    career: CareerCandidate,
    matched_riasec: Sequence[str],
    matched_comps: Sequence[tuple[str, Depth]],
) -> str:
    """Build a non-empty Vietnamese rationale for one career (CP-6).

    References ONLY interest (RIASEC) and competency evidence — never a
    protected attribute (M2). Always returns a non-empty string, even when the
    match is weak, so CP-6 holds for every item. ``matched_comps`` are already
    paired with their attained depth, so no re-lookup (and no dead branch).
    """
    parts: list[str] = []
    if matched_riasec:
        parts.append(
            f"Nhóm sở thích RIASEC nổi trội {','.join(matched_riasec)} khớp với '{career.name}'"
        )
    else:
        parts.append(f"'{career.name}' được đưa vào để bạn tham khảo và mở rộng lựa chọn")
    for comp, depth in matched_comps:
        parts.append(f"năng lực {comp} đạt mức {DEPTH_LABEL_VI[depth]}")
    return "; ".join(parts) + "."


def _rank_careers(profile: RecoProfile, careers: Sequence[CareerCandidate]) -> list[ScoredCareer]:
    """Deterministically rank careers: score desc, then career id asc (stable)."""
    scored = [_score_career(profile, c) for c in careers]
    # Stable, fully deterministic ordering: higher score first; ties broken by
    # career id ascending (NOT by name/field, which could correlate with
    # anything) — pure, reproducible, no randomness.
    scored.sort(key=lambda pair: (-pair[0], pair[1].career_id))
    return [s for _, s in scored]


def _suggest_pathway(
    profile: RecoProfile,
    top_careers: Sequence[ScoredCareer],
    careers_by_id: Mapping[str, CareerCandidate],
    pathways: Sequence[PathwayCandidate],
) -> PathwaySuggestion | None:
    """Pick ONE pathway to surface as a *non-coercive* suggestion (FR-62).

    The chosen pathway is the one most represented among the top careers'
    pathway types (deterministic tie-break by ``PathwayType`` order then id).
    This is interest/competency-driven only: ``school_level``/``dev_phase`` are
    NOT used to push a learner toward or away from any track, and no protected
    attribute is involved (M5: circumstance must never coerce phân luồng).
    """
    if not pathways:
        return None

    # Tally pathway types from the matched top careers.
    tally: dict[PathwayType, int] = {}
    for sc in top_careers:
        cand = careers_by_id.get(sc.career_id)
        if cand is None:  # pragma: no cover - top ids always come from candidates
            continue
        for ptype in cand.pathway_types:
            tally[ptype] = tally.get(ptype, 0) + 1

    pathway_order = list(PathwayType)

    def pathway_sort_key(p: PathwayCandidate) -> tuple[int, int, str]:
        # Higher tally first; then a stable, attribute-free order by enum
        # position then id. No socioeconomic/academic input (M5).
        return (-tally.get(p.type, 0), pathway_order.index(p.type), p.id)

    chosen = sorted(pathways, key=pathway_sort_key)[0]
    label = _PATHWAY_LABEL_VI.get(chosen.type, chosen.name)
    rationale = (
        f"Gợi ý hướng '{label}' dựa trên các nghề phù hợp sở thích/năng lực của bạn. "
        "Đây chỉ là lựa chọn có lý do — quyết định cuối cùng thuộc về "
        "bạn/người giám hộ/giáo viên."
    )
    return PathwaySuggestion(
        pathway_id=chosen.id,
        name=chosen.name,
        type=chosen.type,
        rationale=rationale,
    )


def _overall_rationale(
    top_careers: Sequence[ScoredCareer], pathway: PathwaySuggestion | None
) -> str:
    """Compose the overall (non-empty) rationale for the recommendation (CP-6)."""
    if top_careers:
        names = ", ".join(f"'{c.name}'" for c in top_careers[:3])
        head = f"Dựa trên hồ sơ sở thích và năng lực, các nghề gần với bạn nhất: {names}."
    else:
        head = (
            "Chưa đủ dữ liệu hồ sơ để xếp hạng nghề; hãy hoàn thành thêm "
            "trắc nghiệm/hoạt động để nhận gợi ý sát hơn."
        )
    tail = (
        " Mọi gợi ý đều kèm lý do và KHÔNG mang tính ép buộc — "
        "bạn/người giám hộ/giáo viên là người quyết định (FR-62, CP-5)."
    )
    return head + tail


def recommend(
    profile: RecoProfile,
    *,
    careers: Sequence[CareerCandidate],
    pathways: Sequence[PathwayCandidate],
) -> RecoResult:
    """Produce a deterministic, explainable recommendation (FR-60..62, CP-6).

    Pure function: same ``(profile, careers, pathways)`` → same ``RecoResult``.
    ``profile`` carries no protected attributes (M1), so flipping any such
    attribute upstream cannot change this output (M2 is a structural no-op).

    Returns up to :data:`TOP_N` ranked careers, a single pathway suggestion, and
    a guaranteed-non-empty overall rationale.
    """
    ranked = _rank_careers(profile, careers)
    top = tuple(ranked[:TOP_N])
    careers_by_id = {c.id: c for c in careers}
    pathway = _suggest_pathway(profile, top, careers_by_id, pathways)
    rationale = _overall_rationale(top, pathway)
    return RecoResult(careers=top, pathway=pathway, rationale=rationale)
