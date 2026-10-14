import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.csrf import validate_csrf_token

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

async def csrf_middleware(request: Request, call_next):
    if request.method not in UNSAFE_METHODS:
        return await call_next(request)

    cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or not header_token:
        return JSONResponse(
            status_code=403,
            content={"detail" : "CSRF token missing"},
        )

    if not secrets.compare_digest(cookie_token, header_token):
        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF token mismatch"},
        )

    if not validate_csrf_token(header_token):
        return JSONResponse(
            status_code=403,
            content={"detail": "Inavalid or expired CSRF token"},
        )

    return await call_next(request)
