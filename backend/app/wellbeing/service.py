"""WellbeingService — safe referral pathway to a counselor (FR-71).

Pure business logic, no FastAPI imports (hexagonal, ADR-009).

A student asks for support; the system records a **Tier-3 referral** and routes
it to a counselor in the student's school (reusing ``SchoolMembership`` via the
school repo). If the student has no school counselor, the request is still
recorded — unrouted — so it is never silently dropped.

NG-03 boundary, enforced by construction: this service performs NO diagnosis,
NO risk scoring, and stores NO clinical data. It only creates a routing record
and audits it. There is no code path that derives a severity/risk signal.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.core.audit import IAuditRepo
from app.core.enums import CounselingTier, SupportRequestStatus
from app.core.models import new_uuid
from app.core.trace import emit as trace_emit
from app.wellbeing.models import SupportRequest
from app.wellbeing.repository import IWellbeingRepo


class WellbeingService:
    def __init__(
        self,
        *,
        wellbeing: IWellbeingRepo,
        audit: IAuditRepo,
        find_counselor: Callable[..., Awaitable[str | None]],
    ) -> None:
        self._wellbeing = wellbeing
        self._audit = audit
        # Injected from the school repo (find_counselor_for_student) so the
        # routing reuses SchoolMembership without importing the school service.
        self._find_counselor = find_counselor

    async def request_support(self, *, student_id: str, message: str) -> SupportRequest:
        """Create a Tier-3 referral routed to a same-school counselor (FR-71).

        Routing is best-effort: if no counselor is found, ``counselor_id`` stays
        NULL and the request is still recorded (status ``open``). The referral
        carries only the student's own ``message`` — no diagnosis, no risk score
        (NG-03). Audited.
        """
        counselor_id = await self._find_counselor(student_id=student_id)
        request = SupportRequest(
            id=new_uuid(),
            student_id=student_id,
            counselor_id=counselor_id,
            tier=CounselingTier.TIER_3,
            message=message,
            status=SupportRequestStatus.OPEN,
        )
        await self._wellbeing.add_request(request)
        await self._audit.record(
            action="wellbeing.support_request.created",
            actor_id=student_id,
            target_type="SupportRequest",
            target_id=request.id,
        )
        trace_emit(
            "WellbeingSupportRequest",
            user=student_id,
            state={"routed": counselor_id is not None},
        )
        return request

    async def list_my_requests(self, *, student_id: str) -> list[SupportRequest]:
        """A student's own support requests (CP-4: scoped to themselves)."""
        return await self._wellbeing.list_for_student(student_id=student_id)
