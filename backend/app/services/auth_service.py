from sqlalchemy.orm import Session
from datetime import datetime, timezone
import jwt
from sqlalchemy.exc import IntegrityError


from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import(
    create_user,
    get_user_by_email,
)
from app.repositories.revoked_token_repository import is_token_revoked, revoke_token

from app.schemas.user import UserRegister, UserLogin



def register_user(db: Session, user_data: UserRegister) -> User:
    
    PUBLIC_REGISTRATION_ROLES = {
    UserRole.USER,
    UserRole.CLINICIAN,
    UserRole.RESEARCHER,
    UserRole.DATA_SCIENTIST,
    }
    
    email = str(user_data.email)
    
    
    existing_user = get_user_by_email(db,email)

    if existing_user:
        raise ValueError("Email is already registered")
    
    if user_data.role not in PUBLIC_REGISTRATION_ROLES :
        raise ValueError(
            "This role cannot be assigned through public registration"
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        username = user_data.username,
        email=user_data.email,
        password_hash = hashed_password,
        role=user_data.role
    )
    
    try:
        return create_user(db, new_user)
    except IntegrityError as exc:
        raise ValueError("Email is already register") from exc
    

def login_user(db: Session, user_data: UserLogin) -> tuple[str, User]:
    
    email = str(user_data.email)
    
    user = get_user_by_email(db, email)

    if user is None or not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise ValueError("Invalid email or password")

    
    access_token = create_access_token(str(user.id))
    return access_token, user


def logout_user(db: Session, access_token:str) -> None:
    try:
        
        payload = decode_access_token(access_token)
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid access token") from exc
    
    jti = payload.get("jti")
    exp = payload.get("exp")
    subject = payload.get("sub")
    
    if not isinstance(jti, str) or not jti:
        raise ValueError("Invalid access token")
    
    if not isinstance(subject, str) or not subject:
        raise ValueError("Invalid access token")
    
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise ValueError("Invalid access token")
    
    try:
        expires_at = datetime.fromtimestamp(
            exp,
            tz=timezone.utc,
        )
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("Invalid access token") from exc
    
    
    
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("Inavalid or expired access token")
    
    
    if is_token_revoked(db, jti):
        return
    
    
    revoke_token(
        db=db,
        jti=jti,
        expires_at=expires_at,
    )



