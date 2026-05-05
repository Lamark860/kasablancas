"""SQLAlchemy engine + session + Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from vlad.config import settings


# для SQLite добавляем check_same_thread=False
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
