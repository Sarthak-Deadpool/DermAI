"""Shared database-backed fixed-window rate limiting for auth endpoints."""

import hashlib
import hmac
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth_rate_limit import AuthRateLimitBucket


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def rate_limit_key(scope: str, identity: str) -> str:
    """Return a domain-separated HMAC so email/IP values are not stored raw."""
    normalized = identity.strip().casefold()
    message = f"dermai-auth-rate-limit-v1:{scope}:{normalized}".encode("utf-8")
    return hmac.new(settings.CSRF_SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()


def consume_rate_limit(
    db: Session,
    *,
    scope: str,
    identity: str,
    limit: int,
    now: datetime | None = None,
) -> tuple[bool, int]:
    """Atomically consume one shared DB counter and return allowed/retry-after.

    PostgreSQL is the production backend. SQLite support is intentionally kept
    for isolated integration tests. Other dialects fail closed instead of
    silently switching to process-local memory.
    """
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        insert = pg_insert
    elif bind.dialect.name == "sqlite":
        insert = sqlite_insert
    else:
        raise RuntimeError("Authentication rate limiting requires PostgreSQL or isolated SQLite")

    current_time = _utc(now or datetime.now(timezone.utc))
    window = timedelta(seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS)
    cutoff = current_time - window
    key_hash = rate_limit_key(scope, identity)

    try:
        # Expire old keys to prevent unbounded accumulation from varied emails/IPs.
        db.execute(
            delete(AuthRateLimitBucket).where(
                AuthRateLimitBucket.window_started_at < cutoff
            )
        )
        statement = insert(AuthRateLimitBucket).values(
            key_hash=key_hash,
            window_started_at=current_time,
            attempt_count=1,
            updated_at=current_time,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[AuthRateLimitBucket.key_hash],
            set_={
                "window_started_at": case(
                    (AuthRateLimitBucket.window_started_at <= cutoff, current_time),
                    else_=AuthRateLimitBucket.window_started_at,
                ),
                "attempt_count": case(
                    (AuthRateLimitBucket.window_started_at <= cutoff, 1),
                    else_=AuthRateLimitBucket.attempt_count + 1,
                ),
                "updated_at": current_time,
            },
        ).returning(
            AuthRateLimitBucket.attempt_count,
            AuthRateLimitBucket.window_started_at,
        )
        attempt_count, window_started_at = db.execute(statement).one()
        db.commit()
    except Exception:
        db.rollback()
        raise

    retry_after = max(
        1,
        math.ceil((_utc(window_started_at) + window - current_time).total_seconds()),
    )
    return attempt_count <= limit, retry_after


def consume_login_rate_limits(
    db: Session, email: str, client_ip: str
) -> tuple[bool, int]:
    ip_allowed, ip_retry = consume_rate_limit(
        db,
        scope="login-ip",
        identity=client_ip,
        limit=settings.LOGIN_RATE_LIMIT_PER_IP,
    )
    if not ip_allowed:
        return False, ip_retry
    return consume_rate_limit(
        db,
        scope="login-account",
        identity=email,
        limit=settings.LOGIN_RATE_LIMIT_PER_ACCOUNT,
    )


def consume_registration_rate_limit(db: Session, client_ip: str) -> tuple[bool, int]:
    return consume_rate_limit(
        db,
        scope="register-ip",
        identity=client_ip,
        limit=settings.REGISTER_RATE_LIMIT_PER_IP,
    )


def consume_csrf_bootstrap_rate_limit(db: Session, client_ip: str) -> tuple[bool, int]:
    return consume_rate_limit(
        db,
        scope="csrf-bootstrap-ip",
        identity=client_ip,
        limit=settings.CSRF_BOOTSTRAP_RATE_LIMIT_PER_IP,
    )
