from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import create_user, get_user_by_email
from app.schemas.user import UserLogin, UserRegister


def register_user(db: Session, user_data: UserRegister) -> User:
    email = str(user_data.email)
    if get_user_by_email(db, email):
        raise ValueError("Email is already registered")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        # Public registration can never assign privileged roles.
        role=UserRole.USER,
    )
    try:
        return create_user(db, new_user)
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Email is already registered") from exc


def login_user(db: Session, user_data: UserLogin) -> User:
    email = str(user_data.email)
    user = get_user_by_email(db, email)
    if user is None or not verify_password(user_data.password, user.password_hash):
        raise ValueError("Invalid email or password")
    if not user.is_active:
        raise PermissionError("Account is inactive")
    return user
