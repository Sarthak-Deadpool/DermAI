from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.csrf import create_csrf_token, create_session_csrf_token, CSRF_TOKEN_MAX_AGE_SECONDS
from app.dependencies.database import get_db
from app.services.auth_rate_limit_service import consume_csrf_bootstrap_rate_limit
from app.services.session_service import get_valid_session


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/csrf")
def get_csrf_token(
    request: Request,
    response: Response,
    session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = consume_csrf_bootstrap_rate_limit(db, client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many authentication bootstrap requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    resolved = get_valid_session(db, session_id)
    csrf_token = (
        create_session_csrf_token(session_id)
        if resolved is not None and session_id
        else create_csrf_token()
    )
    
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=CSRF_TOKEN_MAX_AGE_SECONDS,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
    )
    
    return{"csrf_token" : csrf_token}
