Yes — **now we switch from “building the skeleton” to “making the skeleton actually work.”** 🔥

Since your UI and files already exist but the data is static, **do NOT give the vibe coder a giant prompt like “make the whole application functional.”** That will cause it to modify everything and create conflicts.

We should do it **one task at a time**, in dependency order.

## The implementation sequence

We'll eventually go through roughly this order:

```text
TASK 01 → Audit existing code + identify static data
TASK 02 → Connect FastAPI ↔ Supabase
TASK 03 → Make backend CRUD for Tenders
TASK 04 → Connect Tenders frontend to API
TASK 05 → Make Bidders backend dynamic
TASK 06 → Connect Bidders frontend
TASK 07 → Make Tender Details dynamic
TASK 08 → Make Bidder Details dynamic
TASK 09 → Document upload/storage
TASK 10 → Verification job creation
TASK 11 → Verification status
TASK 12 → Demo OCR pipeline
TASK 13 → Demo AI extraction
TASK 14 → Government verification services
TASK 15 → Compliance/risk calculation
TASK 16 → Dynamic dashboard
TASK 17 → Audit trail
TASK 18 → Officer decision workflow
TASK 19 → Error/loading/empty states
TASK 20 → Full end-to-end testing
```

**We should start with Task 01.**

---

# TASK 01 — Audit the existing application

### Goal

Before changing anything, make the AI coder understand:

* which data is currently hardcoded
* which pages are static
* which APIs already exist
* which backend services already exist
* which Supabase tables already exist
* which frontend components need to be connected
* which files should NOT be modified

This is important because **you already have a structure**. We don't want the agent rebuilding it.

---

## Give your vibe coder this prompt

Copy this **exactly**:

```text
TASK 01 — EXISTING APPLICATION AUDIT

We already have the initial project structure implemented for the GeM Bid Compliance Verification Platform.

The frontend is React.
The backend is Python FastAPI.
The database is Supabase PostgreSQL.
The project already contains demo/static data and UI pages.

IMPORTANT:
Do NOT redesign the application.
Do NOT create a new architecture.
Do NOT rewrite existing files unnecessarily.
Do NOT install new dependencies unless absolutely required.
Do NOT modify frontend or backend implementation in this task.

This task is ONLY an audit.

OBJECTIVE:

Inspect the entire existing repository and determine exactly how the current application works and where static/demo data is being used.

You must inspect:

1. Frontend pages
2. Frontend components
3. Frontend API/client/service files
4. Frontend demo/static data files
5. Backend FastAPI routes
6. Backend services
7. Backend models/schemas
8. Backend database/repository layer
9. Supabase configuration
10. Supabase migrations/schema
11. Existing tests
12. Docker configuration

Identify every location where data is currently hardcoded or generated locally instead of coming from the backend/database.

For every page, determine:

- Page name
- React file
- Current data source
- Whether data is static or API-based
- API endpoint currently used, if any
- Backend endpoint that exists, if any
- Supabase table involved, if any
- What is missing to make it dynamic

Pages to specifically inspect:

- Dashboard
- Tenders
- Tender Details
- Bidders
- Bidder Details
- Documents
- Verification
- Audit
- Settings

Also inspect all existing demo data files such as:

- demoData.js
- mock data
- JSON files
- hardcoded arrays
- hardcoded statistics
- hardcoded dashboard numbers

BACKEND AUDIT:

List all existing FastAPI endpoints.

For each endpoint provide:

METHOD
PATH
FILE
PURPOSE
CURRENT DATA SOURCE
DATABASE CONNECTED? YES/NO
IMPLEMENTATION STATUS

DATABASE AUDIT:

Inspect the existing Supabase schema/migrations.

List:

- tables
- important columns
- primary keys
- foreign keys
- indexes
- relationships

Do NOT modify the database.

DO NOT modify any files.

DO NOT delete static/demo data.

DO NOT replace mock data yet.

OUTPUT:

Create ONLY one new file:

docs/dynamic-data-audit.md

The document must contain these sections:

# Dynamic Data Audit

## 1. Current Architecture

## 2. Frontend Pages

Create a table:

| Page | File | Current Data Source | API Connected | Backend Endpoint | Supabase Source | Status |

## 3. Static Data Locations

List every file containing hardcoded/demo data.

For each:

| File | Data | Used By | Replacement Needed |

## 4. Existing Backend APIs

| Method | Endpoint | File | Purpose | Database Connected | Status |

## 5. Supabase Schema

| Table | Important Columns | Relationships | Used By |

## 6. Missing Connections

Clearly identify:

Frontend → Backend missing connections

Backend → Supabase missing connections

Frontend → API service missing connections

## 7. Recommended Implementation Order

Give a dependency-aware order for converting the static application into a dynamic application.

## 8. Files That Should NOT Be Modified During Initial Integration

Identify core architecture files that should remain stable.

FINAL REQUIREMENT:

After creating docs/dynamic-data-audit.md, show me a concise summary of:

1. How many pages are currently static
2. How many backend APIs already exist
3. How many Supabase tables exist
4. Which page should be connected first
5. Which files should be modified in the next task

Do not implement any of the fixes in this task.
```

---

# What should happen after this?

The agent should come back with something like:

```text
Audit completed.

Static pages: 7
Existing API endpoints: 11
Supabase tables: 7

Most static page:
Dashboard

Recommended first dynamic page:
Tenders

Files to modify next:
backend/app/services/tender_service.py
backend/app/api/tenders.py
frontend/src/api/client.js
frontend/src/pages/Tenders.jsx
```

**Stop there. Don't let it continue implementing.**

Then send me the contents of:

```text
docs/dynamic-data-audit.md
```

or paste its output here.

---

## Why we're starting here

Because your current situation is:

```text
              CURRENT
                 │
       ┌─────────┴─────────┐
       ↓                   ↓
    React UI          FastAPI skeleton
       │                   │
       ↓                   ↓
  demoData.js         demo responses
       │                   │
       └─────────┬─────────┘
                 ↓
             Supabase
             (barely used)
```

We want to gradually reach:

```text
                 React
                   │
                   │ REST
                   ▼
                FastAPI
                   │
             Service Layer
                   │
             Repository
                   │
                   ▼
                Supabase
                   │
                   ▼
             Real application data
```

And **we will not remove the demo data immediately**. It can remain as fallback/test fixtures until the real path is proven.

### Our rule from now on

For every task I'll give you:

**1. Task number**
**2. Objective**
**3. Exact files allowed to change**
**4. Exact files NOT to touch**
**5. Exact vibe-coding prompt**
**6. How to manually test it**
**7. What success should look like**

That way you can give **one task → one coder → one branch → test → merge → next task**.

Send me the audit result after **TASK 01**, and I'll give you **TASK 02 — the first actual database/API connection**.
