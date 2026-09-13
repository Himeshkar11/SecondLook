"""Registry for the exact M11 provider-agnostic demo integration lookup.

The registry is intentionally dependency-free and deterministic. It maps a
provider code string to an implementation object. The implementation is an
interface-only placeholder and never touches the network.
"""

from __future__ import annotations

from typing import Dict, Type

from app.integrations.base import GovernmentIntegration
from app.integrations.blacklist import BlacklistIntegration
from app.integrations.digilocker import DigiLockerIntegration
from app.integrations.epfo import EPFOIntegration
from app.integrations.esic import ESICIntegration
from app.integrations.gst import GSTIntegration
from app.integrations.mca import MCAIntegration
from app.integrations.nsic import NSICIntegration
from app.integrations.oem import OEMIntegration
from app.integrations.pan import PANIntegration
from app.integrations.startup_india import StartupIndiaIntegration
from app.integrations.udyam import UdyamIntegration


class IntegrationRegistry:
    """In-memory registry for the required M11 providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, Type[GovernmentIntegration]] = {
            PANIntegration.name: PANIntegration,
            GSTIntegration.name: GSTIntegration,
            UdyamIntegration.name: UdyamIntegration,
            MCAIntegration.name: MCAIntegration,
            EPFOIntegration.name: EPFOIntegration,
            ESICIntegration.name: ESICIntegration,
            StartupIndiaIntegration.name: StartupIndiaIntegration,
            NSICIntegration.name: NSICIntegration,
            DigiLockerIntegration.name: DigiLockerIntegration,
            BlacklistIntegration.name: BlacklistIntegration,
            OEMIntegration.name: OEMIntegration,
        }

    def get(self, provider: str) -> Type[GovernmentIntegration]:
        """Return an integration class for a provider token.

        Raises:
            KeyError: if the provider token has no registered demo class.
        """
        key = provider.upper()
        try:
            return self._providers[key]
        except KeyError as exc:
            raise KeyError(f"Unknown provider '{provider}'") from exc

    def available(self) -> list[str]:
        """Return all known provider tokens for documentation and tests."""
        return sorted(self._providers.keys())


registry = IntegrationRegistry()


def get_integration(provider: str) -> GovernmentIntegration:
    """Factory helper used by the service layer.

    Returns a new provider instance corresponding to the requested token.
    """
    provider_cls = registry.get(provider)
    return provider_cls()


def get_government_provider(source: str) -> GovernmentProvider:
    """Factory helper for statutory GovernmentProvider instances (Task 10).

    Supports:
        GST -> GSTProvider / DemoGSTProvider
        PAN -> PANProvider / DemoPANProvider
    """
    from app.config.settings import settings
    from app.integrations.gst import DemoGSTProvider, GSTProvider
    from app.integrations.pan import DemoPANProvider, PANProvider

    normalized = (source or "").strip().upper()
    if normalized == "GST":
        if (settings.gst_provider or "demo").lower() == "demo":
            return DemoGSTProvider()
        return GSTProvider()
    elif normalized == "PAN":
        if (settings.pan_provider or "demo").lower() == "demo":
            return DemoPANProvider()
        return PANProvider()
    else:
        raise ValueError(f"Unsupported statutory verification source: '{source}'. Only GST and PAN are supported in Task 10.")

