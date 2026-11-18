"""Database engine, session factory and declarative base (SQLAlchemy 2.x)."""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/calc_db"


def get_database_url() -> str:
    """Read the DB URL from the environment, normalising the driver prefix."""
    url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    # Accept plain postgres:// / postgresql:// URLs and force the psycopg 3 driver.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Importing models registers them on Base.metadata."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
