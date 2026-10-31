from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import Field, field_validator, model_validator
from urllib.parse import urlsplit



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

    APP_ENV: Literal["development", "test", "staging", "production"] = "development"
    SESSION_COOKIE_NAME: str = "dermai_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    SESSION_COOKIE_PATH: str = "/"
    SESSION_COOKIE_DOMAIN: str | None = None
    SESSION_IDLE_TIMEOUT_MINUTES: int = Field(default=30, ge=1, le=720)
    SESSION_ABSOLUTE_TIMEOUT_HOURS: int = Field(default=12, ge=1, le=168)
    SESSION_TOUCH_INTERVAL_SECONDS: int = Field(default=60, ge=1, le=3600)

    CORS_DEVELOPMENT_ORIGINS: str = "http://localhost:5173"
    CORS_PRODUCTION_ORIGINS: str = ""
    CORS_ALLOWED_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    CORS_ALLOWED_HEADERS: str = "Accept,Content-Type,X-CSRF-Token"
    CORS_PREFLIGHT_MAX_AGE_SECONDS: int = Field(default=600, ge=0, le=86400)

    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = Field(default=900, ge=60, le=86400)
    LOGIN_RATE_LIMIT_PER_ACCOUNT: int = Field(default=10, ge=1, le=1000)
    LOGIN_RATE_LIMIT_PER_IP: int = Field(default=100, ge=1, le=10000)
    REGISTER_RATE_LIMIT_PER_IP: int = Field(default=20, ge=1, le=10000)
    CSRF_BOOTSTRAP_RATE_LIMIT_PER_IP: int = Field(default=120, ge=1, le=10000)
    
    CSRF_COOKIE_NAME: str = "dermai_csrf_token"
    CSRF_SECRET_KEY:str = Field(min_length=32)
    MAX_UPLOAD_BYTES: int = Field(default=10 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    MAX_IMAGE_PIXELS: int = Field(default=25_000_000, ge=10_000, le=100_000_000)
    MIN_IMAGE_SIDE: int = Field(default=100, ge=1, le=10000)

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

    @field_validator("SESSION_COOKIE_DOMAIN", mode="before")
    @classmethod
    def normalize_cookie_domain(cls, value):
        return None if value is None or not str(value).strip() else str(value).strip()
    
    @model_validator(mode="after")
    def validate_cookie_settings(self):
        if self.JWT_COOKIE_SAMESITE == "none" and not self.JWT_COOKIE_SECURE:
            raise ValueError(
                 "SameSite='none' requires JWT_COOKIE_SECURE=True"
            )
            
        return self

    @model_validator(mode="after")
    def validate_session_timeouts(self):
        if self.SESSION_IDLE_TIMEOUT_MINUTES >= self.SESSION_ABSOLUTE_TIMEOUT_HOURS * 60:
            raise ValueError("Session idle timeout must be shorter than absolute lifetime")
        if self.SESSION_COOKIE_SAMESITE == "none" and not self.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SAMESITE='none' requires SESSION_COOKIE_SECURE=True")
        if self.APP_ENV in {"staging", "production"} and not self.SESSION_COOKIE_SECURE:
            raise ValueError("SESSION_COOKIE_SECURE must be True in staging and production")
        if not self.SESSION_COOKIE_PATH.startswith("/") or ";" in self.SESSION_COOKIE_PATH:
            raise ValueError("SESSION_COOKIE_PATH must be an absolute cookie path")
        development_origins = self._parse_csv(self.CORS_DEVELOPMENT_ORIGINS)
        production_origins = self._parse_csv(self.CORS_PRODUCTION_ORIGINS)
        if not development_origins:
            raise ValueError("CORS_DEVELOPMENT_ORIGINS must contain at least one origin")
        if self.APP_ENV in {"staging", "production"} and not production_origins:
            raise ValueError("CORS_PRODUCTION_ORIGINS is required in staging and production")
        for origin in development_origins:
            self._validate_origin(origin, production=False)
        for origin in production_origins:
            self._validate_origin(origin, production=True)
        methods = self._parse_csv(self.CORS_ALLOWED_METHODS)
        headers = self._parse_csv(self.CORS_ALLOWED_HEADERS)
        if not methods or not headers or "*" in methods or "*" in headers:
            raise ValueError("CORS methods and headers must be explicit and cannot contain wildcards")
        if any(method.upper() not in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"} for method in methods):
            raise ValueError("CORS_ALLOWED_METHODS contains an unsupported method")
        if "OPTIONS" not in methods:
            raise ValueError("CORS_ALLOWED_METHODS must include OPTIONS")
        return self

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _validate_origin(origin: str, *, production: bool) -> None:
        parts = urlsplit(origin)
        if (
            origin == "*"
            or "*" in origin
            or parts.scheme not in {"http", "https"}
            or not parts.netloc
            or parts.path
            or parts.query
            or parts.fragment
            or parts.username
            or parts.password
        ):
            raise ValueError("CORS origins must be exact scheme and host origins without paths or wildcards")
        if production and parts.scheme != "https":
            raise ValueError("Production CORS origins must use HTTPS")
        if not production and parts.scheme == "http" and parts.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("HTTP development origins are allowed only for loopback hosts")

    @property
    def trusted_origins(self) -> list[str]:
        source = self.CORS_DEVELOPMENT_ORIGINS if self.APP_ENV in {"development", "test"} else self.CORS_PRODUCTION_ORIGINS
        return self._parse_csv(source)

    @property
    def cors_allowed_methods(self) -> list[str]:
        return [method.upper() for method in self._parse_csv(self.CORS_ALLOWED_METHODS)]

    @property
    def cors_allowed_headers(self) -> list[str]:
        return [header.lower() for header in self._parse_csv(self.CORS_ALLOWED_HEADERS)]
        
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
