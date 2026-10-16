from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


from app.models.user import User


from app.schemas.user import UserRegister, UserResponse, UserLogin
from app.services.auth_service import register_user, login_user, logout_user


def register_controller(
        db:Session,
        user_data :UserRegister,

)-> UserResponse:
    try:
        user = register_user(db, user_data)
        return UserResponse.model_validate(user)
    except ValueError as exc:
        message = str(exc)
        
        if message == "Email is already registered":
            raise HTTPException (
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            ) from exc
            
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )from exc
        
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        ) from exc


def login_controller(
        db: Session,
        user_data: UserLogin,
) -> tuple[str, User] :

    try:

        return  login_user(db, user_data)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inavalid email or password",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        ) from exc


def logout_controller(
    db: Session,
    access_token: str
) -> None:
    try:
        logout_user(db, access_token)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    except SQLAlchemyError as exc:
     db.rollback()

     raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Logout failed",
    ) from exc
