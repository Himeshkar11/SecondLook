"""Demo Government repository.

This repository is intentionally the thin SQLAlchemy-backed read model that
allows the demo integrations to obtain deterministic government
verification records from the Supabase PostgreSQL demo table called
`demo_government_records`.

The repository is the source-of-truth read boundary for M12 and must not
mask missing data with provider-local hardcoded responses.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.connection import SessionLocal


class DemoGovernmentRepositoryError(RuntimeError):
    """Base error for repository lookup failures."""


class DemoGovernmentRepositoryUnavailable(DemoGovernmentRepositoryError):
    """Raised when the configured database connection is not usable."""


class DemoGovernmentRepository:
    """Repository wrapper that reads demo government rows via SQLAlchemy."""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session

    def find_by_provider_and_identifier(self, provider: str, identifier: str) -> dict[str, Any] | None:
        """Return a provider-and-identifier demo record from Supabase.

        Returns:
            A record mapping with key fields for the integration layer, or
            None when a record is missing.

        Raises:
            DemoGovernmentRepositoryUnavailable: when the configured
                database session cannot connect or the table cannot be read.
        """
        provider_key = (provider or "").upper().strip()
        identifier_key = (identifier or "").strip()

        if not settings.database_url:
            raise DemoGovernmentRepositoryUnavailable("DATABASE_URL is not configured")

        if not provider_key or not identifier_key:
            return None

        session = self.session or SessionLocal()
        try:
            row = session.execute(
                text(
                    """
                    SELECT id, provider, identifier, status, name, data, created_at, updated_at
                    FROM demo_government_records
                    WHERE provider = :provider
                      AND identifier = :identifier
                    LIMIT 1
                    """
                ),
                {"provider": provider_key, "identifier": identifier_key},
            ).mappings().first()

            if row is None:
                return None

            payload = row["data"]
            if isinstance(payload, str):
                try:
                    import json
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            elif not isinstance(payload, Mapping):
                payload = dict(payload or {})

            return {
                "id": str(row["id"]),
                "provider": str(row["provider"]),
                "identifier": str(row["identifier"]),
                "status": str(row["status"]),
                "name": row["name"],
                "data": dict(payload),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        except SQLAlchemyError as exc:
            raise DemoGovernmentRepositoryUnavailable(f"Supabase database lookup failed: {exc}") from exc
        except Exception as exc:
            raise DemoGovernmentRepositoryUnavailable(f"Supabase database lookup failed: {exc}") from exc
        finally:
            if self.session is None:
                session.close()
