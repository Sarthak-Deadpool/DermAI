from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    role:str
    created_at:datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type:str= "bearer"