# Architecture Baseline, Ownership & Future Development Map

This document records the repository as it exists in the workspace at the current milestone. It is intentionally a documentation-only baseline and does not redefine the application architecture, API contract, nor database schema.

## 1. Architecture Baseline

The implemented and documented architecture remains:

```text
REST API
    ↓
VerificationService
    ↓
Government Integration Interface
    ↓
Demo Government Integration
    ↓
Repository / Data Access
    ↓
Supabase PostgreSQL
```

This is evidenced by the following workspace files:

- API route boundary: `backend/app/api/router.py`
- Verification orchestration boundary: `backend/app/services/verification_service.py`
- Provider-neutral integration abstraction: `backend/app/integrations/base.py`
- Provider registry: `backend/app/integrations/registry.py`
- Demo repository read-object: `backend/app/database/demo_government_repository.py`
- Supabase migration for source-of-truth demo data: `supabase/migrations/20260911_create_demo_government_data.sql`
- Supabase deterministic seed: `supabase/seed.sql`

The route layer keeps REST concerns in `router.py`. The service layer selects the provider through `get_integration(provider)` and passes an `IntegrationRequest` into the provider object. The provider object implements `GovernmentIntegration.verify(request)` and resolves the response through the common repository-backed helper `_fetch_from_demo_repo(request)` from the shared base class. The repository layer uses SQLAlchemy `SessionLocal()` and `text()` to inspect `demo_government_records` in Supabase/PostgreSQL.

## 2. Verified Layer Boundaries

### 2.1 REST API boundary

Defined in `backend/app/api/router.py` and `backend/app/main.py`.

Responsible layers:

- `GET /api/v1/tenders`
- `GET /api/v1/tenders/{id}`
- `GET /api/v1/bidders`
- `GET /api/v1/bidders/{id}`
- `POST /api/v1/documents/upload`
- `POST /api/v1/verification/start`
- `GET /api/v1/verification/{id}`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/audit/{id}`

These route functions remain a lawful public contract layer. They delegate to service classes and do not contain database or government integration queries.

### 2.2 Service boundary

Defined in `backend/app/services/verification_service.py`.

The service currently remains deliberately demo-friendly and contract-aligned. It uses:

- `VerificationService.start_verification(...)`
- `VerificationService.get_verification(...)`

The service obtains a provider class from `IntegrationRegistry.get(provider)` and performs a provider-neutral request by constructing an `IntegrationRequest`. It does not contain provider-specific switching logic in the route path or in the repository path.

### 2.3 Integration abstraction

Defined in `backend/app/integrations/base.py`.

The interface contract is:

```text
IntegrationRequest → GovernmentIntegration.verify(request) → IntegrationResponse
```

The shared response contract is provider-neutral and maps repository statuses through a common vocabulary:

- `VERIFIED`
- `NOT_VERIFIED`
- `NOT_FOUND`
- `PENDING`
- `UNAVAILABLE`
- `ERROR`
- `CLEAR`
- `BLACKLISTED`

The base response mapper deliberately recognizes `CLEAR` and `BLACKLISTED` rows from the repository record and injects a `listed` boolean into the common response data payload for deterministic provider-neutral behavior.

### 2.4 Provider registry and implemented provider wrappers

Defined in `backend/app/integrations/registry.py` and the provider modules in `backend/app/integrations/`.

Current registered provider wrappers:

- `PANIntegration`
- `GSTIntegration`
- `UdyamIntegration`
- `MCAIntegration`
- `EPFOIntegration`
- `ESICIntegration`
- `StartupIndiaIntegration`
- `NSICIntegration`
- `DigiLockerIntegration`
- `BlacklistIntegration`
- `OEMIntegration`

All provider wrappers are thin wrappers over the common `GovernmentIntegration._fetch_from_demo_repo(request)` path and therefore do not define provider-local hardcoded demos or offline JSON sources.

### 2.5 Repository and Supabase source-of-truth path

Defined in `backend/app/database/demo_government_repository.py`.

The repository is the single access object that reads provider records from the table:

```text
demo_government_records
```

The repository reads through SQLAlchemy `text()`:

```sql
SELECT id, provider, identifier, status, name, data, created_at, updated_at
FROM demo_government_records
WHERE provider = :provider
  AND identifier = :identifier
LIMIT 1
```

It maps the JSONB payload into a Python `dict`, and maps missing records to `None`, database failure to `DemoGovernmentRepositoryUnavailable`, while the base integration layer converts missing rows to `NOT_FOUND` and database failures to `UNAVAILABLE`.

The source table itself is created by:

```sql
supabase/migrations/20260911_create_demo_government_data.sql
```

The deterministic seed rows intended for demo verification are in:

```sql
supabase/seed.sql
```

These rows are intentionally written as the source of truth for provider demo data and do not rely on local JSON fixture files.

## 3. Ownership Map

The repository is organized by area so ownership stays explicit.

### 3.1 Frontend ownership

Source area:

- `frontend/`

Owns:

- React UI
- Vite-based frontend structure
- Client-facing contract usage

### 3.2 Backend ownership

Source area:

- `backend/app/`

Owns:

- FastAPI route wrappers
- Service orchestration
- Integration interface and registry
- Repository access object
- Domain model and response contract code

### 3.3 Database ownership

Source area:

- `supabase/`

Owns:

- PostgreSQL migration files
- `demo_government_records` table design
- `seed.sql` deterministic data
- public database documentation and schema records

### 3.4 Documentation ownership

Source area:

- `docs/`

Owns:

- architecture narrative
- API contract documentation
- contributor/developer standards
- this archival baseline document

## 4. Future Development Map

The current repository deliberately separates future provider expansion from the public API contract:

```text
REST Route
    ↓
VerificationService
    ↓
GovernmentIntegration.verify(IntegrationRequest)
    ↓
Registry -> provider-specific integration class
    ↓
Repository-backed provider source-of-truth record
```

Future real government providers should replace the demo repository-backed provider classes by implementing the same interface and then wiring a real data acquisition path. This is the explicit replacement point the code comments and base abstraction document.

The accepted future replacement strategy is:

1. Keep the route contract unchanged.
2. Keep the service contract unchanged.
3. Keep the service-to-provider registry abstraction unchanged.
4. Replace the provider implementation class behind the registry while preserving the `GovernmentIntegration` interface.
5. Replace the repository lookup backend with a real provider read path only after the integration is authorized and documented.

No real provider APIs are implemented in this workspace. The provider modules are demo-only demonstration wrappers that intentionally document the single official replacement focus in their docstrings.

## 5. Current Testing and Verification Evidence

The regression suite is in:

- `backend/tests/test_integrations.py`

It validates:

- Required provider registry tokens
- Common provider-neutral contract shape
- Repository-backed record mapping through `DemoGovernmentRepository`
- Integration status mapping for a request that should return `NOT_FOUND`
- Clear and blacklisted demo rows from the repository-backed source-of-truth table

The fresh evidence command used in the workspace is:

```sh
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

The workspace has previously verified a passing run with 22 passed and 1 warning. That evidence is retained as the test baseline for the current documentation-only milestone.

## 6. Design Constraints

This milestone does not create or modify any implementation architecture beyond the existing files. It documents:

- actual service → integration → repository → Supabase direction,
- current provider registry presence,
- live Supabase-backed source-of-truth row semantics,
- the decision not to store demo source-of-truth records in provider-local JSON or handwritten offline fixtures,
- the repository-backed demo data access path.

This note remains documentation-only and is a map of the way the workspace already behaves, rather than a request to introduce a new architecture.
