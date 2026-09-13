"""Demo OEM integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real OEM verification should be routed to the
applicable original equipment manufacturer or public procurement
registry path only after registration and authorization are in place.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.integrations.base import (
    GovernmentIntegration,
    GovernmentProvider,
    GovernmentSourceStatus,
    GovernmentVerificationResponse,
    IntegrationRequest,
    IntegrationResponse,
    ProviderCapabilities,
)


class OEMIntegration(GovernmentIntegration):
    """Demo OEM verification integration."""

    name = "OEM"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoOEMProvider(GovernmentProvider):
    """Deterministic fictional demo provider for OEM authorization verification (Task 14)."""

    source = "OEM"

    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "OEM-DEMO-000001": {
            "authorization_id": "OEM-DEMO-000001",
            "oem_name": "ABC ORIGINAL EQUIPMENT MANUFACTURER",
            "authorized_bidder": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "product_category": "Industrial Equipment",
            "valid_until": "2027-12-31",
            "status": "VALID",
        },
    }

    NOT_FOUND_IDENTIFIER = "OEM-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "OEM-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="OEM_AUTHORIZATION",
            supported_fields=[
                "authorization_id",
                "oem_name",
                "authorized_bidder",
                "product_category",
                "valid_until",
                "status",
            ],
            is_demo=True,
            supports_lookup=True,
        )

    def verify(self, identifier: str, data: Optional[Dict[str, Any]] = None) -> GovernmentVerificationResponse:
        clean_id = (identifier or "").strip().upper()
        now_iso = datetime.now(timezone.utc).isoformat()

        if clean_id == self.UNAVAILABLE_IDENTIFIER or "UNAVAIL" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.UNAVAILABLE.value,
                identifier=clean_id,
                message="OEM authorization verification service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="OEM verification provider returned an error.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if clean_id in self.DEMO_RECORDS:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.FOUND.value,
                identifier=clean_id,
                data=dict(self.DEMO_RECORDS[clean_id]),
                message="OEM authorization details found in demo source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No OEM authorization record found for ID {clean_id}.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
