"""Import all ORM models so `Base.metadata` is fully populated.

Imported by Alembic env and by the test schema bootstrap. Adding a model means
importing it here (single source of truth for the mapped registry).
"""

from __future__ import annotations

from app.assessments.models import (
    AssessmentInstrument,
    AssessmentItem,
    AssessmentResult,
)
from app.auth.models import RefreshToken, User
from app.competency.models import (
    Competency,
    Indicator,
    LearnerDomainPhase,
    LearnerProgress,
)
from app.core.audit_models import AuditLog
from app.core.database import Base
from app.guardians.models import GuardianConsent, GuardianLink

__all__ = [
    "AssessmentInstrument",
    "AssessmentItem",
    "AssessmentResult",
    "AuditLog",
    "Base",
    "Competency",
    "GuardianConsent",
    "GuardianLink",
    "Indicator",
    "LearnerDomainPhase",
    "LearnerProgress",
    "RefreshToken",
    "User",
]
