
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import engine, SessionLocal

from app.models.user import User
from app.models.case import Case, CaseNote, CaseEvent
from app.models.image import Image
from app.models.revoked_token import RevokedToken
from app.models.audit_log import AuditLog
from app.models.auth_rate_limit import AuthRateLimitBucket

from app.middleware.csrf import csrf_middleware


from app.routes.auth import router as auth_router
from app.routes.cases import router as cases_router
from app.routes.image import router as images_router
from app.routes.csrf import router as csrf_router
from app.routes.patient import router as patients_router

@asynccontextmanager
async def lifespan(app : FastAPI):
    yield

app = FastAPI(
    title="DermAI API",
    version="0.1.0",
    lifespan=lifespan
)

app.state.session_factory = SessionLocal

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.trusted_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allowed_methods,
    allow_headers=settings.cors_allowed_headers,
    max_age=settings.CORS_PREFLIGHT_MAX_AGE_SECONDS,
)

app.middleware("http")(csrf_middleware)

app.include_router(auth_router)
app.include_router(csrf_router)
app.include_router(cases_router)
app.include_router(images_router)
app.include_router(patients_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "dermai-api",
    }


@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        )
