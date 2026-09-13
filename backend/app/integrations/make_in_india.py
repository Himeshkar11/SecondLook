"""Demo Make In India integration implementation.

Provides deterministic demonstration data for local content verification.
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


class MakeInIndiaIntegration(GovernmentIntegration):
    """Demo Make In India verification integration."""

    name = "MAKE_IN_INDIA"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoMakeInIndiaProvider(GovernmentProvider):
    """Deterministic fictional demo provider for Make In India content verification (Task 14)."""

    source = "MAKE_IN_INDIA"

    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "MII-DEMO-000001": {
            "certificate_number": "MII-DEMO-000001",
            "entity_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "local_content_percentage": 65,
            "product_category": "Industrial Equipment",
            "country_of_origin": "India",
            "status": "VALID",
        },
        "MII-LOW-000001": {
            "certificate_number": "MII-LOW-000001",
            "entity_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "local_content_percentage": 40,
            "product_category": "Industrial Equipment",
            "country_of_origin": "India",
            "status": "VALID",
        },
    }

    NOT_FOUND_IDENTIFIER = "MII-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "MII-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="MII_CERTIFICATE",
            supported_fields=[
                "certificate_number",
                "entity_name",
                "local_content_percentage",
                "product_category",
                "country_of_origin",
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
                message="Make In India verification service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="Make In India verification provider returned an error.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if clean_id in self.DEMO_RECORDS:
            record = dict(self.DEMO_RECORDS[clean_id])
            if data and "local_content_percentage" in data:
                record["local_content_percentage"] = data["local_content_percentage"]
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.FOUND.value,
                identifier=clean_id,
                data=record,
                message="Make in India certificate details found in demo source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if data and "local_content_percentage" in data:
            record_data = {
                "certificate_number": clean_id,
                "entity_name": data.get("entity_name", "ABC TECHNOLOGIES PRIVATE LIMITED"),
                "local_content_percentage": data.get("local_content_percentage", 65),
                "product_category": data.get("product_category", "Industrial Equipment"),
                "country_of_origin": "India",
                "status": "VALID",
            }
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.FOUND.value,
                identifier=clean_id,
                data=record_data,
                message="Make in India certificate details found in demo source.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No Make in India record found for certificate number {clean_id}.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
