from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email:EmailStr
    password:str = Field(min_length=8, max_length=128)



class UserLogin(BaseModel):
    email:EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:UUID
    username: str
    email:EmailStr
    role:UserRole
    is_active: bool = True
    created_at:datetime


class UserProfileUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=50)


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("role", mode="before")
    @classmethod
    def map_roadmap_role_aliases(cls, value):
        aliases = {"patient_user": UserRole.USER, "ml_engineer": UserRole.DATA_SCIENTIST}
        return aliases.get(value, value) if isinstance(value, str) else value


class LoginResponse(BaseModel):
    message: str = "Login successful"
    user: UserResponse
