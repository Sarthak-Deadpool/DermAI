from fastapi import APIRouter, Depends, Response, status, Cookie, HTTPException
from sqlalchemy.orm import Session

from app.controllers.auth_controller import register_controller, login_controller, logout_controller
from app.dependencies.database import get_db
from app.schemas.user import UserRegister, UserResponse, UserLogin
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.dependencies.authorization import require_roles
from app.core.config import settings



router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    return register_controller(db, user_data)

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,

)
def login(
    user_data : UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    access_token, user = login_controller(db, user_data)
    
    response.set_cookie(
        key=settings.JWT_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=30*60,
        path="/",
    )
    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user),
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


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    response: Response,
    token: str | None = Cookie(
        default=None,
        alias=settings.JWT_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
): 
    if token is None:
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
        
    logout_controller(db, token)
    
    response.delete_cookie(
        key=settings.JWT_COOKIE_NAME,
        path="/",
        secure=settings.JWT_COOKIE_SECURE,
        httponly=True,
        samesite=settings.JWT_COOKIE_SAMESITE
    )
    
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        secure=settings.JWT_COOKIE_SECURE,
        httponly=False,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )
    
    return {"message" : "Logout successful"}