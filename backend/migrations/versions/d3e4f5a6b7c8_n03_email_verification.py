"""n03 email verification

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-06-02 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd3e4f5a6b7c8'
down_revision: str | None = 'c2d3e4f5a6b7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # N-3 (PT-04 residual): prove email ownership before a session is usable.
    # ``email_verified_at`` is orthogonal to account_status/is_deleted: NULL means
    # ownership unproven, a timestamp means proven. Login is gated on it AFTER the
    # password check, so it is never an enumeration oracle.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True)
        )

    # Backfill: every pre-existing account is grandfathered as verified (its
    # email was already in use). Without this, deploying N-3 would lock out the
    # entire existing user base behind a verification link they never received.
    op.execute('UPDATE "user" SET email_verified_at = created_at')

    # Single-use, hash-only verification tokens (mirrors refresh_token at rest).
    op.create_table(
        'email_verification_token',
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('email_verification_token', schema=None) as batch_op:
        batch_op.create_index(
            'ix_email_verification_token_token_hash', ['token_hash'], unique=True
        )
        batch_op.create_index(
            'ix_email_verification_token_user_id', ['user_id'], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table('email_verification_token', schema=None) as batch_op:
        batch_op.drop_index('ix_email_verification_token_user_id')
        batch_op.drop_index('ix_email_verification_token_token_hash')

    op.drop_table('email_verification_token')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('email_verified_at')
