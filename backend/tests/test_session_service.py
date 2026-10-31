from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.database import Base
from app.models.auth_session import AuthSession
from app.models.user import User, UserRole
from app.services.session_service import (
    cleanup_expired_sessions,
    create_session,
    get_valid_session,
    hash_session_id,
    revoke_session,
    revoke_user_sessions,
    rotate_session,
    touch_session,
)


@pytest.fixture
def db_session(monkeypatch):
    """A private in-memory SQLite database; never uses configured DB settings."""
    monkeypatch.setattr(settings, "SESSION_IDLE_TIMEOUT_MINUTES", 30)
    monkeypatch.setattr(settings, "SESSION_ABSOLUTE_TIMEOUT_HOURS", 12)
    monkeypatch.setattr(settings, "SESSION_TOUCH_INTERVAL_SECONDS", 60)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[User.__table__, AuthSession.__table__])
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()


def make_user(db: Session, *, active: bool = True) -> User:
    user = User(
        username=f"user-{uuid4().hex[:8]}",
        email=f"{uuid4().hex}@example.test",
        password_hash="test-only-hash",
        role=UserRole.USER,
        is_active=active,
    )
    db.add(user)
    db.flush()
    return user


def test_session_identifier_is_random_and_only_digest_is_stored(db_session):
    user = make_user(db_session)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    raw, row = create_session(db_session, user, now=now)

    assert len(raw) >= 40
    assert row.id_hash == hash_session_id(raw)
    assert row.id_hash != raw
    assert db_session.get(AuthSession, raw) is None


def test_session_enforces_idle_and_absolute_expiry(db_session):
    user = make_user(db_session)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    raw, row = create_session(db_session, user, now=start)

    assert row.idle_expires_at == start + timedelta(minutes=30)
    assert row.absolute_expires_at == start + timedelta(hours=12)
    assert get_valid_session(db_session, raw, now=start + timedelta(minutes=29))
    assert get_valid_session(db_session, raw, now=start + timedelta(minutes=30)) is None
    assert get_valid_session(db_session, raw, now=start + timedelta(hours=12)) is None


def test_touch_extends_idle_but_never_absolute_expiry(db_session):
    user = make_user(db_session)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    raw, row = create_session(db_session, user, now=start)
    absolute_expiry = row.absolute_expires_at

    assert touch_session(db_session, row, now=start + timedelta(seconds=30)) is False
    assert touch_session(db_session, row, now=start + timedelta(minutes=2)) is True
    assert row.idle_expires_at == start + timedelta(minutes=32)
    assert row.absolute_expires_at == absolute_expiry

    near_absolute = absolute_expiry - timedelta(minutes=5)
    row.last_seen_at = near_absolute - timedelta(minutes=2)
    row.idle_expires_at = absolute_expiry
    assert touch_session(db_session, row, now=near_absolute) is True
    assert row.idle_expires_at == absolute_expiry
    assert row.absolute_expires_at == absolute_expiry
    assert get_valid_session(db_session, raw, now=absolute_expiry) is None


def test_rotation_revokes_old_identifier_and_preserves_absolute_deadline(db_session):
    user = make_user(db_session)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    old_id, old_row = create_session(db_session, user, now=start)
    rotate_at = start + timedelta(minutes=2)

    new_id, new_row = rotate_session(db_session, old_row, now=rotate_at)

    assert old_row.revoked_at == rotate_at
    assert get_valid_session(db_session, old_id, now=rotate_at) is None
    assert new_id != old_id
    assert new_row.absolute_expires_at == old_row.absolute_expires_at
    assert get_valid_session(db_session, new_id, now=rotate_at)


def test_revoke_session_and_revoke_others(db_session):
    user = make_user(db_session)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    keep_id, keep_row = create_session(db_session, user, now=start)
    other_id, other_row = create_session(db_session, user, now=start)
    current = start + timedelta(minutes=1)

    assert revoke_session(db_session, other_row, now=current)
    assert revoke_session(db_session, other_row, now=current) is False
    assert get_valid_session(db_session, other_id, now=current) is None

    third_id, _ = create_session(db_session, user, now=current)
    count = revoke_user_sessions(
        db_session,
        user.id,
        except_id_hash=keep_row.id_hash,
        reason="password_changed",
        now=current + timedelta(minutes=1),
    )

    assert count == 1
    assert get_valid_session(db_session, keep_id, now=current + timedelta(minutes=1))
    assert get_valid_session(db_session, third_id, now=current + timedelta(minutes=1)) is None


def test_inactive_user_cannot_create_or_use_session(db_session):
    user = make_user(db_session, active=False)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="inactive"):
        create_session(db_session, user, now=now)

    user.is_active = True
    raw, _ = create_session(db_session, user, now=now)
    user.is_active = False
    assert get_valid_session(db_session, raw, now=now) is None


def test_cleanup_removes_expired_session_rows_only(db_session):
    user = make_user(db_session)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    expired_id, expired = create_session(db_session, user, now=start)
    active_id, _ = create_session(db_session, user, now=start + timedelta(days=1))
    expired.idle_expires_at = start - timedelta(seconds=1)
    db_session.flush()

    assert cleanup_expired_sessions(db_session, now=start) == 1
    assert db_session.get(AuthSession, hash_session_id(expired_id)) is None
    assert get_valid_session(db_session, active_id, now=start + timedelta(days=1))
