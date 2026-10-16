from fastapi import APIRouter, Response

from app.core.config import settings
from app.core.csrf import create_csrf_token, CSRF_TOKEN_MAX_AGE_SECONDS


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/csrf")
def get_csrf_token(response:Response) -> dict[str, str]:
    csrf_token = create_csrf_token()
    
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=CSRF_TOKEN_MAX_AGE_SECONDS,
        path="/"
    )
    
    return{"csrf_token" : csrf_token}