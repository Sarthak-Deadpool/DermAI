from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import Field, field_validator, model_validator



class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int = Field(default=5432, ge=1, le=65535)
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    JWT_SECRET_KEY: str = Field(min_length=32)
    
    JWT_COOKIE_NAME: str = "dermai_access_token"
    JWT_COOKIE_SECURE: bool = False
    JWT_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    
    CSRF_COOKIE_NAME: str = "dermai_csrf_token"
    CSRF_SECRET_KEY:str = Field(min_length=32)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value:str) -> str:
        value = value.strip()
        
        if len(value) < 32 :
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters"
            )
            
        if value.lower() in {
            "changeme",
            "your-secret-key",
            "secret",
            "replace-me",
        } :
            raise ValueError("JWT_SECRET_KEY must not be a placeholder")
        return value
    
    @model_validator(mode="after")
    def validate_cookie_settings(self):
        if self.JWT_COOKIE_SAMESITE == "none" and not self.JWT_COOKIE_SECURE:
            raise ValueError(
                 "SameSite='none' requires JWT_COOKIE_SECURE=True"
            )
            
        return self
        
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()