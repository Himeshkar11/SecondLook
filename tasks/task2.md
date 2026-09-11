Perfect. We can assume **TASK 01 passed** and move directly to the first real integration.

# TASK 02 — Connect FastAPI to Supabase

This is the foundation for everything dynamic.

Right now we want to establish:

```text
React
   ↓
FastAPI
   ↓
Supabase PostgreSQL
```

But **we are NOT connecting the Tenders page yet**.

First, prove that the backend can reliably communicate with Supabase.

---

## 🎯 Objective

Make FastAPI able to:

1. Load Supabase configuration from `.env`
2. Initialize the Supabase client/database connection
3. Query Supabase
4. Return a real database response through an API endpoint
5. Handle database errors properly
6. Keep the existing architecture intact

At the end, this should work:

```text
Browser
   ↓
GET /api/v1/health/database
   ↓
FastAPI
   ↓
Supabase
   ↓
real response
```

---

# Files the coder is allowed to modify

The coder should **only modify files related to backend configuration/database/health**.

Potentially:

```text
backend/app/config/settings.py
backend/app/database/connection.py
backend/app/api/router.py
backend/app/main.py
backend/requirements.txt
.env.example
```

If the existing audit shows different filenames, **use those existing files instead of creating duplicates**.

### Do NOT modify

```text
frontend/**
backend/app/services/**
backend/app/integrations/**
backend/app/verification/**
backend/app/ai/**
backend/app/ocr/**
backend/app/workers/**
supabase/migrations/**
```

And definitely:

```text
DO NOT redesign the project.
DO NOT create another database layer.
DO NOT create another Supabase client.
DO NOT create duplicate configuration files.
```

---

# 📋 Give the vibe coder this prompt

```text
TASK 02 — CONNECT FASTAPI TO SUPABASE

TASK 01 has already been completed successfully.

The repository has been audited and the existing architecture is already established.

The technology stack is:

Frontend:
React

Backend:
Python + FastAPI

Database:
Supabase PostgreSQL

The purpose of this task is ONLY to establish and verify the FastAPI → Supabase database connection.

DO NOT implement tender functionality yet.
DO NOT implement bidder functionality yet.
DO NOT modify the frontend.
DO NOT implement OCR.
DO NOT implement AI.
DO NOT implement government integrations.
DO NOT implement verification logic.

IMPORTANT:
Use the existing project architecture discovered during TASK 01.

Do not create duplicate files or duplicate services.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Make the FastAPI backend communicate with the existing Supabase project.

The connection must use environment variables.

The backend must be able to:

1. Load Supabase configuration.
2. Initialize the Supabase/database client.
3. Execute a simple read query against an existing Supabase table.
4. Return the result through a backend health endpoint.
5. Handle connection/query errors cleanly.
6. Avoid exposing secrets in API responses or logs.

--------------------------------------------------
STEP 1 — ENVIRONMENT CONFIGURATION
--------------------------------------------------

Inspect the existing configuration system first.

Use the existing settings/configuration mechanism if one already exists.

Required configuration should be represented through environment variables.

Do NOT hard-code:

- Supabase URL
- Supabase keys
- database passwords
- service-role keys
- API secrets

Update .env.example with placeholder variable names if necessary.

Do NOT commit or create a real .env file containing secrets.

--------------------------------------------------
STEP 2 — SUPABASE CONNECTION
--------------------------------------------------

Use the existing backend database architecture.

If backend/app/database/connection.py already exists, implement the connection there.

If another database connection mechanism already exists, improve that implementation instead of creating another one.

Create one reusable Supabase/database client.

The rest of the application should be able to import/use this client rather than creating a new client for every request.

--------------------------------------------------
STEP 3 — DATABASE HEALTH ENDPOINT
--------------------------------------------------

Create a backend endpoint:

GET /api/v1/health/database

The endpoint should perform a lightweight real query against Supabase.

Use an existing safe table from the current schema.

Do NOT modify the database schema.

The response should clearly indicate whether the database connection is working.

Example successful response:

{
  "status": "ok",
  "database": "connected"
}

If appropriate, include a minimal non-sensitive verification field such as:

{
  "status": "ok",
  "database": "connected",
  "query": "successful"
}

Do not return credentials, keys, tokens, or sensitive database information.

--------------------------------------------------
STEP 4 — ERROR HANDLING
--------------------------------------------------

If Supabase cannot be reached or the query fails, return an appropriate HTTP error response.

Do not expose internal stack traces or credentials.

Example:

{
  "status": "error",
  "database": "unavailable"
}

Use appropriate logging on the backend for debugging.

--------------------------------------------------
STEP 5 — PRESERVE EXISTING API STRUCTURE
--------------------------------------------------

Use the existing router structure.

If the project already has:

backend/app/api/router.py

register the database health endpoint there.

Do NOT create another main FastAPI application.

Do NOT create another router hierarchy unless the existing architecture requires it.

--------------------------------------------------
STEP 6 — TESTING
--------------------------------------------------

Add backend tests for the database connection/health functionality.

Tests should cover:

1. Successful database connection.
2. Successful database query.
3. Database/query failure handling.

Use mocking where appropriate so unit tests do not require a live Supabase connection.

If the project already has a testing structure, follow it.

Do not rewrite existing tests.

--------------------------------------------------
STEP 7 — VERIFY LOCALLY
--------------------------------------------------

Run the existing backend test suite.

Then start the backend.

Call:

GET /api/v1/health

and:

GET /api/v1/health/database

The database endpoint must actually communicate with the configured Supabase project.

Do not fake the response.

--------------------------------------------------
IMPORTANT RESTRICTIONS
--------------------------------------------------

DO NOT MODIFY:

frontend/**
backend/app/services/**
backend/app/integrations/**
backend/app/verification/**
backend/app/ai/**
backend/app/ocr/**
backend/app/workers/**
supabase/migrations/**

unless the existing architecture makes a minimal modification absolutely necessary.

DO NOT:

- create duplicate Supabase clients
- create duplicate settings files
- create a second database abstraction
- redesign the architecture
- add unrelated dependencies
- modify UI
- replace existing demo data
- implement tender APIs
- implement bidder APIs

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

This task is complete only when:

1. FastAPI starts successfully.
2. Existing /health endpoint still works.
3. FastAPI successfully connects to the real Supabase project.
4. /api/v1/health/database performs a real database query.
5. Database failure is handled safely.
6. Secrets are loaded through environment variables.
7. No secrets are committed.
8. Existing tests still pass.
9. New database connection tests pass.
10. No unrelated files were modified.

--------------------------------------------------
FINAL OUTPUT
--------------------------------------------------

After implementation, report:

1. Files modified.
2. Dependencies added, if any.
3. Supabase connection method used.
4. Table queried by the health check.
5. API endpoint created.
6. Test results.
7. Whether the live Supabase query succeeded.
8. Any issues encountered.

STOP after completing this task.

Do NOT continue to TASK 03 automatically.
```

---

# 🧪 Then manually test it

Once the coder says it is complete, **don't immediately move on**.

Run the backend and test:

### 1. Basic API

```text
GET /health
```

Expected:

```json
{
  "status": "ok"
}
```

### 2. Supabase

```text
GET /api/v1/health/database
```

Expected something equivalent to:

```json
{
  "status": "ok",
  "database": "connected"
}
```

The exact response can differ depending on the existing API conventions.

### 3. Supabase dashboard

Open your Supabase project and make sure the table being queried actually exists.

You want to prove:

```text
FastAPI
   │
   │ real query
   ▼
Supabase
   │
   ▼
real table
```

not:

```text
FastAPI
   │
   ▼
hardcoded {"database":"connected"}
```

That's an important distinction.

---

# 🔥 One thing to watch for

Because you're using Supabase, the coder may be tempted to use the **Supabase JavaScript client from React** directly.

Don't do that for this architecture.

Your intended flow is:

```text
React
  │
  │ REST API
  ▼
FastAPI
  │
  │ database/service layer
  ▼
Supabase
```

Keep the database access on the backend.

The frontend should eventually know things like:

```text
GET /api/v1/tenders
```

not:

```text
React → Supabase tables directly
```

This keeps your business logic, authorization, verification rules, and database access centralized.

---

## After TASK 02

Once this passes, **TASK 03 will be our first actual feature: Tenders.**

We'll convert:

```text
Tenders.jsx
      ↓
demoData.js
      ↓
static tender cards/table
```

into:

```text
Tenders.jsx
      ↓
GET /api/v1/tenders
      ↓
FastAPI
      ↓
TenderService
      ↓
Supabase
      ↓
real tender records
```

And we'll do that without touching the rest of the application.
