"""Add an optional patient name to current patient records.

Existing records are preserved and receive NULL. Legacy names from the
pre-M1 backup are not imported or modified by this migration.

Revision ID: 20261031_patient_name
Revises: 20261031_srvdef_align
"""
from alembic import op
import sqlalchemy as sa


revision = "20261031_patient_name"
down_revision = "20261031_srvdef_align"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("patients", sa.Column("patient_name", sa.String(length=150), nullable=True))


def downgrade():
    op.drop_column("patients", "patient_name")
