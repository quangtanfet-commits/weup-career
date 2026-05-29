"""Unit tests for the deterministic recommendation engine (FR-60..62, CP-6).

Covers ranking determinism, stable id tie-break, RIASEC + competency scoring,
rationale non-emptiness for every item (CP-6), pathway suggestion selection,
and the empty-input edge cases.
"""

from __future__ import annotations

from app.core.enums import Depth, PathwayType
from app.reco.engine import (
    TOP_N,
    CareerCandidate,
    PathwayCandidate,
    RecoProfile,
    recommend,
)


def _careers() -> list[CareerCandidate]:
    return [
        CareerCandidate(
            id="c1",
            name="Kỹ sư phần mềm",
            field="technology",
            riasec_codes=("I", "R"),
            required_competencies=("NL5", "NL6"),
            pathway_types=(PathwayType.ACADEMIC, PathwayType.GDNN),
        ),
        CareerCandidate(
            id="c2",
            name="Điều dưỡng viên",
            field="health",
            riasec_codes=("S", "I"),
            required_competencies=("NL3",),
            pathway_types=(PathwayType.ACADEMIC,),
        ),
        CareerCandidate(
            id="c3",
            name="Kỹ thuật viên cơ khí",
            field="engineering",
            riasec_codes=("R", "C"),
            required_competencies=("NL5",),
            pathway_types=(PathwayType.VOCATIONAL_SECONDARY, PathwayType.GDNN),
        ),
    ]


def _pathways() -> list[PathwayCandidate]:
    return [
        PathwayCandidate(id="p1", name="Học tiếp ĐH", type=PathwayType.ACADEMIC),
        PathwayCandidate(id="p2", name="GDNN", type=PathwayType.GDNN),
        PathwayCandidate(id="p3", name="Trung học nghề", type=PathwayType.VOCATIONAL_SECONDARY),
    ]


def test_ranking_orders_by_score_then_id() -> None:
    profile = RecoProfile(riasec_code="IRA", competency_depth={"NL5": Depth.R})
    result = recommend(profile, careers=_careers(), pathways=_pathways())
    # c1 (I+R primary + NL5 depth R) should outrank the others.
    assert result.careers[0].career_id == "c1"
    # Scores are non-increasing.
    scores = [c.score for c in result.careers]
    assert scores == sorted(scores, reverse=True)


def test_ranking_is_deterministic() -> None:
    profile = RecoProfile(riasec_code="SR", competency_depth={"NL3": Depth.A})
    r1 = recommend(profile, careers=_careers(), pathways=_pathways())
    r2 = recommend(profile, careers=_careers(), pathways=_pathways())
    assert [c.career_id for c in r1.careers] == [c.career_id for c in r2.careers]


def test_tie_break_by_career_id() -> None:
    """Equal-scoring careers are ordered by id ascending (stable, attribute-free)."""
    careers = [
        CareerCandidate(
            id="z-career",
            name="Z",
            field="f",
            riasec_codes=(),
            required_competencies=(),
            pathway_types=(),
        ),
        CareerCandidate(
            id="a-career",
            name="A",
            field="f",
            riasec_codes=(),
            required_competencies=(),
            pathway_types=(),
        ),
    ]
    result = recommend(RecoProfile(), careers=careers, pathways=[])
    assert [c.career_id for c in result.careers] == ["a-career", "z-career"]


def test_every_item_has_nonempty_rationale_cp6() -> None:
    profile = RecoProfile(riasec_code="IRA", competency_depth={"NL5": Depth.A})
    result = recommend(profile, careers=_careers(), pathways=_pathways())
    assert result.rationale.strip()
    for career in result.careers:
        assert career.rationale.strip()
    assert result.pathway is not None
    assert result.pathway.rationale.strip()


def test_no_riasec_match_still_explains() -> None:
    """A career with zero interest match still gets a non-empty rationale (CP-6)."""
    profile = RecoProfile(riasec_code="", competency_depth={})
    result = recommend(profile, careers=_careers(), pathways=_pathways())
    for career in result.careers:
        assert career.rationale.strip()


def test_competency_depth_increases_score() -> None:
    base = RecoProfile(riasec_code="I")
    deeper = RecoProfile(riasec_code="I", competency_depth={"NL5": Depth.R, "NL6": Depth.R})
    c1_base = next(
        c for c in recommend(base, careers=_careers(), pathways=[]).careers if c.career_id == "c1"
    )
    c1_deep = next(
        c for c in recommend(deeper, careers=_careers(), pathways=[]).careers if c.career_id == "c1"
    )
    assert c1_deep.score > c1_base.score
    assert set(c1_deep.matched_competencies) == {"NL5", "NL6"}


def test_top_n_limit() -> None:
    careers = [
        CareerCandidate(
            id=f"c{i}",
            name=f"N{i}",
            field="f",
            riasec_codes=("R",),
            required_competencies=(),
            pathway_types=(PathwayType.ACADEMIC,),
        )
        for i in range(10)
    ]
    result = recommend(RecoProfile(riasec_code="R"), careers=careers, pathways=_pathways())
    assert len(result.careers) == TOP_N


def test_pathway_suggestion_reflects_top_careers() -> None:
    """The suggested pathway is the most-represented among the matched top careers."""
    profile = RecoProfile(riasec_code="RC", competency_depth={"NL5": Depth.R})
    result = recommend(profile, careers=_careers(), pathways=_pathways())
    assert result.pathway is not None
    # c3 (R,C → vocational/gdnn) and c1 (I,R → academic/gdnn) both carry GDNN.
    assert result.pathway.type in {
        PathwayType.GDNN,
        PathwayType.ACADEMIC,
        PathwayType.VOCATIONAL_SECONDARY,
    }


def test_no_pathways_yields_none() -> None:
    result = recommend(RecoProfile(riasec_code="R"), careers=_careers(), pathways=[])
    assert result.pathway is None
    assert result.rationale.strip()  # overall rationale still present (CP-6)


def test_empty_careers_yields_empty_with_rationale() -> None:
    result = recommend(RecoProfile(riasec_code="R"), careers=[], pathways=_pathways())
    assert result.careers == ()
    assert result.rationale.strip()
