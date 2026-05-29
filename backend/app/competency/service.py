"""CompetencyService — competency tree, progress (CP-8), dev-phase inference.

Pure business logic, no FastAPI imports (hexagonal, ADR-009).

CP-8 (progress monotonicity) is the load-bearing invariant here. ``record_indicator``:

- reads the learner's current depth on the indicator's competency (max over
  their append-only ``LearnerProgress`` rows — absence = rank 0 = "none");
- inserts a new row **only** when the indicator's depth outranks the current
  one (``depth_rank`` strictly greater);
- never updates or deletes an existing row, so history is preserved and
  ``depth_achieved`` for any (user, competency) can never decrease.

dev_phase (FR-23): for a ``student`` the phase is *inferred* from
``school_level`` (lower_secondary→exploration, upper_secondary→planning,
primary→awareness) but personal deviation is allowed — an explicitly stored
``LearnerDomainPhase`` row, if present, wins over the inference. ``working``
users may hold several phases at once (one per area), so the stored rows are
authoritative and no inference is applied.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.auth.repository import IUserRepo
from app.competency.models import (
    Competency,
    Indicator,
    LearnerDomainPhase,
    LearnerProgress,
)
from app.competency.repository import ICompetencyRepo
from app.core.audit import IAuditRepo
from app.core.enums import (
    CompetencyArea,
    Depth,
    DevPhase,
    SchoolLevel,
    UserType,
    depth_rank,
)
from app.core.exceptions import NotFoundError
from app.core.models import new_uuid
from app.core.trace import emit as trace_emit

# Default student dev-phase per school level (FR-23, ADR-013). THCS focuses on
# Exploration, THPT on Planning; primary on Awareness. Tertiary/none have no
# default and fall back to Awareness as the safest entry phase.
_STUDENT_PHASE_BY_LEVEL: dict[SchoolLevel, DevPhase] = {
    SchoolLevel.PRIMARY: DevPhase.AWARENESS,
    SchoolLevel.LOWER_SECONDARY: DevPhase.EXPLORATION,
    SchoolLevel.UPPER_SECONDARY: DevPhase.PLANNING,
}


def infer_student_phase(school_level: SchoolLevel | str) -> DevPhase:
    """Default dev_phase for a student from their school level (FR-23)."""
    try:
        level = SchoolLevel(school_level)
    except ValueError:
        return DevPhase.AWARENESS
    return _STUDENT_PHASE_BY_LEVEL.get(level, DevPhase.AWARENESS)


@dataclass(frozen=True)
class CompetencyProgress:
    """Current per-competency progress + the dev_phase of its area."""

    competency: Competency
    depth_achieved: Depth | None
    dev_phase: DevPhase


@dataclass(frozen=True)
class RecordOutcome:
    """Outcome of recording an indicator (CP-8): did depth advance, and to where."""

    competency_id: str
    advanced: bool
    depth_achieved: Depth | None


class CompetencyService:
    def __init__(
        self,
        *,
        competencies: ICompetencyRepo,
        users: IUserRepo,
        audit: IAuditRepo,
    ) -> None:
        self._competencies = competencies
        self._users = users
        self._audit = audit

    async def list_tree(self) -> tuple[list[Competency], dict[str, list[Indicator]]]:
        """Return the 12 competencies plus their indicators grouped by competency id."""
        comps = await self._competencies.list_competencies()
        indicators = await self._competencies.list_indicators()
        by_comp: dict[str, list[Indicator]] = {}
        for ind in indicators:
            by_comp.setdefault(ind.competency_id, []).append(ind)
        return comps, by_comp

    def _current_depth_by_competency(
        self, progress_rows: list[LearnerProgress]
    ) -> dict[str, Depth]:
        """Max attained depth per competency id from append-only rows (CP-8)."""
        current: dict[str, Depth] = {}
        for row in progress_rows:
            best = current.get(row.competency_id)
            if best is None or depth_rank(row.depth_achieved) > depth_rank(best):
                current[row.competency_id] = row.depth_achieved
        return current

    async def _phase_for_area(
        self,
        *,
        stored_by_area: dict[CompetencyArea, DevPhase],
        area: CompetencyArea,
        user_type: UserType | str,
        school_level: SchoolLevel | str,
    ) -> DevPhase:
        """Resolve the dev_phase for an area: stored row wins, else inferred (students)."""
        if area in stored_by_area:
            return stored_by_area[area]
        if str(user_type) == UserType.STUDENT.value:
            return infer_student_phase(school_level)
        # Working user with no stored phase for this area → safe default.
        return DevPhase.AWARENESS

    def _latest_stored_phases(
        self, phase_rows: list[LearnerDomainPhase]
    ) -> dict[CompetencyArea, DevPhase]:
        """Latest stored dev_phase per area (rows arrive ordered by set_at)."""
        latest: dict[CompetencyArea, DevPhase] = {}
        for row in phase_rows:
            latest[row.area] = row.dev_phase  # last write per area wins
        return latest

    async def get_progress(self, *, user_id: str) -> list[CompetencyProgress]:
        """Per-competency depth_achieved + the dev_phase of the competency's area.

        Ownership (CP-4): progress and phase rows are fetched scoped to
        ``user_id`` by the repo, so no foreign learner's data is visible.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Không tìm thấy người dùng")

        comps = await self._competencies.list_competencies()
        progress_rows = await self._competencies.list_progress(user_id)
        phase_rows = await self._competencies.list_domain_phases(user_id)

        current = self._current_depth_by_competency(progress_rows)
        stored_by_area = self._latest_stored_phases(phase_rows)

        out: list[CompetencyProgress] = []
        for comp in comps:
            phase = await self._phase_for_area(
                stored_by_area=stored_by_area,
                area=comp.area,
                user_type=user.user_type,
                school_level=user.school_level,
            )
            out.append(
                CompetencyProgress(
                    competency=comp,
                    depth_achieved=current.get(comp.id),
                    dev_phase=phase,
                )
            )
        return out

    async def record_indicator(self, *, user_id: str, indicator_id: str) -> RecordOutcome:
        """Record attainment of an indicator, advancing depth only (CP-8).

        Inserts a new ``LearnerProgress`` row **iff** the indicator's depth
        strictly outranks the learner's current depth on the competency. If the
        indicator is at or below the current depth, nothing is written
        (``advanced=False``) — no regression, no duplicate downgrade. The
        returned ``depth_achieved`` is the learner's depth on that competency
        *after* the operation.
        """
        indicator = await self._competencies.get_indicator(indicator_id)
        if indicator is None:
            raise NotFoundError("Không tìm thấy chỉ báo năng lực")

        progress_rows = await self._competencies.list_progress(user_id)
        current = self._current_depth_by_competency(progress_rows)
        current_depth = current.get(indicator.competency_id)

        # CP-8: only advance — write iff the new depth strictly outranks current.
        if current_depth is not None and depth_rank(indicator.depth) <= depth_rank(current_depth):
            return RecordOutcome(
                competency_id=indicator.competency_id,
                advanced=False,
                depth_achieved=current_depth,
            )

        row = LearnerProgress(
            id=new_uuid(),
            user_id=user_id,
            competency_id=indicator.competency_id,
            depth_achieved=indicator.depth,
            evidence_ref=f"indicator:{indicator.id}",
        )
        await self._competencies.add_progress(row)
        await self._audit.record(
            action="competency.depth.advanced",
            actor_id=user_id,
            target_type="LearnerProgress",
            target_id=row.id,
        )
        # Gate B conformance trace: spec action Advance (CompetencyProgress.tla).
        trace_emit(
            "AdvanceDepth",
            user=user_id,
            state={
                "competency": indicator.competency_id,
                "depth": depth_rank(indicator.depth),
            },
        )
        return RecordOutcome(
            competency_id=indicator.competency_id,
            advanced=True,
            depth_achieved=indicator.depth,
        )

    async def set_domain_phase(
        self, *, user_id: str, area: CompetencyArea, dev_phase: DevPhase
    ) -> LearnerDomainPhase:
        """Record a (possibly deviating) dev_phase for the learner on an area.

        A new row is appended — students may deviate from the inferred default,
        and working users accumulate one phase per area (non-linear ABCD, FR-23).
        """
        row = LearnerDomainPhase(
            id=new_uuid(),
            user_id=user_id,
            area=area,
            dev_phase=dev_phase,
        )
        await self._competencies.add_domain_phase(row)
        return row
