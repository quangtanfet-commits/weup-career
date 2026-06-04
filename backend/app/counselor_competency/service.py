"""CounselorCompetencyService — framework fetch + self-assessment lifecycle.

Pure business logic, no FastAPI imports (hexagonal, ADR-009).

Responsibilities:
- ``list_competencies``: return the counseling-practice competency framework
  (FR-100). Read-only reference data.
- ``create_self_assessment``: accept a per-competency score dict from a
  counselor, derive a development-path suggestion with explanation (FR-102),
  persist a new versioned row (FR-101). Does NOT touch CP-5/CP-6.
- ``list_self_assessments``: the calling counselor's own history (FR-101).

Privacy / CP-1 isolation (FR-103, ADR-016):
  - Self-assessment data is the counselor's own personal data. This service
    NEVER touches student career data, guardians, assessments, or
    recommendations.
  - No guardian-consent check is performed here. The consent gate (CP-1) is
    for under-16 student career data; a counselor's self-assessment is a
    different legal category (professional development record of an adult).
  - The router wires ``require_counselor`` — not ``require_career_data_consent``.

Development-path suggestion (FR-102):
  - Runs in its own flow, not through CP-5/CP-6.
  - Identifies competencies rated ≤ DEV_PATH_LOW_THRESHOLD (default 2 on 1–5
    scale) as improvement targets.
  - Produces a Vietnamese-language text explaining which competencies need work
    and points to TT 18/2025 training modules as a concrete step.
  - When all scores are high (no low-rated competency), produces a positive
    maintenance message.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.counselor_competency.models import CounselorCompetency, CounselorSelfAssessment
from app.counselor_competency.repository import ICounselorCompetencyRepo
from app.core.exceptions import PermissionDeniedError
from app.core.models import new_uuid
from app.school.repository import ISchoolRepo

# Competencies rated at or below this threshold are flagged as development targets.
DEV_PATH_LOW_THRESHOLD = 2

_SUGGESTION_HEADER = (
    "Kết quả tự đánh giá cho thấy bạn cần tập trung phát triển các năng lực sau:\n"
)
_SUGGESTION_ITEM = (
    "  - {name_vi} ({code}): điểm hiện tại {score}/5 — "
    "khuyến nghị tham gia tập huấn theo {source_ref}.\n"
)
_SUGGESTION_ALL_GOOD = (
    "Kết quả tự đánh giá cho thấy bạn duy trì mức năng lực tốt trên tất cả các năng lực "
    "của khung hành nghề tư vấn (TT 18/2025). "
    "Hãy tiếp tục cập nhật kiến thức chuyên môn và tham gia sinh hoạt chuyên đề định kỳ "
    "để duy trì chất lượng tư vấn."
)
_SUGGESTION_FOOTER = (
    "\nCăn cứ: Thông tư 18/2025/TT-BGDĐT về công tác tư vấn tâm lý, hướng nghiệp học đường. "
    "Đây là công cụ tự phát triển cá nhân — không phải KPI hành chính."
)


def _encode_scores(scores: dict[str, int]) -> str:
    """Encode a CODE→rating dict to the semicolon-delimited string convention."""
    return ";".join(f"{k}:{v}" for k, v in sorted(scores.items()))


def _decode_scores(raw: str) -> dict[str, int]:
    """Decode a semicolon-delimited CODE:rating string to a dict."""
    if not raw:
        return {}
    out: dict[str, int] = {}
    for part in raw.split(";"):
        part = part.strip()
        if ":" not in part:
            continue
        code, _, rating_str = part.partition(":")
        try:
            out[code.strip()] = int(rating_str.strip())
        except ValueError:
            continue
    return out


@dataclass(frozen=True)
class SelfAssessmentResult:
    """Returned from create_self_assessment to the router layer."""

    id: str
    counselor_id: str
    version: int
    scores: dict[str, int]
    suggested_development_path: str
    created_at: object  # datetime — typed as object to avoid circular imports


class CounselorCompetencyService:
    def __init__(
        self,
        *,
        repo: ICounselorCompetencyRepo,
        school: ISchoolRepo,
    ) -> None:
        self._repo = repo
        self._school = school

    # -- authorization helper ------------------------------------------------

    async def _require_counselor(self, *, user_id: str) -> None:
        """Raise ``PermissionDeniedError`` if the user holds no counselor membership.

        Authority is re-derived from ``SchoolMembership`` per request (never
        from the JWT claim) — mirrors the CP-4 pattern.
        """
        from app.core.enums import SchoolRole
        from sqlalchemy import select
        from app.school.models import SchoolMembership

        # Reach into the school repo's session via the internal attribute.
        # This avoids importing FastAPI and stays within the hexagonal boundary.
        session = self._school._session  # type: ignore[attr-defined]
        result = await session.execute(
            select(SchoolMembership.id).where(
                SchoolMembership.user_id == user_id,
                SchoolMembership.role == SchoolRole.COUNSELOR,
            ).limit(1)
        )
        if result.first() is None:
            raise PermissionDeniedError(
                "Chỉ tư vấn viên (counselor) mới có thể truy cập chức năng này"
            )

    # -- framework (FR-100) --------------------------------------------------

    async def list_competencies(
        self, *, actor_id: str
    ) -> list[CounselorCompetency]:
        """Return the full counseling-practice competency framework.

        Counselor membership required; anyone else → PermissionDeniedError.
        """
        await self._require_counselor(user_id=actor_id)
        return await self._repo.list_competencies()

    # -- self-assessment (FR-101/102) ----------------------------------------

    async def create_self_assessment(
        self,
        *,
        counselor_id: str,
        scores: dict[str, int],
    ) -> SelfAssessmentResult:
        """Create a new versioned self-assessment for the calling counselor.

        Derives a development-path suggestion (FR-102) in its own flow —
        NOT through CP-5/CP-6. The suggestion is stored in
        ``suggested_development_path`` together with an explanation.

        CP-1: does NOT invoke require_career_data_consent or any guardian/
        student logic. This is the counselor's own personal data.
        """
        await self._require_counselor(user_id=counselor_id)

        version = await self._repo.next_version(counselor_id=counselor_id)
        path = await self._suggest_development_path(scores=scores)
        raw_scores = _encode_scores(scores)

        row = CounselorSelfAssessment(
            id=new_uuid(),
            counselor_id=counselor_id,
            version=version,
            scores=raw_scores,
            suggested_development_path=path,
        )
        await self._repo.add_self_assessment(row)
        return SelfAssessmentResult(
            id=row.id,
            counselor_id=row.counselor_id,
            version=row.version,
            scores=scores,
            suggested_development_path=row.suggested_development_path,
            created_at=row.created_at,
        )

    async def list_self_assessments(
        self, *, counselor_id: str
    ) -> list[SelfAssessmentResult]:
        """The calling counselor's own assessment history, latest first."""
        await self._require_counselor(user_id=counselor_id)
        rows = await self._repo.list_self_assessments(counselor_id=counselor_id)
        return [
            SelfAssessmentResult(
                id=r.id,
                counselor_id=r.counselor_id,
                version=r.version,
                scores=_decode_scores(r.scores),
                suggested_development_path=r.suggested_development_path,
                created_at=r.created_at,
            )
            for r in rows
        ]

    # -- development-path suggestion (FR-102) --------------------------------

    async def _suggest_development_path(self, *, scores: dict[str, int]) -> str:
        """Produce a development-path suggestion string with explanation.

        Own flow — does NOT import from app.reco or app.competency (FR-102).

        Algorithm:
        1. Collect competency codes with rating ≤ DEV_PATH_LOW_THRESHOLD.
        2. For each such code, look up the framework entry (for the Vietnamese
           name and source_ref).
        3. Build a Vietnamese-language explanation listing the gap areas and
           pointing to TT 18/2025.
        4. If no gaps, produce a positive maintenance message.
        """
        low_codes = [code for code, rating in scores.items() if rating <= DEV_PATH_LOW_THRESHOLD]

        if not low_codes:
            return _SUGGESTION_ALL_GOOD + _SUGGESTION_FOOTER

        lines: list[str] = [_SUGGESTION_HEADER]
        for code in sorted(low_codes):
            competency = await self._repo.get_competency_by_code(code)
            if competency is not None:
                lines.append(
                    _SUGGESTION_ITEM.format(
                        name_vi=competency.name_vi,
                        code=code,
                        score=scores[code],
                        source_ref=competency.source_ref or "TT 18/2025",
                    )
                )
            else:
                # Unknown code — still surface it with a generic note
                lines.append(
                    f"  - {code}: điểm hiện tại {scores[code]}/5 — "
                    "khuyến nghị tham gia tập huấn theo TT 18/2025.\n"
                )

        lines.append(_SUGGESTION_FOOTER)
        return "".join(lines)
