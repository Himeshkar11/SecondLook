"""Verification service demo operations.

This service intentionally never calls external government, OCR, AI, or
provider APIs. It returns deterministic placeholder job and result data.
The provider choice is resolved through the M11 integration registry and a
common GovernmentIntegration.verify(request) abstraction.
"""

from typing import Any, Dict, Optional

from app.integrations.base import IntegrationRequest
from app.integrations.registry import get_integration

DEFAULT_PROVIDER_IDENTIFIERS = {
    "PAN": "ABCDE1234F",
    "GST": "27ABCDE1234F1Z5",
    "UDYAM": "UDYAM-TEST-001",
    "MCA": "U12345",
    "DIGILOCKER": "DL-USER-001",
    "EPFO": "EPFO-123456",
    "ESIC": "ESIC-123456",
    "BLACKLIST": "BLACKLIST-CASE-0001",
}


class VerificationService:
    """Demo-only verification service for the REST API contract boundary."""

    def start_verification(self, bidder_id: str, document_id: str | None = None, verification_type: str = "vendor-gst", provider: str = "PAN") -> Dict[str, Any]:
        """Return a deterministic queued verification job shape.

        The provider token is looked up through the demo registry. The
        provider implementation is then asked to verify a contract-only
        IntegrationRequest object through the common interface.
        """
        if not bidder_id:
            raise ValueError("bidder_id is required")

        normalized_provider = provider.upper()
        provider_cls = get_integration(normalized_provider)
        default_identifier = DEFAULT_PROVIDER_IDENTIFIERS.get(normalized_provider, "")
        response = provider_cls.verify(
            IntegrationRequest(
                entity_type="bidder",
                entity_id=bidder_id,
                provider=normalized_provider,
                document_id=document_id,
                payload={
                    "verification_type": verification_type,
                    "identifier": default_identifier,
                },
            )
        )

        return {
            "id": "00000000-0000-0000-0000-000000000003",
            "bidder_id": bidder_id,
            "document_id": document_id,
            "verification_type": verification_type,
            "provider": response.provider,
            "status": "queued",
            "started_at": None,
            "completed_at": None,
            "created_at": "2026-09-11T00:00:00Z",
            "result": {
                "overall_status": "pending",
                "checks": [
                    {
                        "provider": response.provider,
                        "status": response.status,
                        "success": response.success,
                        "message": response.message,
                    }
                ],
            },
        }

    def get_verification(self, verification_id: str) -> Dict[str, Any] | None:
        """Return a deterministic job/result demo object for a known UUID."""
        if verification_id != "00000000-0000-0000-0000-000000000003":
            return None

        return {
            "id": verification_id,
            "bidder_id": "00000000-0000-0000-0000-000000000002",
            "document_id": "00000000-0000-0000-0000-000000000004",
            "verification_type": "vendor-gst",
            "provider": "PAN",
            "status": "queued",
            "started_at": None,
            "completed_at": None,
            "created_at": "2026-09-11T00:00:00Z",
            "result": {
                "overall_status": "pending",
                "checks": [],
            },
        }
