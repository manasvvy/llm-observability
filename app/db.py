from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    """Return a SQLAlchemy-compatible URL for SQLite or hosted PostgreSQL."""
    url = os.getenv("DATABASE_URL", "sqlite:///./llm_observability.db")
    # Hosted PostgreSQL providers commonly supply either URL scheme. Use the
    # psycopg 3 driver installed by requirements.txt for both forms.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


_DATABASE_URL = _database_url()
engine = create_engine(
    _DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def init_db() -> None:
    from app.models.observations import LLMObservation  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
