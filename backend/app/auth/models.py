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
    # Email-ownership proof (N-3, PT-04 residual). Orthogonal to ``account_status``
    # (lifecycle) and ``is_deleted`` — an under-16 user can be email-verified yet
    # still PENDING_GUARDIAN_CONSENT. NULL = unproven; login is gated on this being
    # set (post-credential, so it is never an enumeration oracle). Existing rows
    # backfill to ``created_at`` in the migration to avoid mass lockout.
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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


class EmailVerificationToken(UUIDMixin, Base):
    """Single-use email-verification token (N-3, PT-04 residual).

    Hash-only at rest (mirrors ``RefreshToken``): the raw token travels only in
    the verification link, and only its SHA-256 hash is persisted, so a DB read
    cannot forge a verification. A row is consumed exactly once (``consumed_at``
    set on success) and is otherwise valid until ``expires_at``.
    """

    __tablename__ = "email_verification_token"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
