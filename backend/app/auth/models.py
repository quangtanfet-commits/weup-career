"""Auth domain ORM models: User, RefreshToken (spec.md §5)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import AccountStatus, AgeBand, SchoolLevel, UserType
from app.core.models import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user"
    __table_args__ = (Index("ix_user_age_status", "age_band", "account_status"),)

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(120), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    age_band: Mapped[AgeBand] = mapped_column(Enum(AgeBand), nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)
    school_level: Mapped[SchoolLevel] = mapped_column(
        Enum(SchoolLevel), nullable=False, default=SchoolLevel.NONE
    )
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Global/internal content-editor capability (spec §2 "Nội bộ", FR-90). NOT
    # school-scoped: a content_editor manages the versioned public content
    # library system-wide. Minimal, auditable flag (default off) rather than a
    # separate global-role table — only an operator/seed grants it.
    is_content_editor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Session epoch (H-02). Every access token embeds this as the ``sv`` claim;
    # a token whose ``sv`` is below the user's current value is rejected at
    # validation time. Bumped on re-login (kills bare stolen access tokens) and
    # on password change (hard session kill, paired with refresh-family revoke).
    session_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )


class RefreshToken(UUIDMixin, Base):
    __tablename__ = "refresh_token"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)


class RevokedAccessToken(UUIDMixin, Base):
    """Denylisted access-token ``jti`` (H-01).

    Stateless access JWTs (ADR-008) can't be torn down at logout, so logout
    records the token's ``jti`` here until its ``exp``. Token validation rejects
    any ``jti`` present with ``expires_at`` still in the future; entries past
    ``expires_at`` are inert and pruned opportunistically (TTL ≤15 min).
    """

    __tablename__ = "revoked_access_token"

    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
