"""Guardian domain ORM models: GuardianLink, GuardianConsent (spec.md §5,
guardian-verification.md §6)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import (
    AssuranceLevel,
    ConsentStatus,
    VerificationMethod,
)
from app.core.models import UUIDMixin, utcnow


class GuardianLink(UUIDMixin, Base):
    __tablename__ = "guardian_link"
    __table_args__ = (
        Index("ix_guardian_link_child", "child_user_id"),
        Index("ix_guardian_link_guardian", "guardian_user_id"),
    )

    child_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    guardian_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    relationship: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_method: Mapped[VerificationMethod] = mapped_column(
        Enum(VerificationMethod), nullable=False, default=VerificationMethod.EMAIL
    )
    assurance_level: Mapped[AssuranceLevel] = mapped_column(
        Enum(AssuranceLevel), nullable=False, default=AssuranceLevel.LOW
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class GuardianConsent(UUIDMixin, Base):
    __tablename__ = "guardian_consent"
    __table_args__ = (
        Index("ix_guardian_consent_child_status", "child_user_id", "status"),
    )

    child_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    guardian_link_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("guardian_link.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(128), nullable=False, default="career_data")
    status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus), nullable=False, default=ConsentStatus.ACTIVE
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
