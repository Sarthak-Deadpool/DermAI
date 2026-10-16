from uuid import UUID

import jwt

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.config import settings
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import get_user_by_id
from app.repositories.revoked_token_repository import is_token_revoked



def get_current_user(
        token: str | None = Cookie(
            default=None,
            alias=settings.JWT_COOKIE_NAME,
            ),
        db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if token is None:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        subject= payload.get("sub")
        jti = payload.get("jti")
        
        if not isinstance(subject, str) or not subject:
            raise credentials_exception
        
        if not isinstance(jti, str) or not jti:
            raise credentials_exception

        user_id = UUID(subject)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception from None
    
    
    if is_token_revoked(db, jti):
        raise credentials_exception
    
    

    user = get_user_by_id(db, user_id)

    if user is None:
        raise credentials_exception
    
    
    return user
