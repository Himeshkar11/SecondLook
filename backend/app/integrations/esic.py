"""Demo ESIC integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real ESIC verification should be replaced by the
official ESIC / employer-portal integration path only after required
registration and authorization. Official reference page:
https://www.esic.gov.in/
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


class ESICIntegration(GovernmentIntegration):
    """Demo ESIC verification integration."""

    name = "ESIC"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoESICProvider(GovernmentProvider):
    """Deterministic fictional demo provider for ESIC statutory verification (Task 14)."""

    source = "ESIC"

    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "ESIC-DEMO-000001": {
            "registration_number": "ESIC-DEMO-000001",
            "establishment_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "status": "ACTIVE",
            "registration_date": "2024-01-01",
        },
    }

    NOT_FOUND_IDENTIFIER = "ESIC-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "ESIC-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="ESIC_REGISTRATION",
            supported_fields=[
                "registration_number",
                "establishment_name",
                "status",
                "registration_date",
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
                message="ESIC verification service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="ESIC verification provider returned an error.",
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
                message="ESIC registration details found in demo government source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No ESIC record found for registration number {clean_id}.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
