"""Unit tests for RecoService pure helpers: profile build + serialise.

These exercise the decode/parse branches (RIASEC scores / [CRED_CC6BB3E5] / [CRED_4FA08DDA] + the
school-level parsing and the pathway-None serialisation path without a DB.
"""

from __future__ import annotations

import json

from app.assessments.models import AssessmentInstrument, AssessmentResult
from app.competency.models import Competency, LearnerProgress
from app.core.crypto import FieldCrypto
from app.core.enums import CompetencyArea, Depth, InstrumentType, SchoolLevel
from app.reco.engine import PathwaySuggestion, RecoResult, ScoredCareer
from app.reco.repository import SqlRecoRepo  # noqa: F401  (import sanity)
from app.reco.service import RecoService

from tests.conftest import make_settings


class _NullRepo:
    """Unused by the helper tests — RecoService only needs crypto here."""


def _service() -> RecoService:
    crypto = FieldCrypto(make_settings().field_encryption_key)
    return RecoService(reco=_NullRepo(), audit=None, crypto=crypto)  # type: ignore[arg-type]


def _result(
    crypto: FieldCrypto, instrument_type: InstrumentType, payload: dict
) -> tuple[AssessmentResult, AssessmentInstrument]:
    inst = AssessmentInstrument(id=f"i-{instrument_type.value}", type=instrument_type, version="1")
    res = AssessmentResult(
        id=f"r-{instrument_type.value}",
        user_id="u1",
        instrument_id=inst.id,
        result_payload=crypto.encrypt(json.dumps(payload)),
        key_version=crypto.key_version,
        version=1,
    )
    return res, inst


def test_build_profile_reads_all_three_instruments() -> None:
    svc = _service()
    crypto = FieldCrypto(make_settings().field_encryption_key)
    results = [
        _result(crypto, InstrumentType.RIASEC, {"code": "IRA", "scores": {"I": 9, "R": 7}}),
        _result(crypto, InstrumentType.VIPS, {"dominant": "V"}),
        _result(crypto, InstrumentType.MBTI, {"code": "INTJ"}),
    ]
    comp = Competency(id="cmp5", code="NL5", area=CompetencyArea.C_BUILDING, name_vi="x")
    progress = [
        (
            LearnerProgress(id="lp1", user_id="u1", competency_id="cmp5", depth_achieved=Depth.A),
            comp,
        )
    ]

    profile = svc._build_profile(school_level="upper_secondary", results=results, progress=progress)
    assert profile.riasec_code == "IRA"
    assert profile.riasec_scores == {"I": 9, "R": 7}
    assert profile.vips_dominant == "V"
    assert profile.mbti_code == "INTJ"
    assert profile.competency_depth == {"NL5": Depth.A}
    assert profile.school_level == SchoolLevel.UPPER_SECONDARY


def test_build_profile_tolerates_missing_and_malformed_fields() -> None:
    svc = _service()
    crypto = FieldCrypto(make_settings().field_encryption_key)
    # scores not a dict; vips with no dominant; mbti with no code.
    results = [
        _result(crypto, InstrumentType.RIASEC, {"code": "", "scores": "bad"}),
        _result(crypto, InstrumentType.VIPS, {}),
        _result(crypto, InstrumentType.MBTI, {}),
    ]
    profile = svc._build_profile(school_level="not-a-level", results=results, progress=[])
    assert profile.riasec_code == ""
    assert profile.riasec_scores == {}
    assert profile.vips_dominant is None
    assert profile.mbti_code is None
    assert profile.school_level is None  # unparseable level → None


def test_build_profile_keeps_max_depth_per_competency() -> None:
    svc = _service()
    comp = Competency(id="c", code="NL5", area=CompetencyArea.C_BUILDING, name_vi="x")
    progress = [
        (LearnerProgress(id="a", user_id="u", competency_id="c", depth_achieved=Depth.A), comp),
        (LearnerProgress(id="b", user_id="u", competency_id="c", depth_achieved=Depth.K), comp),
    ]
    profile = svc._build_profile(school_level=None, results=[], progress=progress)
    assert profile.competency_depth == {"NL5": Depth.A}  # max kept, not overwritten down


def test_serialise_with_pathway() -> None:
    result = RecoResult(
        careers=(
            ScoredCareer(
                career_id="c1",
                name="N",
                field="f",
                score=3.0,
                matched_riasec=("I",),
                matched_competencies=("NL5",),
                rationale="vì sao",
            ),
        ),
        pathway=PathwaySuggestion(
            pathway_id="p1",
            name="Học tiếp",
            type=__import__("app.core.enums", fromlist=["PathwayType"]).PathwayType.ACADEMIC,
            rationale="lý do",
        ),
        rationale="tổng quan",
    )
    payload = RecoService._serialise(result)
    assert payload["careers"][0]["career_id"] == "c1"
    assert payload["pathway"]["type"] == "academic"


def test_serialise_without_pathway() -> None:
    result = RecoResult(careers=(), pathway=None, rationale="tổng quan")
    payload = RecoService._serialise(result)
    assert payload["careers"] == []
    assert payload["pathway"] is None
