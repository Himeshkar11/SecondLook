# SecondLook Architecture

This document records the intended architecture and ownership boundaries for the SecondLook repository foundation.

## Current architecture direction

```text
REST Route
    ↓
Service
    ↓
Repository
    ↓
Database
```

The architecture is intentionally layered. Routes are responsible only for HTTP concerns, services coordinate domain operations, repositories own database access, and the database layer owns persistence.

## Responsibility map

### API / Route

Responsible for:

- HTTP
- request parsing
- response formatting
- HTTP status codes
- dependency injection

Routes must not contain business logic or direct database queries.

### Service

Responsible for:

- domain operations
- business rules
- orchestration

M10 services provide deterministic demo behavior suitable for the contract boundary. They may be replaced by repository-backed services later without changing the public API contract.

### Repository

Responsible for:

- database access
- persistence
- queries

### Database

Responsible for:

- persistent data
- constraints
- relationships

## Ownership diagram

```text
┌──────────────────────┐
│      Frontend        │
│     frontend/        │
│ Frontend Developer   │
└──────────┬───────────┘
           │
           │ REST API
           ▼
┌──────────────────────┐
│       Backend        │
│    backend/app/      │
│  Backend Developer   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     Repository       │
│    Data Access       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       Supabase       │
│      supabase/       │
│   Database Owner     │
└──────────────────────┘
```

## Ownership boundaries

- Frontend developer owns the UI and frontend deliverables in `frontend/`.
- Backend developer owns API routes, services, and future business orchestration under `backend/app/`.
- Database owner owns migration and schema configuration under `supabase/`.
- The repository and data access boundary exists between the service layer and the Supabase PostgreSQL database.

The service ownership boundary for this milestone is:

```text
backend/app/api/      → API developers
backend/app/services/ → Backend/service developers
backend/app/database/ → Database/repository developers
backend/app/models/    → Database/domain model ownership
```

Front-end code must not directly access `Supabase PostgreSQL`. The correct data direction is:

```text
React
  ↓
FastAPI REST API
  ↓
Database
```

## Backend future responsibilities

The future backend is responsible for:

- AI/OCR interfaces
- Government integrations
- Verification pipeline
- Service orchestration

These areas are documented as future responsibilities and are not implemented in this milestone. They must remain behind interfaces and mock-first providers as required by the project architecture.

## Integration abstraction

External systems are reached through service and integration interfaces:

```text
Service
   ↓
IntegrationRegistry
   ↓
GovernmentIntegration.verify(request)
   ↓
Demo Provider / Future Provider
```

This keeps government and data-provider work separated from the core application flow. In this milestone, the registry points to provider demo classes that implement the same shared interface and never reach outside the application boundary. The M11 registry and contract stay intentionally provider-agnostic and documentation-backed, while the service route remains a public demo contract.

```text
REST Route
    ↓
VerificationService
    ↓
IntegrationRegistry
    ↓
PAN / GST / Udyam / MCA / EPFO / ESIC / Startup India / NSIC / DigiLocker / Blacklist / OEM
```

The known M11 providers remain demonstration-only: they return contract objects and follow the shared integration status vocabulary without performing real verification tasks.
