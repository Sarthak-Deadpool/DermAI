from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers.auth_controller import register_controller, login_controller
from app.dependencies.database import get_db
from app.schemas.user import UserRegister, UserResponse, UserLogin, TokenResponse
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.dependencies.authorization import require_roles



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
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,

)
def login(
    user_data : UserLogin,
    db: Session = Depends(get_db),
):
    return login_controller(db, user_data)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user:User = Depends(get_current_user),
):
    return current_user


# @router.get("/test-admin")
# def test_admin_access(
#     current_user: User = Depends(require_roles(UserRole.USER)),
# ):
#     return {
#         "message": "Admin access granted",
#         "username": current_user.username,
#         "role": current_user.role.value,
#     }