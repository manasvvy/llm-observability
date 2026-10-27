from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./llm_observability.db")


engine = create_engine(
    _database_url(),
    future=True,
    connect_args={"check_same_thread": False} if _database_url().startswith("sqlite") else {},
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
