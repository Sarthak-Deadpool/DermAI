"""Opt-in PostgreSQL dialect check for the shared auth limiter.

Run only against an explicitly designated loopback database whose name ends
in `_auth_test`, with DERMAI_ALLOW_DISPOSABLE_POSTGRES_TEST=1 set.
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.models.auth_rate_limit import AuthRateLimitBucket
from app.services.auth_rate_limit_service import consume_rate_limit, rate_limit_key


POSTGRES_URL = os.getenv("DERMAI_AUTH_TEST_POSTGRES_URL")
EXPLICIT_DISPOSABLE_OPT_IN = os.getenv("DERMAI_ALLOW_DISPOSABLE_POSTGRES_TEST") == "1"
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL or not EXPLICIT_DISPOSABLE_OPT_IN,
    reason="requires explicit opt-in and a disposable loopback PostgreSQL *_auth_test database",
)


def test_postgres_shared_rate_limit_upsert():
    url = make_url(POSTGRES_URL)
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or not (url.database or "").endswith("_auth_test")
    ):
        pytest.fail("Refusing PostgreSQL test target that is not loopback *_auth_test")

    engine = create_engine(url)
    table_preexisted = inspect(engine).has_table(AuthRateLimitBucket.__tablename__)
    if not table_preexisted:
        AuthRateLimitBucket.__table__.create(engine)

    identity = f"postgres-test-{uuid4().hex}"
    key = rate_limit_key("phase3-postgres-test", identity)
    try:
        with Session(engine) as db:
            assert consume_rate_limit(db, scope="phase3-postgres-test", identity=identity, limit=2)[0]
            assert consume_rate_limit(db, scope="phase3-postgres-test", identity=identity, limit=2)[0]
            allowed, retry_after = consume_rate_limit(
                db, scope="phase3-postgres-test", identity=identity, limit=2
            )
            assert not allowed
            assert retry_after > 0
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(AuthRateLimitBucket).where(AuthRateLimitBucket.key_hash == key)
            )
        if not table_preexisted:
            AuthRateLimitBucket.__table__.drop(engine)
        engine.dispose()
