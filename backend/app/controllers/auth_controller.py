from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


from app.schemas.user import UserRegister, UserResponse, UserLogin, TokenResponse
from app.services.auth_service import register_user, login_user


def register_controller(
        db:Session,
        user_data :UserRegister,

)-> UserResponse:
    try:
        user = register_user(db, user_data)
        return UserResponse.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with these details already exists",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user",
        ) from exc


def login_controller(
        db: Session,
        user_data: UserLogin,
) -> TokenResponse :

    try:
        access_token = login_user(db, user_data)

        return TokenResponse(
            access_token = access_token,
            token_type="bearer",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        ) from exc
