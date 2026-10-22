"""
Async-compatible SQLAlchemy session factory for PostgreSQL (via psycopg 3).

Uses a module-level engine created once at startup from settings.database_url.
The get_db dependency yields a session per request and commits/rolls back cleanly.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True) if settings.database_url else None

SessionLocal: type[Session] | None = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    The session is committed on success and rolled back on exception.
    """
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured.")
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Probe the database with SELECT 1.

    Returns True if reachable, False otherwise. Used by the health endpoint.
    """
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 — health probe catches all DB errors by design
        _ = exc
        return False
