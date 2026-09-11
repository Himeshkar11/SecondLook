from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide a scoped SQLAlchemy session for future FastAPI dependencies.

    The session is opened per request and closed in a finally block, keeping
    the database lifecycle explicit and generic.
    """

    if not settings.database_url:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def select_one() -> int | None:
    """Execute a minimal database connectivity probe without exposing secrets.

    If `DATABASE_URL` was not configured, return None so the app can keep
    starting and the database verification can be reported as skipped.
    """

    if not settings.database_url:
        return None

    db = SessionLocal()
    try:
        return int(db.execute(text("SELECT 1")).scalar_one())
    finally:
        db.close()
