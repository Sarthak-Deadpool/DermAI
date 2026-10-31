"""Align patient uniqueness objects with SQLAlchemy model metadata.

Revision ID: 20261031_patient_index_alignment
Revises: 20261031_auth_security
"""
from alembic import op


revision = "20261031_patient_index_alignment"
down_revision = "20261031_auth_security"
branch_labels = None
depends_on = None


def upgrade():
    # The model declares unique=True, index=True for both columns. Keep the
    # uniqueness guarantees while matching the model's unique-index shape.
    op.drop_constraint("patients_patient_code_key", "patients", type_="unique")
    op.drop_constraint("patients_user_id_key", "patients", type_="unique")
    op.drop_index("ix_patients_user_id", table_name="patients")
    op.create_index("ix_patients_user_id", "patients", ["user_id"], unique=True)


def downgrade():
    op.drop_index("ix_patients_user_id", table_name="patients")
    op.create_index("ix_patients_user_id", "patients", ["user_id"], unique=False)
    op.create_unique_constraint("patients_user_id_key", "patients", ["user_id"])
    op.create_unique_constraint("patients_patient_code_key", "patients", ["patient_code"])
