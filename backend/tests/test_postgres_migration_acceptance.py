"""Opt-in acceptance against an explicitly disposable local PostgreSQL DB.

Set DERMAI_M1_TEST_POSTGRES_URL to a loopback database ending `_m1_test` and
DERMAI_ALLOW_DISPOSABLE_POSTGRES_TEST=1. Tests create/drop only uniquely named
schemas inside that database; they never touch pre-existing schemas.
"""

import importlib
import os
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect
from sqlalchemy.engine import make_url


POSTGRES_URL = os.getenv("DERMAI_M1_TEST_POSTGRES_URL")
ENABLED = os.getenv("DERMAI_ALLOW_DISPOSABLE_POSTGRES_TEST") == "1"
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL or not ENABLED,
    reason="requires explicit opt-in and a disposable loopback *_m1_test PostgreSQL database",
)

migrations = [
    importlib.import_module("migrations.versions.20261031_m1_privacy_case_image"),
    importlib.import_module("migrations.versions.20261031_auth_sessions"),
    importlib.import_module("migrations.versions.20261031_auth_security"),
]


def _run(revision, connection, operation):
    original = revision.op
    revision.op = Operations(MigrationContext.configure(connection))
    try:
        getattr(revision, operation)()
    finally:
        revision.op = original


def _guarded_url():
    url = make_url(POSTGRES_URL)
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or not (url.database or "").endswith("_m1_test")
    ):
        pytest.fail("Refusing a PostgreSQL target not explicitly named loopback *_m1_test")
    return url


def _create_schema(engine, schema):
    with engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')


def _drop_schema(engine, schema):
    with engine.begin() as connection:
        connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def test_postgres_fresh_chain_constraints_data_and_downgrade_guard():
    engine = sa.create_engine(_guarded_url())
    schema = f"m1_test_{uuid4().hex}"
    _create_schema(engine, schema)
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(f'SET search_path TO "{schema}"')
            connection.commit()
            with connection.begin():
                for revision in migrations:
                    _run(revision, connection, "upgrade")
                inspector = inspect(connection)
                assert {
                    "users", "patients", "cases", "case_notes", "case_events",
                    "images", "auth_sessions", "auth_rate_limit_buckets",
                } <= set(inspector.get_table_names())
                assert {fk["referred_table"] for fk in inspector.get_foreign_keys("cases")} == {
                    "users", "patients"
                }
                assert "ix_cases_owner_user_id" in {
                    index["name"] for index in inspector.get_indexes("cases")
                }
                assert "ck_patient_age_range" in {
                    item["name"] for item in inspector.get_check_constraints("patients")
                }
                assert "ck_case_status" in {
                    item["name"] for item in inspector.get_check_constraints("cases")
                }
                user_id = UUID("154891b5-bb7b-48df-8f01-b139723b8a82")
                patient_id = UUID("a0b7fc62-f9fb-4b1f-9eeb-40aa32a65a0a")
                case_id = UUID("bd0cd7b2-a0b1-469c-8aac-d190b1de41f5")
                connection.execute(
                    sa.text(
                        "INSERT INTO users (id, username, email, password_hash, role) "
                        "VALUES (:id, 'm1pg', 'm1pg@example.test', 'hash', 'clinician')"
                    ),
                    {"id": user_id},
                )
                connection.execute(
                    sa.text(
                        "INSERT INTO patients (id, patient_code, age, gender, clinician_id, created_at) "
                        "VALUES (:id, 'PAT-M1PG', 40, 'unknown', :owner, now())"
                    ),
                    {"id": patient_id, "owner": user_id},
                )
                connection.execute(
                    sa.text(
                        "INSERT INTO cases (id, owner_user_id, patient_id, status) "
                        "VALUES (:id, :owner, :patient, 'created')"
                    ),
                    {"id": case_id, "owner": user_id, "patient": patient_id},
                )
                with connection.begin_nested():
                    with pytest.raises(sa.exc.IntegrityError):
                        connection.execute(
                            sa.text(
                                "INSERT INTO cases (id, owner_user_id, patient_id, status) "
                                "VALUES (:id, :owner, :patient, 'unknown')"
                            ),
                            {"id": uuid4(), "owner": user_id, "patient": patient_id},
                        )
            with connection.begin():
                assert connection.execute(sa.text("SELECT count(*) FROM users")).scalar_one() == 1
                assert connection.execute(sa.text("SELECT count(*) FROM patients")).scalar_one() == 1
                assert connection.execute(sa.text("SELECT count(*) FROM cases")).scalar_one() == 1
                assert connection.execute(
                    sa.text("SELECT patient_id FROM cases WHERE id=:id"), {"id": case_id}
                ).scalar_one() == patient_id

            # Remove the two additive revisions, then prove populated baseline downgrade refuses.
            with connection.begin():
                for revision in reversed(migrations[1:]):
                    _run(revision, connection, "downgrade")
                with pytest.raises(RuntimeError, match="Refusing destructive baseline downgrade"):
                    _run(migrations[0], connection, "downgrade")
                assert connection.execute(sa.text("SELECT count(*) FROM cases")).scalar_one() == 1
    finally:
        _drop_schema(engine, schema)
        engine.dispose()


def test_postgres_refuses_legacy_schema_and_preserves_patient_name():
    engine = sa.create_engine(_guarded_url())
    schema = f"m1_legacy_test_{uuid4().hex}"
    _create_schema(engine, schema)
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(f'SET search_path TO "{schema}"')
            connection.commit()
            with connection.begin():
                connection.exec_driver_sql(
                    "CREATE TABLE patients (id text PRIMARY KEY, name text NOT NULL, gender text)"
                )
                connection.exec_driver_sql(
                    "INSERT INTO patients VALUES ('legacy-p1', 'preserve-me', 'unmapped-value')"
                )
                with pytest.raises(RuntimeError, match="Refusing automatic M1 schema adoption"):
                    _run(migrations[0], connection, "upgrade")
                assert connection.execute(
                    sa.text("SELECT name FROM patients WHERE id='legacy-p1'")
                ).scalar_one() == "preserve-me"
                assert connection.execute(sa.text("SELECT count(*) FROM patients")).scalar_one() == 1
                assert set(inspect(connection).get_table_names()) == {"patients"}
    finally:
        _drop_schema(engine, schema)
        engine.dispose()
