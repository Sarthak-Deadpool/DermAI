from sqlalchemy.orm import Session
from datetime import datetime, timezone
import jwt


from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import(
    create_user,
    get_user_by_email,
)
from app.repositories.revoked_token_repository import revoke_token

from app.schemas.user import UserRegister, UserLogin



def register_user(db: Session, user_data: UserRegister) -> User:
    existing_user = get_user_by_email(db, user_data.email)

    if existing_user:
        raise ValueError("Email is already registered")
    
    if user_data.role == UserRole.ADMIN :
        raise ValueError(
            "Administrator accounts cannot be created through public registration"
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        username = user_data.username,
        email=user_data.email,
        password_hash = hashed_password,
        role=user_data.role
    )

    return create_user(db, new_user);

def login_user(db: Session, user_data: UserLogin) -> str:
    user = get_user_by_email(db, user_data.email)

    if not user:
        raise ValueError("Invalid email or password")

    password_is_valid = verify_password(
        user_data.password,
        user.password_hash,
    )

    if not password_is_valid:
        raise ValueError("Invalid email or password")

    access_token = create_access_token(str(user.id))

    return access_token


def logout_user(db: Session, access_token:str) -> None:
    try:
        
        payload = decode_access_token(access_token)
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid access token") from exc
    
    jti = payload.get("jti")
    expires_at_timestamp = payload.get("exp")
    
    if not jti or not expires_at_timestamp:
        raise ValueError("Invalid access token")
    
    expires_at = datetime.fromtimestamp(
        expires_at_timestamp,
        tz=timezone.utc
    )
    
    revoke_token(
        db=db,
        jti=jti,
        expires_at=expires_at,
    )


