"""Remove a database default absent from the Case model.

Revision ID: 20261031_srvdef_align
Revises: 20261031_patient_index_alignment
"""
from alembic import op
import sqlalchemy as sa


revision = "20261031_srvdef_align"
down_revision = "20261031_patient_index_alignment"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "cases",
        "status",
        existing_type=sa.String(length=30),
        existing_nullable=False,
        server_default=None,
    )


def downgrade():
    op.alter_column(
        "cases",
        "status",
        existing_type=sa.String(length=30),
        existing_nullable=False,
        server_default="created",
    )
