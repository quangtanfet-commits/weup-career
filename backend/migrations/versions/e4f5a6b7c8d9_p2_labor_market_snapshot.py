"""p2 labor market snapshot

Adds the ``labor_market_snapshot`` table (spec.md §5, FR-34/FR-35; ADR-015).

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-06-04 00:00:00.000000

Two heads are expected: another parallel migration stream branches off the same
head (``d3e4f5a6b7c8``). The lead engineer will serialize / rebase at
integration. Do NOT attempt to resolve the two-head situation here.

Key provenance invariant (ADR-015):
- ``source_ref`` NOT NULL — no snapshot without an authoritative citation.
- ``as_of_date``  NOT NULL — no snapshot without a data timestamp.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e4f5a6b7c8d9"
down_revision: str | None = "d3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "labor_market_snapshot",
        sa.Column("sector", sa.String(length=128), nullable=False),
        sa.Column("salary_range", sa.String(length=128), nullable=False),
        sa.Column("demand_forecast", sa.String(length=255), nullable=False),
        sa.Column("required_skills", sa.String(length=512), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=False),
        # PROVENANCE GUARD — NOT NULL by design (ADR-015 §Decision 2).
        sa.Column("source_ref", sa.String(length=255), nullable=False),
        # DATA TIMESTAMP — NOT NULL by design (ADR-015 §Decision 2).
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("labor_market_snapshot", schema=None) as batch_op:
        batch_op.create_index("ix_lms_sector", ["sector"], unique=False)
        batch_op.create_index("ix_lms_region", ["region"], unique=False)
        batch_op.create_index("ix_lms_sector_region", ["sector", "region"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("labor_market_snapshot", schema=None) as batch_op:
        batch_op.drop_index("ix_lms_sector_region")
        batch_op.drop_index("ix_lms_region")
        batch_op.drop_index("ix_lms_sector")
    op.drop_table("labor_market_snapshot")
