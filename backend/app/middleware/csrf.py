import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.csrf import validate_csrf_token, validate_session_csrf_token
from app.db.database import SessionLocal
from app.services.session_service import get_valid_session

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _has_active_session(session_factory, session_id: str) -> bool:
    try:
        with session_factory() as db:
            return get_valid_session(db, session_id) is not None
    except ValueError:
        return False


async def csrf_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if request.method not in UNSAFE_METHODS:
        return await call_next(request)

    origin = request.headers.get("Origin")
    if not origin:
        return JSONResponse(status_code=403, content={"detail": "Origin header required"})
    if origin not in settings.trusted_origins:
        return JSONResponse(status_code=403, content={"detail": "Untrusted request origin"})

    cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token:
        return JSONResponse(status_code=403, content={"detail": "CSRF token missing"})
    if not secrets.compare_digest(cookie_token, header_token):
        return JSONResponse(status_code=403, content={"detail": "CSRF token mismatch"})

    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    session_factory = getattr(request.app.state, "session_factory", SessionLocal)
    has_active_session = False
    if session_id:
        try:
            has_active_session = await run_in_threadpool(
                _has_active_session, session_factory, session_id
            )
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication verification unavailable"},
            )

    if has_active_session and session_id:
        csrf_valid = validate_session_csrf_token(header_token, session_id)
    else:
        # Anonymous CSRF tokens are accepted only when no active server session
        # is presented. This supports login/register and idempotent expired logout.
        csrf_valid = validate_csrf_token(header_token, cookie_token)
    if not csrf_valid:
        return JSONResponse(status_code=403, content={"detail": "Invalid or expired CSRF token"})

    return await call_next(request)
