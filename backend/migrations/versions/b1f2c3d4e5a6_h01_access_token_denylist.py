"""h01 access token denylist

Revision ID: b1f2c3d4e5a6
Revises: 5fecd1fe010a
Create Date: 2026-06-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b1f2c3d4e5a6'
down_revision: str | None = '5fecd1fe010a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # H-01: denylist of revoked access-token jtis (logout revocation). Entries
    # live until the token's exp (TTL <=15 min) and are pruned opportunistically.
    op.create_table(
        'revoked_access_token',
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('revoked_access_token', schema=None) as batch_op:
        batch_op.create_index('ix_revoked_access_token_jti', ['jti'], unique=True)
        batch_op.create_index('ix_revoked_access_token_user_id', ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('revoked_access_token', schema=None) as batch_op:
        batch_op.drop_index('ix_revoked_access_token_user_id')
        batch_op.drop_index('ix_revoked_access_token_jti')

    op.drop_table('revoked_access_token')
