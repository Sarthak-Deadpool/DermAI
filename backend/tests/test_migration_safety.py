import importlib

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect


m1 = importlib.import_module("migrations.versions.20261031_m1_privacy_case_image")
auth_sessions = importlib.import_module("migrations.versions.20261031_auth_sessions")
auth_security = importlib.import_module("migrations.versions.20261031_auth_security")


def run_revision(revision, connection, operation):
    original = revision.op
    revision.op = Operations(MigrationContext.configure(connection))
    try:
        getattr(revision, operation)()
    finally:
        revision.op = original


def test_fresh_schema_upgrade_builds_explicit_core_and_auth_tables():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        run_revision(m1, connection, "upgrade")
        run_revision(auth_sessions, connection, "upgrade")
        run_revision(auth_security, connection, "upgrade")
        tables = set(inspect(connection).get_table_names())
        assert {
            "users", "patients", "cases", "case_notes", "case_events", "images",
            "audit_logs", "revoked_token", "auth_sessions", "auth_rate_limit_buckets",
        } <= tables
        assert "name" not in {column["name"] for column in inspect(connection).get_columns("patients")}
        assert {fk["referred_table"] for fk in inspect(connection).get_foreign_keys("cases")} == {"users", "patients"}
        indexes = {
            table: {index["name"] for index in inspect(connection).get_indexes(table)}
            for table in ("patients", "cases", "case_notes", "case_events", "images", "auth_sessions")
        }
        assert "ix_patients_patient_code" in indexes["patients"]
        assert "ix_patients_clinician_id" in indexes["patients"]
        assert "ix_cases_owner_user_id" in indexes["cases"]
        assert "ix_cases_patient_id" in indexes["cases"]
        assert "ix_case_notes_case_id" in indexes["case_notes"]
        assert "ix_case_events_case_id" in indexes["case_events"]
        assert "ix_images_sha256" in indexes["images"]
        assert "ix_auth_sessions_user_id" in indexes["auth_sessions"]
        assert "ck_patient_age_range" in {
            item["name"] for item in inspect(connection).get_check_constraints("patients")
        }
        assert "ck_patient_exactly_one_owner" in {
            item["name"] for item in inspect(connection).get_check_constraints("patients")
        }
        assert "ck_case_status" in {
            item["name"] for item in inspect(connection).get_check_constraints("cases")
        }
    engine.dispose()


def test_existing_legacy_schema_fails_closed_without_changing_data():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE patients (id TEXT PRIMARY KEY, name TEXT NOT NULL)")
        connection.exec_driver_sql("INSERT INTO patients (id, name) VALUES ('p1', 'preserve-me')")
        with pytest.raises(RuntimeError, match="Refusing automatic M1 schema adoption"):
            run_revision(m1, connection, "upgrade")
        assert connection.exec_driver_sql("SELECT name FROM patients WHERE id='p1'").scalar_one() == "preserve-me"
        assert set(inspect(connection).get_table_names()) == {"patients"}
    engine.dispose()


def test_baseline_downgrade_refuses_to_drop_existing_application_rows():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        run_revision(m1, connection, "upgrade")
        connection.execute(
            sa.text("INSERT INTO users (id, username, email, password_hash, role) "
                    "VALUES (:id, 'test', 'test@example.com', 'hash', 'user')"),
            {"id": "e2d0f98a-10cd-46a2-bb87-23f37a40c328"},
        )
        with pytest.raises(RuntimeError, match="Refusing destructive baseline downgrade"):
            run_revision(m1, connection, "downgrade")
        assert connection.execute(sa.text("SELECT count(*) FROM users")).scalar_one() == 1
    engine.dispose()


def test_empty_fresh_schema_can_be_downgraded():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        run_revision(m1, connection, "upgrade")
        run_revision(m1, connection, "downgrade")
        assert set(inspect(connection).get_table_names()) == set()
    engine.dispose()
