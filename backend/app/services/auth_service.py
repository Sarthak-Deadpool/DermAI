from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import(
    create_user,
    get_user_by_email,
)

from app.schemas.user import UserRegister, UserLogin

def register_user(db: Session, user_data: UserRegister) -> User:
    existing_user = get_user_by_email(db, user_data.email)

    if existing_user:
        raise ValueError("Email is already registered")

    hashed_password = hash_password(user_data.password)

    new_user = User(
        username = user_data.username,
        email=user_data.email,
        password_hash = hashed_password,
        role=UserRole.USER,
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