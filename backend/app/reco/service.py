"""RecoService — generate + confirm explainable recommendations (FR-60..63).

Pure business logic, no FastAPI imports (hexagonal, ADR-009). Governs the two
correctness properties of ADR-012:

- **CP-6 (rationale always present).** ``generate`` refuses to persist a
  recommendation whose rationale is empty/whitespace (``RationaleRequiredError``).
  This is *defence in depth* on top of the DB-level ``NOT NULL`` on
  ``Recommendation.rationale`` — the engine always produces a rationale, the
  service re-checks it, and the database is the last line.
- **CP-5 (human-in-the-loop).** ``generate`` always stores
  ``requires_human_confirmation=True`` and leaves ``confirmed_by`` /
  ``confirmed_decision`` NULL. The system NEVER writes a decision itself; only
  ``confirm`` does, and only on behalf of an authorised human.

Fairness (M1): the engine profile this service builds carries NO protected
attribute. The build reads RIASEC/VIPS/MBTI results + competency depth + school
level/dev phase only — protected attributes are never collected here, so they
cannot reach the engine.

Audit (FR-63 / [CRED_C6BAB85F]: both ``generate`` and ``confirm`` write an append-only
audit row (input → reco → who confirmed what), and emit a Gate-B conformance
trace mirroring the ``RecommendationGovernance`` TLA+ actions.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from app.assessments.models import AssessmentInstrument, AssessmentResult
from app.competency.models import Competency, LearnerProgress
from app.core.audit import IAuditRepo
from app.core.authz import can_access
from app.core.crypto import FieldCrypto
from app.core.enums import (
    Depth,
    DevPhase,
    InstrumentType,
    RecoDecision,
    SchoolLevel,
    depth_rank,
)
from app.core.exceptions import NotFoundError, RationaleRequiredError
from app.core.models import new_uuid
from app.core.trace import emit as trace_emit
from app.guardians.repository import IGuardianRepo
from app.reco.engine import (
    CareerCandidate,
    PathwayCandidate,
    RecoProfile,
    RecoResult,
    ScoredCareer,
    recommend,
)
from app.reco.models import Recommendation
from app.reco.repository import IRecoRepo


def _split(codes: str) -> tuple[str, ...]:
    """Split a comma-joined code string into a clean tuple."""
    return tuple(c for c in (part.strip() for part in codes.split(",")) if c)


class RecoService:
    def __init__(
        self,
        *,
        reco: IRecoRepo,
        audit: IAuditRepo,
        crypto: FieldCrypto,
        guardians: IGuardianRepo | None = None,
        counselor_access: Callable[..., Awaitable[bool]] | None = None,
    ) -> None:
        self._reco = reco
        self._audit = audit
        self._crypto = crypto
        # G-6 (CP-4/CP-5): relational access for read/confirm of ANOTHER user's
        # recommendation. ``guardians`` powers the guardian↔child path;
        # ``counselor_access`` (school repo's has_counselor_access) the
        # counselor↔student path. Both optional so unit tests can construct a
        # generate-only service.
        self._guardians = guardians
        self._counselor_access = counselor_access

    # -- profile assembly --------------------------------------------------

    def _decode_payload(self, result: AssessmentResult) -> dict[str, object]:
        """Decrypt + parse a result payload (no protected attributes inside)."""
        parsed: dict[str, object] = json.loads(self._crypto.decrypt(result.result_payload))
        return parsed

    def _build_profile(
        self,
        *,
        school_level: str | None,
        results: list[tuple[AssessmentResult, AssessmentInstrument]],
        progress: list[tuple[LearnerProgress, Competency]],
    ) -> RecoProfile:
        """Assemble the engine profile from sensitive results + progress (M1-clean).

        Reads ONLY interest/competency signals. No protected attribute is read,
        derived, or attached — so the engine cannot branch on one (M1/M2).
        """
        riasec_code = ""
        riasec_scores: dict[str, int] = {}
        vips_dominant: str | None = None
        mbti_code: str | None = None

        for result, instrument in results:
            payload = self._decode_payload(result)
            if instrument.type == InstrumentType.RIASEC:
                riasec_code = str(payload.get("code", "") or "")
                raw_scores = payload.get("scores", {})
                if isinstance(raw_scores, dict):
                    riasec_scores = {
                        str(k): int(v) for k, v in raw_scores.items() if isinstance(v, int)
                    }
            elif instrument.type == InstrumentType.VIPS:
                dom = payload.get("dominant")
                vips_dominant = str(dom) if dom is not None else None
            else:  # InstrumentType.MBTI — the only remaining instrument type.
                code = payload.get("code")
                mbti_code = str(code) if code is not None else None

        # Current (max) depth per competency code from append-only rows (CP-8).
        depth_by_comp: dict[str, Depth] = {}
        for row, comp in progress:
            best = depth_by_comp.get(comp.code)
            if best is None or depth_rank(row.depth_achieved) > depth_rank(best):
                depth_by_comp[comp.code] = row.depth_achieved

        level: SchoolLevel | None = None
        phase: DevPhase | None = None
        if school_level:
            try:
                level = SchoolLevel(school_level)
            except ValueError:
                level = None

        return RecoProfile(
            riasec_code=riasec_code,
            riasec_scores=riasec_scores,
            vips_dominant=vips_dominant,
            mbti_code=mbti_code,
            competency_depth=depth_by_comp,
            school_level=level,
            dev_phase=phase,
        )

    @staticmethod
    def _serialise(result: RecoResult) -> dict[str, object]:
        """Engine result → JSON-safe payload stored on the recommendation."""

        def career_dict(c: ScoredCareer) -> dict[str, object]:
            return {
                "career_id": c.career_id,
                "name": c.name,
                "field": c.field,
                "score": c.score,
                "matched_riasec": list(c.matched_riasec),
                "matched_competencies": list(c.matched_competencies),
                "rationale": c.rationale,
            }

        payload: dict[str, object] = {
            "careers": [career_dict(c) for c in result.careers],
            "pathway": None,
        }
        if result.pathway is not None:
            payload["pathway"] = {
                "pathway_id": result.pathway.pathway_id,
                "name": result.pathway.name,
                "type": result.pathway.type.value,
                "rationale": result.pathway.rationale,
            }
        return payload

    # -- commands ----------------------------------------------------------

    async def generate(self, *, user_id: str, school_level: str | None = None) -> Recommendation:
        """Build a profile, run the engine, persist a *proposed* recommendation.

        Consent (CP-1) is verified by the route dependency. Here we assemble the
        engine inputs, run the deterministic engine, and persist with
        ``requires_human_confirmation=True`` and NO decision (CP-5). Refuses to
        persist a rationale-less recommendation (CP-6 guard).
        """
        results = await self._reco.latest_results(user_id)
        progress = await self._reco.progress_rows(user_id)
        career_rows = await self._reco.list_careers()
        pathway_rows = await self._reco.list_pathways()

        careers = [
            CareerCandidate(
                id=c.id,
                name=c.name,
                field=c.field,
                riasec_codes=_split(c.riasec_codes),
                required_competencies=_split(c.required_competencies),
                pathway_types=tuple(p.type for p in c.pathways),
            )
            for c in career_rows
        ]
        pathways = [PathwayCandidate(id=p.id, name=p.name, type=p.type) for p in pathway_rows]

        profile = self._build_profile(school_level=school_level, results=results, progress=progress)
        result = recommend(profile, careers=careers, pathways=pathways)

        rationale = result.rationale
        # CP-6 (defence in depth): never persist an empty/whitespace rationale,
        # even though the engine always supplies one and the DB column is NOT NULL.
        if not rationale or not rationale.strip():
            raise RationaleRequiredError()

        reco = Recommendation(
            id=new_uuid(),
            user_id=user_id,
            payload=self._serialise(result),
            rationale=rationale,
            requires_human_confirmation=True,
            confirmed_by=None,
            confirmed_decision=None,
        )
        await self._reco.add(reco)

        # FR-63 / [CRED_C6BAB85F]: record that a recommendation was produced for this user.
        await self._audit.record(
            action="recommendation.created",
            actor_id=user_id,
            target_type="Recommendation",
            target_id=reco.id,
        )
        # Gate B conformance trace: RecommendationGovernance!Propose.
        trace_emit(
            "RecommendationCreated",
            user=user_id,
            state={
                "reco": reco.id,
                "requiresHumanConfirmation": True,
                "hasRationale": True,
                "confirmedDecision": None,
            },
        )
        return reco

    async def _accessible_reco(self, *, actor_id: str, reco_id: str) -> Recommendation | None:
        """Fetch a recommendation the actor may access relationally (CP-4, G-6).

        The actor is allowed iff they OWN it, or are a verified guardian of, or
        an assigned counselor of, the owner. When no relational repos were wired
        (generate-only service), this collapses to owner-only. A recommendation
        the actor cannot reach returns ``None`` → 404 (no existence disclosure).
        """
        reco = await self._reco.get_by_id(reco_id)
        if reco is None:
            return None
        if reco.user_id == actor_id:
            return reco
        if self._guardians is None:
            return None
        allowed = await can_access(
            actor_id=actor_id,
            owner_id=reco.user_id,
            guardian_repo=self._guardians,
            counselor_check=self._counselor_check_adapter(),
        )
        return reco if allowed else None

    def _counselor_check_adapter(self) -> Callable[[str, str], Awaitable[bool]] | None:
        """Adapt the school repo's keyword hook to ``can_access``' positional one."""
        access = self._counselor_access
        if access is None:
            return None

        async def _check(actor_id: str, owner_id: str) -> bool:
            return await access(counselor_id=actor_id, student_id=owner_id)

        return _check

    async def confirm(
        self, *, user_id: str, reco_id: str, decision: RecoDecision
    ) -> Recommendation:
        """Record a HUMAN decision on a recommendation — the only path to effect (CP-5).

        G-6 (CP-4 + CP-5): the confirmer may be the owner OR an authorised human
        relation (verified guardian / assigned counselor). A recommendation the
        caller has no relation to is not found (→ 404), never confirmed. CP-5 is
        preserved: ``confirmed_by`` is set to the ACTUAL confirming human
        (``user_id``) — still a real person, never the system — and the
        rationale (CP-6) is untouched. The system never reaches this code on its
        own; only an authenticated human POST does.
        """
        reco = await self._accessible_reco(actor_id=user_id, reco_id=reco_id)
        if reco is None:
            raise NotFoundError("Không tìm thấy gợi ý")

        reco.confirmed_by = user_id
        reco.confirmed_decision = decision
        await self._reco.add(reco)

        # FR-63 / [CRED_C6BAB85F]: record who confirmed what.
        await self._audit.record(
            action="recommendation.confirmed",
            actor_id=user_id,
            target_type="Recommendation",
            target_id=reco.id,
        )
        # Gate B conformance trace: RecommendationGovernance!Confirm.
        trace_emit(
            "RecommendationConfirmed",
            user=user_id,
            state={
                "reco": reco.id,
                "confirmedBy": user_id,
                "confirmedDecision": decision.value,
            },
        )
        return reco

    async def get_for_actor(self, *, user_id: str, reco_id: str) -> Recommendation:
        """Fetch a recommendation the caller may access relationally, or 404 (G-6).

        Allowed for the owner, a verified guardian, or an assigned counselor
        (CP-4). Cross-relation → 404 (existence-hiding).
        """
        reco = await self._accessible_reco(actor_id=user_id, reco_id=reco_id)
        if reco is None:
            raise NotFoundError("Không tìm thấy gợi ý")
        return reco
