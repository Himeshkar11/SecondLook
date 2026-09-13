"""Demo Udyam integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real Udyam integration should be replaced by the
official Udyam/MSME registration verification path under government
credentialing and authorization. Official reference page:
https://udyamregistration.gov.in/
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


class UdyamIntegration(GovernmentIntegration):
    """Demo Udyam verification integration."""

    name = "UDYAM"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoUdyamProvider(GovernmentProvider):
    """Deterministic fictional demo provider for Udyam MSME verification (Task 14)."""

    source = "UDYAM"

    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "UDYAM-TN-00-0000001": {
            "udyam_number": "UDYAM-TN-00-0000001",
            "enterprise_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "enterprise_type": "Micro",
            "major_activity": "Services",
            "registration_date": "2024-04-12",
            "status": "ACTIVE",
            "state": "Tamil Nadu",
        },
    }

    NOT_FOUND_IDENTIFIER = "UDYAM-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "UDYAM-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="UDYAM_NUMBER",
            supported_fields=[
                "udyam_number",
                "enterprise_name",
                "enterprise_type",
                "major_activity",
                "registration_date",
                "status",
                "state",
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
                message="Udyam verification service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="Udyam verification provider returned an error.",
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
                message="Udyam registration found in demo government source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No Udyam record found for registration number {clean_id}.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
