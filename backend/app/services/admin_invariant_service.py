"""Database serialization for invariants around administrator access."""

from sqlalchemy import text
from sqlalchemy.orm import Session


POSTGRES_ADMIN_ACCESS_LOCK_KEY = 0x4445524D414931


def lock_admin_access_changes(db: Session) -> None:
    """Serialize role/activation writes before checking the last-admin rule."""
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": POSTGRES_ADMIN_ACCESS_LOCK_KEY},
        )
    elif dialect == "sqlite":
        # SQLite has no row-level FOR UPDATE. A no-op UPDATE acquires its single
        # writer lock before the count/check/write sequence.
        db.execute(text(
            "UPDATE users SET is_active = is_active "
            "WHERE id = (SELECT id FROM users ORDER BY id LIMIT 1)"
        ))
    else:
        raise RuntimeError(
            "Admin access updates require a database-supported invariant lock."
        )
