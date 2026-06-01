"""h02 session version epoch

Revision ID: c2d3e4f5a6b7
Revises: b1f2c3d4e5a6
Create Date: 2026-06-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: str | None = 'b1f2c3d4e5a6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # H-02: per-user session epoch. Each access token embeds this as the ``sv``
    # claim; tokens with sv below the user's current value are rejected. Existing
    # rows backfill to 1 via the server_default (which also lets legacy tokens
    # without an ``sv`` claim fall through validation unchanged).
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'session_version',
                sa.Integer(),
                nullable=False,
                server_default='1',
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('session_version')
