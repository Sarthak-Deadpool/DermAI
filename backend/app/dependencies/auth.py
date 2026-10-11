from uuid import UUID

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import get_user_by_id


bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    auto_error=False,
)

def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        subject= payload.get("sub")
        if  not subject:
            raise credentials_exception

        user_id = UUID(subject)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception from None

    user = get_user_by_id(db, user_id)

    if user is None:
        raise credentials_exception
    return user
