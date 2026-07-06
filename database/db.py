"""
Database engine, session factory, and initialisation helpers.
"""
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings
from database.models import Base

logger = logging.getLogger(__name__)

# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + threads
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record) -> None:
    """Enable WAL mode and foreign-key enforcement on every new connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ── Session factory ────────────────────────────────────────────────────────
# expire_on_commit=False keeps loaded attributes accessible after commit/close,
# which avoids lazy-load errors when ORM objects are used after the session exits.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


# ── Public helpers ─────────────────────────────────────────────────────────
def init_db() -> None:
    """Create all tables (idempotent)."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialised.")
    except Exception as exc:
        logger.error("Database initialisation failed: %s", exc)
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager that yields a Session, commits on success,
    rolls back on any exception, and always closes the session.
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
