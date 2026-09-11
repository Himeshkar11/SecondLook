"""Tender service demo operations.

This service intentionally does not access the database.
It returns deterministic, contract-compatible demo data for the
M10 service layer boundary.
"""

from typing import Any, Dict, List


class TenderService:
    """Demo-only tender service for the REST API contract layer."""

    def list_tenders(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Return a deterministic pagination envelope with demo tenders."""
        return {
            "items": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "title": "Demo Government Procurement Tender",
                    "reference_number": "DEMO-TENDER-001",
                    "description": "Demo tender record for development",
                    "status": "draft",
                    "created_at": "2026-09-11T00:00:00Z",
                    "updated_at": "2026-09-11T00:00:00Z",
                }
            ],
            "total": 1,
            "page": page,
            "page_size": page_size,
        }

    def get_tender(self, tender_id: str) -> Dict[str, Any] | None:
        """Return a deterministic tender demo object for a known UUID.

        Unknown IDs return None as the service-level not-found behavior.
        """
        if tender_id == "00000000-0000-0000-0000-000000000001":
            return {
                "id": tender_id,
                "title": "Demo Government Procurement Tender",
                "reference_number": "DEMO-TENDER-001",
                "description": "Demo tender record for development",
                "status": "draft",
                "created_at": "2026-09-11T00:00:00Z",
                "updated_at": "2026-09-11T00:00:00Z",
            }
        return None
