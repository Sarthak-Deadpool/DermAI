
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import Base, engine
from app.models.user import User
from app.models.case import Case


from app.routes.auth import router as auth_router
from app.routes.cases import router as cases_router

@asynccontextmanager
async def lifespan(app : FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="DermAI API",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(cases_router)


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
