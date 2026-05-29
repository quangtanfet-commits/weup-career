"""AssessmentService — scoring, sensitive-data handling, audit (CP-1/CP-3, FF-19).

Pure business logic, no FastAPI imports (hexagonal, ADR-009). The consent gate
(CP-1/CP-2) is enforced at the router via ``require_career_data_consent``; this
service adds the **assurance gate** (FF-19) for under-16 sensitive processing,
the **field encryption** (ADR-011), **versioning** (FR-15), and — critically —
the **same-transaction audit on every sensitive read** (CP-3, fail-closed).

CP-3 atomicity: the audit repo and the assessment repo share one
``AsyncSession``. ``read_result`` writes the audit record before returning the
decrypted payload; if the audit write raises, the exception propagates, the
session is rolled back by the request boundary, and no payload is returned —
there is no read path that skips audit.
"""

from __future__ import annotations

import json

from app.assessments.models import AssessmentInstrument, AssessmentResult
from app.assessments.repository import IAssessmentRepo
from app.assessments.scoring import score
from app.core.assurance import require_assurance
from app.core.audit import IAuditRepo
from app.core.config import Settings
from app.core.consent import is_under_16
from app.core.crypto import FieldCrypto
from app.core.enums import InstrumentType
from app.core.exceptions import NotFoundError
from app.core.models import new_uuid
from app.core.trace import emit as trace_emit
from app.guardians.repository import IGuardianRepo


class AssessmentService:
    def __init__(
        self,
        *,
        settings: Settings,
        assessments: IAssessmentRepo,
        guardians: IGuardianRepo,
        audit: IAuditRepo,
        crypto: FieldCrypto,
    ) -> None:
        self._settings = settings
        self._assessments = assessments
        self._guardians = guardians
        self._audit = audit
        self._crypto = crypto

    async def list_instruments(self) -> list[AssessmentInstrument]:
        return await self._assessments.list_active_instruments()

    async def submit(
        self,
        *,
        user_id: str,
        age_band: str,
        instrument_type: InstrumentType,
        answers: dict[str, int],
    ) -> AssessmentResult:
        """Score answers, encrypt the payload, persist a new versioned result.

        Consent (CP-1) is already verified by the route dependency. Here we add
        the FF-19 assurance gate for under-16 users before any processing.
        """
        instrument = await self._assessments.get_active_instrument(instrument_type)
        if instrument is None:
            raise NotFoundError("Không tìm thấy bộ công cụ trắc nghiệm")

        # FF-19: gate sensitive processing of under-16 data on guardian-link
        # assurance. No-op at the MVP default (SENSITIVE_MIN_ASSURANCE=low).
        if is_under_16(age_band):
            assurance = await self._guardians.best_assurance_for_child(user_id)
            require_assurance(assurance, self._settings.sensitive_min_assurance)

        # Scoring takes ONLY answers (M1 — no protected attributes).
        payload = score(instrument_type, answers)
        ciphertext = self._crypto.encrypt(json.dumps(payload, separators=(",", ":")))

        version = await self._assessments.next_version(
            user_id=user_id, instrument_id=instrument.id
        )
        result = AssessmentResult(
            id=new_uuid(),
            user_id=user_id,
            instrument_id=instrument.id,
            result_payload=ciphertext,
            key_version=self._crypto.key_version,
            is_sensitive=True,
            version=version,
        )
        await self._assessments.add_result(result)

        # Metadata-only audit (no result content — NFR-10).
        await self._audit.record(
            action="assessment.submitted",
            actor_id=user_id,
            target_type="AssessmentResult",
            target_id=result.id,
        )
        # Gate B conformance trace: spec action ProcessCareerData (CanProcess held).
        trace_emit(
            "ProcessCareerData",
            user=user_id,
            state={"consentAtCreation": "active"},
        )
        return result

    async def read_result(
        self, *, user_id: str, result_id: str
    ) -> tuple[AssessmentResult, dict[str, object]]:
        """Read + decrypt a sensitive result, writing exactly one audit (CP-3).

        Ownership is enforced by the repo (cross-user → not found → 404). The
        audit write happens in the same transaction/session as the read and
        BEFORE the payload is returned: if it raises, the read fails closed.
        """
        result = await self._assessments.get_owned_result(
            result_id=result_id, user_id=user_id
        )
        if result is None:
            raise NotFoundError("Không tìm thấy kết quả trắc nghiệm")

        # CP-3: exactly one sensitive-access audit per read, same transaction.
        await self._audit.record(
            action="assessment.result.read",
            actor_id=user_id,
            target_type="AssessmentResult",
            target_id=result.id,
            is_sensitive_access=True,
        )

        payload = json.loads(self._crypto.decrypt(result.result_payload))
        return result, payload

    async def delete_result(self, *, user_id: str, result_id: str) -> None:
        """Delete a result the caller owns (data-subject right, FR-14)."""
        result = await self._assessments.get_owned_result(
            result_id=result_id, user_id=user_id
        )
        if result is None:
            raise NotFoundError("Không tìm thấy kết quả trắc nghiệm")

        await self._assessments.delete_result(result)
        await self._audit.record(
            action="assessment.result.deleted",
            actor_id=user_id,
            target_type="AssessmentResult",
            target_id=result_id,
            is_sensitive_access=True,
        )
