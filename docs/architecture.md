# SecondLook Architecture

This document records the intended architecture and ownership boundaries for the SecondLook repository foundation.

## Current architecture direction

```text
Frontend
   ↓
REST API
   ↓
FastAPI
   ↓
Service Layer
   ↓
Repository Layer
   ↓
Supabase PostgreSQL
```

### Ownership diagram

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
Integration Interface
   ↓
Real Provider / Mock Provider
```

This keeps government and data-provider work separated from the core application flow and remains a documentation-only architecture direction for M02.
