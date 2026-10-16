from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker



from app.core.config import settings

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
class Base(DeclarativeBase):
    
    #Base Class for SQLAlchemy ORM model
    pass

def check_database_connection() -> bool:

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
