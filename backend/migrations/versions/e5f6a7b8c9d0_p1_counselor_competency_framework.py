"""p1 counselor competency framework

Revision ID: e5f6a7b8c9d0
Revises: e4f5a6b7c8d9
Create Date: 2026-06-04 00:00:00.000000

Two new tables for the P1 counselor-competency slice (FR-100..103, ADR-016):

- ``counselor_competency``: the counseling-practice competency framework
  (ethics, listening, assessment-tool literacy, data safety/BVDLCN, referral
  recognition). Grounded in TT 18/2025. Reference data; seeded separately.

- ``counselor_self_assessment``: versioned self-assessments by a counselor.
  ``scores`` is a semicolon-encoded CODE:rating string (SQLite portability).

Chains after ``e4f5a6b7c8d9`` (P2 labor-market). This module was built in
parallel off ``d3e4f5a6b7c8``; the two-head state was resolved at integration
by rebasing this migration onto the P2 head (see slice design note
docs/slices/p1-counselor-competency.md).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # counselor_competency — the framework reference table
    op.create_table(
        "counselor_competency",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True),
        sa.Column("name_vi", sa.String(255), nullable=False),
        sa.Column("name_en", sa.String(255), nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("source_ref", sa.String(255), nullable=False, server_default=""),
    )
    op.create_index(
        "ix_counselor_competency_code", "counselor_competency", ["code"]
    )

    # counselor_self_assessment — versioned per-counselor self-assessment rows
    op.create_table(
        "counselor_self_assessment",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "counselor_id",
            sa.String(36),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("scores", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "suggested_development_path", sa.Text, nullable=False, server_default=""
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "counselor_id",
            "version",
            name="uq_counselor_self_assessment_version",
        ),
    )
    op.create_index(
        "ix_counselor_self_assessment_counselor",
        "counselor_self_assessment",
        ["counselor_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_counselor_self_assessment_counselor", table_name="counselor_self_assessment"
    )
    op.drop_table("counselor_self_assessment")
    op.drop_index("ix_counselor_competency_code", table_name="counselor_competency")
    op.drop_table("counselor_competency")
