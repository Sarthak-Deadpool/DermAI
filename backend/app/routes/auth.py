from fastapi import APIRouter, Depends, Response, status, Cookie, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from uuid import UUID

from app.controllers.auth_controller import register_controller, login_controller
from app.dependencies.database import get_db
from app.schemas.user import UserRegister, UserResponse, UserLogin, UserProfileUpdate, AdminUserUpdate
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.dependencies.authorization import require_roles
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.services.audit_service import record_audit_event
from app.models.auth_session import AuthSession
from app.services.session_service import create_session, hash_session_id, revoke_session, revoke_user_sessions
from app.services.auth_rate_limit_service import consume_login_rate_limits, consume_registration_rate_limit
from app.services.admin_invariant_service import lock_admin_access_changes
from app.core.csrf import create_session_csrf_token, CSRF_TOKEN_MAX_AGE_SECONDS



router = APIRouter(prefix="/auth", tags=["Authentication"])


def _clear_auth_cookies(response: Response, *, clear_csrf: bool = False) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    if clear_csrf:
        response.delete_cookie(
            key=settings.CSRF_COOKIE_NAME,
            path=settings.SESSION_COOKIE_PATH,
            domain=settings.SESSION_COOKIE_DOMAIN,
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=False,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )


def _set_csrf_cookie(response: Response, token: str, *, max_age: int) -> None:
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=max_age,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = consume_registration_rate_limit(db, client_ip)
    if not allowed:
        record_audit_event(db, "registration_rate_limited", "failure", client_ip=client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many authentication requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    user = register_controller(db, user_data)
    record_audit_event(db, "register", "success", user.id, "user", str(user.id), client_ip)
    return user

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,

)
def login(
    user_data : UserLogin,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = consume_login_rate_limits(db, str(user_data.email), client_ip)
    if not allowed:
        record_audit_event(db, "login_rate_limited", "failure", client_ip=client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        user = login_controller(db, user_data)
    except HTTPException:
        record_audit_event(db, "login", "failure", client_ip=client_ip)
        raise
    # Always mint a new random session only after credential verification. A
    # pre-authentication cookie is never adopted, preventing fixation.
    session_id, session = create_session(db, user)
    record_audit_event(
        db,
        "login",
        "success",
        user.id,
        "session",
        session.id_hash,
        client_ip,
    )
    session_csrf_token = create_session_csrf_token(session_id)
    _set_csrf_cookie(response, session_csrf_token, max_age=CSRF_TOKEN_MAX_AGE_SECONDS)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=settings.SESSION_ABSOLUTE_TIMEOUT_HOURS * 60 * 60,
        path=settings.SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
    )
    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user),
        "csrf_token": session_csrf_token,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user:User = Depends(get_current_user),
):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(payload: UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.username = payload.username.strip()
    db.commit(); db.refresh(current_user)
    return current_user


@router.get("/admin/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    return db.query(User).order_by(User.created_at.desc()).limit(100).all()


@router.patch("/admin/users/{user_id}", response_model=UserResponse)
def update_user_access(user_id: str, payload: AdminUserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    try:
        lock_admin_access_changes(db)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Administrator access updates are unavailable.") from exc
    from uuid import UUID
    try:
        target_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found") from None
    target = db.get(User, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    updates = payload.model_dump(exclude_unset=True)
    if not updates or any(value is None for value in updates.values()):
        raise HTTPException(status_code=422, detail="Provide a role and/or active status")
    prior_role = target.role
    prior_active = target.is_active
    will_remain_admin = target.role == UserRole.ADMIN and target.is_active
    loses_admin = updates.get("role", target.role) != UserRole.ADMIN or not updates.get("is_active", target.is_active)
    if will_remain_admin and loses_admin:
        active_admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).count()
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="The last active administrator cannot be removed or deactivated")
    for field, value in updates.items():
        setattr(target, field, value)
    if prior_active and not target.is_active:
        revoke_user_sessions(db, target.id, reason="account_deactivated")
    elif prior_role != target.role:
        revoke_user_sessions(db, target.id, reason="role_changed")
    db.commit(); db.refresh(target)
    record_audit_event(db, "user_access_updated", "success", current_user.id, "user", str(target.id))
    return target


@router.get("/admin/audit", response_model=list[dict])
def list_audit_events(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return [{"id": str(row.id), "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None, "action": row.action, "outcome": row.outcome, "resource_type": row.resource_type, "resource_id": row.resource_id, "client_ip": row.client_ip, "created_at": row.created_at} for row in rows]


@router.get("/sessions")
def list_my_sessions(
    session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_hash = hash_session_id(session_id or "")
    now = datetime.now(timezone.utc)
    rows = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.idle_expires_at > now,
            AuthSession.absolute_expires_at > now,
        )
        .order_by(AuthSession.last_seen_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": str(row.public_id),
            "created_at": row.created_at,
            "last_seen_at": row.last_seen_at,
            "idle_expires_at": row.idle_expires_at,
            "absolute_expires_at": row.absolute_expires_at,
            "is_current": row.id_hash == current_hash,
        }
        for row in rows
    ]


@router.delete("/sessions/{session_public_id}")
def revoke_my_session(
    session_public_id: UUID,
    response: Response,
    request: Request,
    session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(AuthSession)
        .filter(
            AuthSession.public_id == session_public_id,
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at.is_(None),
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    revoke_session(db, row, reason="user_revoked")
    record_audit_event(
        db,
        "session_revoked",
        "success",
        current_user.id,
        "session",
        str(row.public_id),
        request.client.host if request.client else None,
    )
    if session_id and row.id_hash == hash_session_id(session_id):
        _clear_auth_cookies(response)
    return {"message": "Session revoked"}


@router.post("/sessions/revoke-others")
def revoke_other_sessions(
    request: Request,
    session_id: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_hash = hash_session_id(session_id or "")
    count = revoke_user_sessions(
        db,
        current_user.id,
        except_id_hash=current_hash,
        reason="user_revoked_other_sessions",
    )
    record_audit_event(
        db,
        "sessions_revoke_others",
        "success",
        current_user.id,
        "user_sessions",
        str(count),
        request.client.host if request.client else None,
    )
    return {"revoked_count": count}


@router.post("/logout-all")
def logout_all(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = revoke_user_sessions(db, current_user.id, reason="logout_all")
    record_audit_event(
        db,
        "logout_all",
        "success",
        current_user.id,
        "user_sessions",
        str(count),
        request.client.host if request.client else None,
    )
    _clear_auth_cookies(response, clear_csrf=True)
    return {"message": "Logout successful", "revoked_count": count}


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    response: Response,
    request: Request,
    session_id: str | None = Cookie(
        default=None,
        alias=settings.SESSION_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
):
    # Logout is idempotent, including when the browser presents an expired,
    # revoked, malformed, or no-longer-persisted session identifier.
    row = None
    if session_id:
        try:
            row = db.get(AuthSession, hash_session_id(session_id))
        except ValueError:
            row = None
    if row is not None:
        actor_id = row.user_id
        revoke_session(db, row, reason="logout")
        record_audit_event(
            db,
            "logout",
            "success",
            actor_id,
            "session",
            row.id_hash,
            request.client.host if request.client else None,
        )

    _clear_auth_cookies(response, clear_csrf=True)

    return {"message": "Logout successful"}
