# M11 Integration Framework

The integration framework introduces a provider-agnostic abstraction behind the service layer so that the verification service depends on a shared contract rather than a single provider implementation.

## Architecture

```text
REST Route
    ↓
VerificationService
    ↓
IntegrationRegistry
    ↓
GovernmentIntegration.verify(IntegrationRequest)
    ↓
Demo Provider (PAN / GST / Udyam / MCA / EPFO / ESIC / Startup India / NSIC / DigiLocker / Blacklist / OEM)
```

This structure is intentionally declaration-only for the demo milestone. It is designed to stay contract-first and to avoid any database CRUD, authentication, credential handling, storage, or real network verification behavior.

## Shared contract

The common abstraction lives in `backend/app/integrations/base.py`.

- `IntegrationRequest`
  - fields: `entity_type`, `entity_id`, `provider`, `document_id`, `payload`
  - no secret or credential data

- `IntegrationResponse`
  - fields: `success`, `status`, `provider`, `reference_id`, `data`, `message`

- `GovernmentIntegration`
  - required interface: `verify(request)`

- `IntegrationStatus`
  - values: `VERIFIED`, `NOT_VERIFIED`, `NOT_FOUND`, `PENDING`, `UNAVAILABLE`, `ERROR`

## Provider registry

The registry in `backend/app/integrations/registry.py` maps provider strings to demo provider classes.

Known demo providers:

- `PAN`
- `GST`
- `UDYAM`
- `MCA`
- `EPFO`
- `ESIC`
- `STARTUP_INDIA`
- `NSIC`
- `DIGILOCKER`
- `BLACKLIST`
- `OEM`

Unknown provider names fail with a deterministic `KeyError` message: `Unknown provider '...'`.

## Demo implementation notes

Each provider module is a thin class that implements `GovernmentIntegration.verify(request)` and returns a deterministic `IntegrationResponse` object. These providers do not make outgoing HTTP calls and do not read or store credentials.

## Usage pattern

The verification service uses the registry to discover a provider class and then sends a provider-neutral request object through the common verification interface.

This allows future providers to be swapped behind the same service contract without changing the route layer or the service call signature.
