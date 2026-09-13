"""Demo PAN integration implementation.

The provider implementation is intentionally a thin repository-backed
contract wrapper. It reads demo government verification rows from the
Supabase `demo_government_records` table via the common repository helper.

Replacement guidance: real PAN verification should be routed to the
official Income Tax Department / UTIITSL service pathway only after
registration and authorization are in place. Official reference page:
https://www.incometax.gov.in/iec/foportal/
"""

from app.integrations.base import GovernmentIntegration, IntegrationRequest, IntegrationResponse


class PANIntegration(GovernmentIntegration):
    """Demo PAN verification integration."""

    name = "PAN"

    def verify(self, request: IntegrationRequest) -> IntegrationResponse:
        return self._fetch_from_demo_repo(request)


# ---------------------------------------------------------------------------
# Task 10: Statutory Government Verification Providers
# ---------------------------------------------------------------------------
from typing import Any, Dict, Optional
import httpx
from app.config.settings import settings
from app.integrations.base import (
    GovernmentProvider,
    GovernmentSourceStatus,
    GovernmentVerificationResponse,
)


class DemoPANProvider(GovernmentProvider):
    """Deterministic, fictional demo provider for PAN verification.

    Works entirely offline without external credentials.
    """

    source = "PAN"

    # Fictional PAN records strictly for testing/demo per Task 10 specification
    DEMO_RECORDS: Dict[str, Dict[str, Any]] = {
        "ABCDE1234F": {
            "pan": "ABCDE1234F",
            "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
            "status": "ACTIVE",
        },
    }

    # Deterministic NOT_FOUND identifier
    NOT_FOUND_IDENTIFIER = "ABCDE0000N"

    # Deterministic simulated error / unavailable identifier
    UNAVAILABLE_IDENTIFIER = "ERROR0000F"

    def verify(self, identifier: str, data: Optional[Dict[str, Any]] = None) -> GovernmentVerificationResponse:
        clean_id = (identifier or "").strip().upper()

        if clean_id == self.UNAVAILABLE_IDENTIFIER or clean_id.startswith("UNAVAIL"):
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.UNAVAILABLE.value,
                identifier=clean_id,
                message="PAN verification service is temporarily unavailable.",
            )

        if clean_id.startswith("ERROR"):
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.ERROR.value,
                identifier=clean_id,
                message="PAN verification provider returned an error.",
            )

        if clean_id in self.DEMO_RECORDS:
            record_data = dict(self.DEMO_RECORDS[clean_id])
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.FOUND.value,
                identifier=clean_id,
                data=record_data,
                message="PAN details found in demo government source.",
            )

        return GovernmentVerificationResponse(
            source=self.source,
            status=GovernmentSourceStatus.NOT_FOUND.value,
            identifier=clean_id,
            message=f"No PAN record found for PAN {clean_id}.",
        )


class PANProvider(GovernmentProvider):
    """Integration-ready statutory PAN provider.

    Delegates to configured official API if credentials are provided,
    or cleanly falls back to DemoPANProvider if in demo mode or unconfigured.
    """

    source = "PAN"

    def __init__(self, demo_provider: Optional[DemoPANProvider] = None) -> None:
        self.demo_provider = demo_provider or DemoPANProvider()

    def verify(self, identifier: str, data: Optional[Dict[str, Any]] = None) -> GovernmentVerificationResponse:
        provider_mode = (settings.pan_provider or "demo").lower().strip()
        api_url = settings.pan_api_url.strip()
        api_key = settings.pan_api_key.strip()

        if provider_mode == "demo" or not api_url:
            return self.demo_provider.verify(identifier, data)

        clean_id = (identifier or "").strip().upper()
        try:
            with httpx.Client(timeout=15.0) as client:
                headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
                resp = client.get(f"{api_url.rstrip('/')}/pan/{clean_id}", headers=headers)
                if resp.status_code == 200:
                    payload = resp.json()
                    return GovernmentVerificationResponse(
                        source=self.source,
                        status=GovernmentSourceStatus.FOUND.value,
                        identifier=clean_id,
                        data=payload.get("data", payload),
                        raw_response={"status_code": resp.status_code},
                    )
                elif resp.status_code == 404:
                    return GovernmentVerificationResponse(
                        source=self.source,
                        status=GovernmentSourceStatus.NOT_FOUND.value,
                        identifier=clean_id,
                    )
                else:
                    return GovernmentVerificationResponse(
                        source=self.source,
                        status=GovernmentSourceStatus.ERROR.value,
                        identifier=clean_id,
                        message=f"Official PAN API returned HTTP {resp.status_code}",
                    )
        except httpx.RequestError as exc:
            return GovernmentVerificationResponse(
                source=self.source,
                status=GovernmentSourceStatus.UNAVAILABLE.value,
                identifier=clean_id,
                message=f"Official PAN API unavailable: {exc}",
            )

