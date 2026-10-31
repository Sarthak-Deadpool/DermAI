"""Add shared authentication rate-limit buckets.

Revision ID: 20261031_auth_security
Revises: 20261031_auth_sessions
"""
from alembic import op
import sqlalchemy as sa


revision = "20261031_auth_security"
down_revision = "20261031_auth_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_rate_limit_buckets",
        sa.Column("key_hash", sa.String(length=64), primary_key=True),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("attempt_count > 0", name="ck_auth_rate_limit_attempt_count"),
    )


def downgrade():
    op.drop_table("auth_rate_limit_buckets")
