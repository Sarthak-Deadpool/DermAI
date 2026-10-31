"""Persistence operations for opaque browser sessions.

Functions flush but do not commit so callers can make session changes atomic
with account changes and audit events.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_session import AuthSession
from app.models.user import User


def generate_session_id() -> str:
    """Return a 256-bit opaque identifier suitable for a cookie value."""
    return secrets.token_urlsafe(32)


def hash_session_id(session_id: str) -> str:
    if not session_id or len(session_id) > 128:
        raise ValueError("Session identifier is invalid")
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    # SQLite test connections may return naive datetimes for timezone columns.
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def create_session(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
    absolute_expires_at: datetime | None = None,
) -> tuple[str, AuthSession]:
    if not user.is_active:
        raise ValueError("Cannot create a session for an inactive user")
    issued_at = _utc(now or datetime.now(timezone.utc))
    absolute_expires_at = _utc(absolute_expires_at) if absolute_expires_at else issued_at + timedelta(
        hours=settings.SESSION_ABSOLUTE_TIMEOUT_HOURS
    )
    if absolute_expires_at <= issued_at:
        raise ValueError("Session absolute expiry must be in the future")
    idle_expires_at = min(
        issued_at + timedelta(minutes=settings.SESSION_IDLE_TIMEOUT_MINUTES),
        absolute_expires_at,
    )
    session_id = generate_session_id()
    row = AuthSession(
        id_hash=hash_session_id(session_id),
        user_id=user.id,
        last_seen_at=issued_at,
        idle_expires_at=idle_expires_at,
        absolute_expires_at=absolute_expires_at,
    )
    db.add(row)
    db.flush()
    return session_id, row


def get_valid_session(
    db: Session, session_id: str | None, *, now: datetime | None = None
) -> tuple[AuthSession, User] | None:
    if not session_id:
        return None
    row = db.get(AuthSession, hash_session_id(session_id))
    if row is None or row.revoked_at is not None:
        return None
    current_time = _utc(now or datetime.now(timezone.utc))
    if _utc(row.idle_expires_at) <= current_time or _utc(row.absolute_expires_at) <= current_time:
        return None
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    return row, user


def touch_session(
    db: Session, row: AuthSession, *, now: datetime | None = None
) -> bool:
    """Extend idle expiry at most once per configured cadence, never absolute expiry."""
    current_time = _utc(now or datetime.now(timezone.utc))
    if row.revoked_at is not None:
        return False
    if _utc(row.idle_expires_at) <= current_time or _utc(row.absolute_expires_at) <= current_time:
        return False
    if current_time - _utc(row.last_seen_at) < timedelta(
        seconds=settings.SESSION_TOUCH_INTERVAL_SECONDS
    ):
        return False
    row.last_seen_at = current_time
    row.idle_expires_at = min(
        current_time + timedelta(minutes=settings.SESSION_IDLE_TIMEOUT_MINUTES),
        _utc(row.absolute_expires_at),
    )
    db.flush()
    return True


def rotate_session(
    db: Session, row: AuthSession, *, now: datetime | None = None, reason: str = "rotated"
) -> tuple[str, AuthSession]:
    current_time = _utc(now or datetime.now(timezone.utc))
    if row.revoked_at is not None:
        raise ValueError("Cannot rotate a revoked session")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise ValueError("Cannot rotate a session for an inactive user")
    if _utc(row.idle_expires_at) <= current_time or _utc(row.absolute_expires_at) <= current_time:
        raise ValueError("Cannot rotate an expired session")
    row.revoked_at = current_time
    row.revoke_reason = reason
    new_id, new_row = create_session(
        db, user, now=current_time, absolute_expires_at=row.absolute_expires_at
    )
    db.flush()
    return new_id, new_row


def revoke_session(
    db: Session,
    row: AuthSession,
    *,
    reason: str = "logout",
    now: datetime | None = None,
) -> bool:
    if row.revoked_at is not None:
        return False
    row.revoked_at = _utc(now or datetime.now(timezone.utc))
    row.revoke_reason = reason[:80]
    db.flush()
    return True


def revoke_user_sessions(
    db: Session,
    user_id: UUID,
    *,
    except_id_hash: str | None = None,
    reason: str = "security_change",
    now: datetime | None = None,
) -> int:
    current_time = _utc(now or datetime.now(timezone.utc))
    statement = select(AuthSession).where(
        AuthSession.user_id == user_id,
        AuthSession.revoked_at.is_(None),
        AuthSession.absolute_expires_at > current_time,
    )
    if except_id_hash is not None:
        statement = statement.where(AuthSession.id_hash != except_id_hash)
    rows = db.scalars(statement).all()
    for row in rows:
        row.revoked_at = current_time
        row.revoke_reason = reason[:80]
    db.flush()
    return len(rows)


def cleanup_expired_sessions(db: Session, *, now: datetime | None = None) -> int:
    current_time = _utc(now or datetime.now(timezone.utc))
    result = db.execute(
        delete(AuthSession).where(
            (AuthSession.absolute_expires_at <= current_time)
            | (AuthSession.idle_expires_at <= current_time)
        )
    )
    db.flush()
    return result.rowcount or 0
