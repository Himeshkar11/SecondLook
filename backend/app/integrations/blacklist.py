"""Demo Blacklist integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.
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


class BlacklistIntegration(GovernmentIntegration):
    """Demo blacklist verification integration."""

    name = "BLACKLIST"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


class DemoBlacklistProvider(GovernmentProvider):
    """Deterministic fictional demo provider for Debarment / Blacklist registry checks (Task 14)."""

    source = "BLACKLIST"

    NOT_FOUND_IDENTIFIER = "BLACKLIST-NOTFOUND-000001"
    UNAVAILABLE_IDENTIFIER = "BLACKLIST-UNAVAIL-000001"

    def __init__(self) -> None:
        self.capabilities = ProviderCapabilities(
            source=self.source,
            identifier_type="ENTITY_NAME",
            supported_fields=[
                "entity_name",
                "listed",
                "status",
                "checked_at",
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
                message="Blacklist registry service is temporarily unavailable.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if "ERROR" in clean_id:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="Blacklist registry provider returned an error.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        if clean_id == self.NOT_FOUND_IDENTIFIER:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.NOT_FOUND.value,
                identifier=clean_id,
                message=f"No registry entry found for identifier {clean_id}.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        # Negative blacklist outcome (Listed / Debarred entity)
        if "LISTED" in clean_id or "DEBARRED" in clean_id or (data and data.get("listed") is True):
            record = {
                "entity_name": clean_id,
                "listed": True,
                "status": "LISTED",
                "reason": "Debarred under demonstration order",
                "checked_at": now_iso,
            }
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.FOUND.value,
                identifier=clean_id,
                data=record,
                message="Entity is listed on the debarment registry.",
                provider="demo",
                is_demo=True,
                retrieved_at=now_iso,
            )

        # Standard clean outcome
        record = {
            "entity_name": clean_id,
            "listed": False,
            "status": "CLEAR",
            "checked_at": now_iso,
        }
        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.FOUND.value,
            identifier=clean_id,
            data=record,
            message="Entity is clear of any debarment / blacklist records.",
            provider="demo",
            is_demo=True,
            retrieved_at=now_iso,
        )
