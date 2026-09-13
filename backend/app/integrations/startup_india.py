"""Demo Startup India integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real Startup India verification should be routed to
DPIIT or an official registration/verification service path only after
registration and authorization are in place.
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


class StartupIndiaIntegration(GovernmentIntegration):
    """Demo Startup India verification integration."""

    name = "STARTUP_INDIA"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoStartupIndiaProvider(GovernmentProvider):
    """Deterministic fictional demo provider for Startup India / DPIIT verification (Task 14)."""

    source = "STARTUP_INDIA"

    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "DPIIT-DEMO-000001": {
            "recognition_number": "DPIIT-DEMO-000001",
            "entity_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "status": "ACTIVE",
            "recognition_date": "2024-04-12",
        },
    }

    NOT_FOUND_IDENTIFIER = "DPIIT-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "DPIIT-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="DPIIT_RECOGNITION",
            supported_fields=[
                "recognition_number",
                "entity_name",
                "status",
                "recognition_date",
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
                message="Startup India verification service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="Startup India verification provider returned an error.",
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
                message="Startup India recognition found in demo government source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No Startup India record found for recognition number {clean_id}.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
