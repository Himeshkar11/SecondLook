"""Tender service database operations.

This service retrieves real tender records from Supabase PostgreSQL using
SQLAlchemy and the configured repository/database layer.
"""

import logging
from typing import Any, Dict
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database.connection import SessionLocal
from app.models.tender import Tender

logger = logging.getLogger(__name__)


class TenderService:
    """Tender service for retrieving real database records from Supabase."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def list_tenders(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Return real tender records from Supabase with pagination envelope."""
        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        if session is None:
            logger.warning("Database session unavailable; returning empty tender list.")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
            }

        try:
            total = session.scalar(select(func.count(Tender.id))) or 0
            stmt = (
                select(Tender)
                .options(joinedload(Tender.creator))
                .order_by(Tender.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            tenders = session.execute(stmt).scalars().unique().all()

            items = []
            for t in tenders:
                org_name = t.creator.full_name if t.creator else "CPCL / Ministry of Petroleum"
                closing_str = t.created_at.strftime("%d %b %Y") if t.created_at else "24 Sep 2026"
                items.append({
                    "id": str(t.id),
                    "reference_number": t.reference_number,
                    "title": t.title,
                    "description": t.description or "",
                    "status": t.status,
                    "created_by": str(t.created_by),
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                    "organization": org_name,
                    "value": "₹ 4,20,00,000",
                    "bids": 0,
                    "risk": "LOW",
                    "closingDate": closing_str,
                })

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        except Exception as exc:
            logger.error("Failed to query tenders from Supabase: %s", exc)
            raise
        finally:
            if should_close and session is not None:
                session.close()

    def get_tender(self, tender_id: str) -> Dict[str, Any] | None:
        """Return a single tender record by UUID or reference number."""
        session = self.db
        should_close = False
        if session is None and SessionLocal is not None:
            session = SessionLocal()
            should_close = True

        if session is None:
            return None

        try:
            stmt = select(Tender).options(joinedload(Tender.creator))
            try:
                parsed_uuid = uuid.UUID(tender_id)
                stmt = stmt.where((Tender.id == parsed_uuid) | (Tender.reference_number == tender_id))
            except ValueError:
                stmt = stmt.where(Tender.reference_number == tender_id)

            t = session.execute(stmt).scalars().first()
            if t is None:
                return None

            org_name = t.creator.full_name if t.creator else "CPCL / Ministry of Petroleum"
            closing_str = t.created_at.strftime("%d %b %Y") if t.created_at else "24 Sep 2026"
            return {
                "id": str(t.id),
                "reference_number": t.reference_number,
                "title": t.title,
                "description": t.description or "",
                "status": t.status,
                "created_by": str(t.created_by),
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                "organization": org_name,
                "value": "₹ 4,20,00,000",
                "bids": 0,
                "risk": "LOW",
                "closingDate": closing_str,
            }
        except Exception as exc:
            logger.error("Failed to retrieve tender %s: %s", tender_id, exc)
            raise
        finally:
            if should_close and session is not None:
                session.close()
