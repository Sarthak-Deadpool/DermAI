from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies.database import get_db
from app.models.user import User
from app.services.session_service import get_valid_session, touch_session


def get_current_user(
    session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        resolved = get_valid_session(db, session_id)
    except ValueError:
        # Reject malformed/oversized cookie values without reflecting them.
        raise credentials_exception from None
    if resolved is None:
        raise credentials_exception

    session, user = resolved
    if touch_session(db, session):
        # The idle timeout is server managed. Persist activity independently of
        # whether the downstream route later commits a business transaction.
        db.commit()
    return user
