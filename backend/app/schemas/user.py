from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email:EmailStr
    password:str = Field(min_length=8, max_length=128)
    role: UserRole


class UserLogin(BaseModel):
    email:EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:UUID
    username: str
    email:EmailStr
    role:UserRole
    created_at:datetime


class LoginResponse(BaseModel):
    message: str = "Login successful"
    user: UserResponse
