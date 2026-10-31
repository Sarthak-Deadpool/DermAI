"""Create the reviewed DermAI M1 schema on an empty database.

This baseline intentionally refuses to adopt an existing application schema.
Legacy adoption requires a separately reviewed data inventory and explicit
patient-name disposition; this revision never rewrites or drops legacy data.

Revision ID: 20261031_m1
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20261031_m1"
down_revision = None
branch_labels = None
depends_on = None


TABLES = (
    "case_events",
    "case_notes",
    "images",
    "cases",
    "patients",
    "audit_logs",
    "revoked_token",
    "users",
)


def _application_tables(bind) -> set[str]:
    return set(inspect(bind).get_table_names()) - {"alembic_version"}


def upgrade():
    bind = op.get_bind()
    existing = _application_tables(bind)
    if existing:
        raise RuntimeError(
            "Refusing automatic M1 schema adoption: existing tables detected "
            f"({', '.join(sorted(existing))}). Preserve and inventory legacy "
            "data, approve patient-name disposition, then use a separately "
            "reviewed adoption migration. No schema or data was changed."
        )

    user_role = sa.Enum(
        "user", "clinician", "researcher", "data_scientist", "admin",
        name="user_role_enum",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("patient_code", sa.String(length=40), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=30), nullable=False),
        sa.Column("medical_history", sa.String(length=2000), nullable=True),
        sa.Column("known_allergies", sa.String(length=1000), nullable=True),
        sa.Column("fitzpatrick_type", sa.String(length=20), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("clinician_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("age >= 0 AND age <= 120", name="ck_patient_age_range"),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND clinician_id IS NULL) OR "
            "(user_id IS NULL AND clinician_id IS NOT NULL)",
            name="ck_patient_exactly_one_owner",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["clinician_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_code"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_patients_patient_code", "patients", ["patient_code"], unique=True)
    op.create_index("ix_patients_user_id", "patients", ["user_id"])
    op.create_index("ix_patients_clinician_id", "patients", ["clinician_id"])

    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("patient_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_label", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_source", sa.String(length=50), nullable=True),
        sa.Column("capture_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("body_location", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="created", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('created','image_uploaded','quality_assessed','analysis_pending','analyzed','failed')",
            name="ck_case_status",
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cases_owner_user_id", "cases", ["owner_user_id"])
    op.create_index("ix_cases_patient_id", "cases", ["patient_id"])

    op.create_table(
        "case_notes",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("author_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])

    op.create_table(
        "case_events",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_events_case_id", "case_events", ["case_id"])

    op.create_table(
        "images",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_images_case_id", "images", ["case_id"])
    op.create_index("ix_images_sha256", "images", ["sha256"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "revoked_token",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index("ix_revoked_token_expires_at", "revoked_token", ["expires_at"])


def downgrade():
    bind = op.get_bind()
    existing = _application_tables(bind)
    if existing != set(TABLES):
        raise RuntimeError(
            "Refusing downgrade because the database schema differs from the "
            "fresh M1 baseline. No schema or data was changed."
        )
    nonempty = [
        table for table in TABLES
        if bind.execute(sa.text(f'SELECT 1 FROM "{table}" LIMIT 1')).first() is not None
    ]
    if nonempty:
        raise RuntimeError(
            "Refusing destructive baseline downgrade while application rows "
            f"exist in: {', '.join(sorted(nonempty))}. Use the approved restore/forward-recovery plan."
        )

    op.drop_index("ix_revoked_token_expires_at", table_name="revoked_token")
    op.drop_table("revoked_token")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_images_sha256", table_name="images")
    op.drop_index("ix_images_case_id", table_name="images")
    op.drop_table("images")
    op.drop_index("ix_case_events_case_id", table_name="case_events")
    op.drop_table("case_events")
    op.drop_index("ix_case_notes_case_id", table_name="case_notes")
    op.drop_table("case_notes")
    op.drop_index("ix_cases_patient_id", table_name="cases")
    op.drop_index("ix_cases_owner_user_id", table_name="cases")
    op.drop_table("cases")
    op.drop_index("ix_patients_clinician_id", table_name="patients")
    op.drop_index("ix_patients_user_id", table_name="patients")
    op.drop_index("ix_patients_patient_code", table_name="patients")
    op.drop_table("patients")
    op.drop_table("users")
    if bind.dialect.name == "postgresql":
        sa.Enum(
            "user", "clinician", "researcher", "data_scientist", "admin",
            name="user_role_enum",
        ).drop(bind, checkfirst=True)
