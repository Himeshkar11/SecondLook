"""Demo NSIC integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real NSIC verification should be routed to the
official national small industries portal or applicable public registry
path only after registration and authorization are in place.
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


class NSICIntegration(GovernmentIntegration):
    """Demo NSIC verification integration."""

    name = "NSIC"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoNSICProvider(GovernmentProvider):
    """Deterministic fictional demo provider for NSIC certificate verification (Task 14)."""

    source = "NSIC"

    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "NSIC-DEMO-000001": {
            "certificate_number": "NSIC-DEMO-000001",
            "enterprise_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "status": "ACTIVE",
            "valid_until": "2027-04-12",
        },
    }

    NOT_FOUND_IDENTIFIER = "NSIC-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "NSIC-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="NSIC_CERTIFICATE",
            supported_fields=[
                "certificate_number",
                "enterprise_name",
                "status",
                "valid_until",
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
                message="NSIC verification service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="NSIC verification provider returned an error.",
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
                message="NSIC certification details found in demo government source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No NSIC record found for certificate number {clean_id}.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
