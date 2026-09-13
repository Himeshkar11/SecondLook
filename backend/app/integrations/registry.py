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


class GovernmentProviderRegistry:
    """Centralized registry for statutory and demonstration government verification providers (Task 14)."""

    def __init__(self) -> None:
        pass

    def get(self, source: str) -> GovernmentProvider:
        """Resolve and instantiate the configured provider for a given source."""
        from app.config.settings import settings
        from app.integrations.blacklist import DemoBlacklistProvider
        from app.integrations.epfo import DemoEPFOProvider
        from app.integrations.esic import DemoESICProvider
        from app.integrations.gst import DemoGSTProvider, GSTProvider
        from app.integrations.make_in_india import DemoMakeInIndiaProvider
        from app.integrations.nsic import DemoNSICProvider
        from app.integrations.oem import DemoOEMProvider
        from app.integrations.pan import DemoPANProvider, PANProvider
        from app.integrations.startup_india import DemoStartupIndiaProvider
        from app.integrations.udyam import DemoUdyamProvider

        key = (source or "").strip().upper()

        if key == "GST":
            if (settings.gst_provider or "demo").lower() == "demo":
                return DemoGSTProvider()
            return GSTProvider()

        if key == "PAN":
            if (settings.pan_provider or "demo").lower() == "demo":
                return DemoPANProvider()
            return PANProvider()

        if key in ("UDYAM", "MSME"):
            return DemoUdyamProvider()

        if key == "EPFO":
            return DemoEPFOProvider()

        if key == "ESIC":
            return DemoESICProvider()

        if key in ("STARTUP_INDIA", "STARTUPINDIA", "DPIIT"):
            return DemoStartupIndiaProvider()

        if key == "NSIC":
            return DemoNSICProvider()

        if key in ("MAKE_IN_INDIA", "MAKEININDIA", "MII"):
            return DemoMakeInIndiaProvider()

        if key == "OEM":
            return DemoOEMProvider()

        if key in ("BLACKLIST", "BLACKLISTING", "DEBARMENT"):
            return DemoBlacklistProvider()

        raise ValueError(
            f"Unknown or unsupported government verification source: '{source}'. "
            f"Supported sources: {self.available()}"
        )

    @classmethod
    def list_providers(cls) -> list[str]:
        """Classmethod returning all supported statutory and registry sources."""
        return [
            "BLACKLIST",
            "EPFO",
            "ESIC",
            "GST",
            "MAKE_IN_INDIA",
            "NSIC",
            "OEM",
            "PAN",
            "STARTUP_INDIA",
            "UDYAM",
        ]

    def available(self) -> list[str]:
        """List all supported statutory and registry sources."""
        return self.list_providers()


government_provider_registry = GovernmentProviderRegistry()


def get_provider(source: str) -> GovernmentProvider:
    """Canonical factory helper for retrieving a statutory/registry provider (Task 14)."""
    return government_provider_registry.get(source)


def get_government_provider(source: str) -> GovernmentProvider:
    """Backward-compatible statutory provider helper from Task 10 (GST & PAN only)."""
    key = (source or "").strip().upper()
    if key not in ("GST", "PAN"):
        raise ValueError(
            f"Unsupported statutory verification source: '{source}'. "
            f"Task 10 statutory document verification only supports GST and PAN. "
            f"Use get_provider('{source}') for multi-source verification."
        )
    return get_provider(source)
