"""Assessment domain ORM models (spec.md §5, FR-10/11/13/15, ADR-011).

- ``AssessmentInstrument``  — a versioned RIASEC / [CRED_BFC75A05] / [CRED_3DBF26B0] questionnaire.
- ``AssessmentItem``        — one item, tagged with competency + Điều 5 code.
- ``AssessmentResult``      — a respondent's scored result. ``result_payload`` is
  **encrypted at rest** (Field Crypto, ADR-011); ``is_sensitive`` defaults True;
  results are **versioned, never overwritten** (FR-15). No index on payload
  content (architecture/overview.md §"Lưu ý mã hóa").
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import InstrumentType
from app.core.models import UUIDMixin, utcnow


class AssessmentInstrument(UUIDMixin, Base):
    __tablename__ = "assessment_instrument"
    __table_args__ = (
        Index("ix_assessment_instrument_type_active", "type", "is_active"),
    )

    type: Mapped[InstrumentType] = mapped_column(Enum(InstrumentType), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AssessmentItem(UUIDMixin, Base):
    __tablename__ = "assessment_item"
    __table_args__ = (
        Index("ix_assessment_item_instrument", "instrument_id"),
    )

    instrument_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_instrument.id", ondelete="CASCADE"), nullable=False
    )
    # Stable key the scorer reads (e.g. "R_1"); see assessments/scoring.py.
    item_key: Mapped[str] = mapped_column(String(32), nullable=False)
    competency_code: Mapped[str] = mapped_column(String(16), nullable=False)
    dieu5_code: Mapped[str] = mapped_column(String(8), nullable=False, default="b")
    prompt_vi: Mapped[str] = mapped_column(Text, nullable=False)


class AssessmentResult(UUIDMixin, Base):
    __tablename__ = "assessment_result"
    __table_args__ = (
        # Versioned retrieval per (user, instrument). NOT indexed on payload.
        Index(
            "ix_assessment_result_user_instrument_version",
            "user_id",
            "instrument_id",
            "version",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_instrument.id", ondelete="CASCADE"), nullable=False
    )
    # Ciphertext (Field Crypto wire format). Never plaintext, never indexed.
    result_payload: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
