"""Bidder service demo operations.

The service is contract-only and returns deterministic demo payloads.
No FastAPI objects or database queries are used here.
"""

from typing import Any, Dict


class BidderService:
    """Demo-only bidder service for the REST API contract layer."""

    def list_bidders(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Return a deterministic paginated bidder list demo payload."""
        return {
            "items": [
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "legal_name": "Demo Bidder Pvt Ltd",
                    "registration_number": "DEMO-BIDDER-001",
                    "gst_number": "DEMO-GST-001",
                    "pan_number": "ABCDE1234F",
                    "status": "draft",
                    "created_at": "2026-09-11T00:00:00Z",
                    "updated_at": "2026-09-11T00:00:00Z",
                }
            ],
            "total": 1,
            "page": page,
            "page_size": page_size,
        }

    def get_bidder(self, bidder_id: str) -> Dict[str, Any] | None:
        """Return a deterministic bidder demo object for a known UUID."""
        if bidder_id == "00000000-0000-0000-0000-000000000002":
            return {
                "id": bidder_id,
                "legal_name": "Demo Bidder Pvt Ltd",
                "registration_number": "DEMO-BIDDER-001",
                "gst_number": "DEMO-GST-001",
                "pan_number": "ABCDE1234F",
                "status": "draft",
                "created_at": "2026-09-11T00:00:00Z",
                "updated_at": "2026-09-11T00:00:00Z",
            }
        return None
