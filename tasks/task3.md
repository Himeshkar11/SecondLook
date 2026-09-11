# TASK 03 — Make the Tenders Module Dynamic

Great. Assuming **TASK 02 passed completely**, we now have:

```text
React
   │
   ▼
FastAPI
   │
   ▼
Supabase
```

Now we're going to use that connection for the **first real feature: Tenders**.

The target is:

```text
Before

Tenders.jsx
    ↓
demoData.js
    ↓
static data


After

Tenders.jsx
    ↓
GET /api/v1/tenders
    ↓
Tender API
    ↓
TenderService
    ↓
Supabase
    ↓
tenders table
```

This is the first task where you'll actually see the website stop being purely static.

---

# 🎯 TASK 03 OBJECTIVE

Make the **Tenders page fully database-driven**.

It must:

* retrieve tenders from Supabase
* expose them through FastAPI
* display them in React
* support loading state
* support empty state
* support API error state
* preserve your existing UI
* preserve your existing architecture

### Do NOT implement yet:

* tender creation
* tender editing
* tender deletion
* bidder verification
* compliance calculation
* AI
* OCR
* government APIs

We're only doing:

> **Supabase → FastAPI → React → Tenders page**

---

# 📁 Files allowed to modify

The exact filenames should follow your existing audit from TASK 01.

Likely:

```text
backend/app/api/tenders.py
backend/app/services/tender_service.py
backend/app/models/tender.py
backend/app/schemas/tender.py
backend/app/database/repository.py
backend/tests/...

frontend/src/pages/Tenders.jsx
frontend/src/api/client.js
frontend/src/services/tenderService.js
frontend/src/data/demoData.js   ← only if necessary
```

If your project has different filenames, **use the existing files rather than creating duplicates.**

### Do NOT modify

```text
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/Verification.jsx
frontend/src/pages/Documents.jsx
frontend/src/pages/Audit.jsx

backend/app/integrations/**
backend/app/verification/**
backend/app/ai/**
backend/app/ocr/**
backend/app/workers/**
supabase/migrations/**
```

unless an absolutely minimal change is required by the existing architecture.

---

# 📋 GIVE THIS EXACT PROMPT TO THE VIBE CODER

```text id="9u1g9f"
TASK 03 — MAKE THE TENDERS MODULE DYNAMIC

TASK 02 has been completed successfully.

FastAPI is connected to the real Supabase PostgreSQL database.

The project already has:

- React frontend
- Python FastAPI backend
- Supabase PostgreSQL database
- existing API structure
- existing service structure
- existing Tender model/schema structure
- existing Tenders page
- existing demo/static data

The goal of this task is to convert ONLY the Tenders module from static/demo data to real Supabase-backed data.

DO NOT redesign the application.

DO NOT create a new architecture.

DO NOT rewrite unrelated files.

DO NOT implement bidders, documents, AI, OCR, verification, government integrations, or dashboard functionality.

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

The final flow must be:

React Tenders page
        ↓
Frontend API service
        ↓
GET /api/v1/tenders
        ↓
FastAPI route
        ↓
TenderService
        ↓
Database/repository layer
        ↓
Supabase PostgreSQL
        ↓
tenders table

The React page must NOT directly query Supabase.

--------------------------------------------------
STEP 1 — INSPECT EXISTING TENDER IMPLEMENTATION
--------------------------------------------------

Before changing anything:

Inspect:

- existing Tenders.jsx
- existing tender components
- existing demoData.js
- existing Tender model
- existing Tender schema
- existing backend router
- existing service layer
- existing database/repository layer
- existing Supabase tenders table

Reuse existing structures.

Do not create duplicate Tender models, services, repositories, or API clients.

--------------------------------------------------
STEP 2 — DATABASE MODEL
--------------------------------------------------

Use the EXISTING Supabase tenders table.

Do NOT create a new table.

Inspect its actual columns and map them correctly.

Do not assume column names.

The API should expose only fields required by the existing Tenders UI.

If the existing schema already contains more fields, do not unnecessarily expose all of them.

--------------------------------------------------
STEP 3 — BACKEND TENDER SERVICE
--------------------------------------------------

Implement the existing TenderService so that it retrieves tender records from Supabase.

The service should:

- query the existing tenders table
- return structured tender data
- handle database errors
- avoid leaking database internals
- follow the existing repository/service architecture

Do not put database queries directly inside the FastAPI route if the project already has a service/repository layer.

Use:

Route
  ↓
Service
  ↓
Repository/Database
```

not:

Route
↓
Direct database query

---

## STEP 4 — CREATE/IMPLEMENT TENDER API

Implement:

GET /api/v1/tenders

The endpoint should return real records from Supabase.

Use the existing API versioning/router conventions.

Expected response shape should be consistent and predictable.

For example:

{
"items": [
{
"id": "...",
"tender_id": "...",
"title": "...",
"organization": "...",
"status": "ACTIVE",
"submission_deadline": "...",
"bid_count": 12
}
],
"total": 1
}

However, DO NOT blindly use this exact schema.

Adapt it to the existing database schema and frontend requirements.

Do not break existing API conventions.

---

## STEP 5 — FRONTEND API SERVICE

Use the existing frontend API client.

If a tender service already exists, implement it.

If it does not exist and the existing architecture allows it, create:

frontend/src/services/tenderService.js

The service should call:

GET /api/v1/tenders

The Tenders page should communicate with the backend through this service.

Do NOT put fetch/axios logic directly throughout Tenders.jsx.

Use the existing API client abstraction.

---

## STEP 6 — REMOVE STATIC TENDER DISPLAY

The Tenders page currently uses static/demo data.

Replace the page's production data source with the API response.

IMPORTANT:

Do NOT delete demoData.js if other pages still use it.

Do NOT globally remove demoData.js.

Only remove the Tenders page's dependency on static tender data.

If demoData.js contains data used by other pages, leave those parts untouched.

---

## STEP 7 — LOADING STATE

When the Tenders page is waiting for the API:

Display the existing loading component if available.

If there is no loading component, use a simple consistent loading state.

Do not add excessive animations.

The UI should remain consistent with the existing minimal government portal design.

---

## STEP 8 — EMPTY STATE

If the API successfully returns zero tenders:

Show a proper empty state.

Example concept:

"No tenders found."

Do not display fake tender cards.

---

## STEP 9 — ERROR STATE

If the API request fails:

Show a clear error state.

Example:

"Unable to load tenders. Please try again."

Provide a retry action if the existing UI architecture supports it.

Do not expose:

* stack traces
* database errors
* credentials
* internal server information

---

## STEP 10 — PRESERVE UI

Keep the existing Tenders page visual design.

Do NOT:

* redesign cards
* change colors unnecessarily
* introduce animations
* add gradients
* add unrelated components
* change the navigation
* change the global theme

Only replace the data source.

The existing minimal government portal styling must remain intact.

---

## STEP 11 — TESTING

Add/update backend tests for:

1. GET /api/v1/tenders returns successful data.
2. GET /api/v1/tenders handles an empty database.
3. GET /api/v1/tenders handles database failure.
4. Response structure is valid.

Use mocked database responses for unit tests where appropriate.

Add frontend tests if the project already has a frontend testing setup.

At minimum test:

1. Loading state.
2. Successful tender rendering.
3. Empty state.
4. Error state.

Do not rewrite unrelated tests.

---

## STEP 12 — MANUAL TESTING

Verify the following manually.

TEST A — DATABASE DATA

Insert/use at least 2-3 tender records in the existing Supabase tenders table.

Do NOT create a new table.

Example conceptual data:

Tender 1:
CPCL Procurement Tender
Status: ACTIVE

Tender 2:
Equipment Supply Tender
Status: UNDER_REVIEW

Tender 3:
Maintenance Services Tender
Status: CLOSED

Use realistic but clearly fictional demo data.

---

TEST B — API

Open:

GET /api/v1/tenders

Verify that the response contains the records actually stored in Supabase.

The API must NOT return hardcoded arrays.

---

TEST C — FRONTEND

Open the Tenders page.

Verify that the same records appear in React.

---

TEST D — DATABASE CHANGE

Change one tender's title directly in Supabase.

Refresh the Tenders page.

The new title must appear.

This proves the frontend is actually reading from Supabase through FastAPI.

---

TEST E — EMPTY STATE

Temporarily use an empty dataset or appropriate test setup.

The UI should show the empty state.

No fake records should appear.

---

TEST F — ERROR STATE

Temporarily make the API unavailable.

The frontend should show the error state rather than crashing.

---

## FILES RESTRICTION

Only modify files directly required for the Tenders module.

DO NOT modify:

frontend/src/pages/Bidders.jsx
frontend/src/pages/Verification.jsx
frontend/src/pages/Documents.jsx
frontend/src/pages/Audit.jsx

DO NOT modify:

backend/app/integrations/**
backend/app/verification/**
backend/app/ai/**
backend/app/ocr/**
backend/app/workers/**

DO NOT create duplicate:

* API clients
* database clients
* Tender models
* Tender services
* repositories
* configuration files

---

## DEFINITION OF DONE

TASK 03 is complete only when:

[ ] GET /api/v1/tenders exists
[ ] Endpoint queries real Supabase data
[ ] No hardcoded tender array is returned by backend
[ ] TenderService is used
[ ] Existing database architecture is preserved
[ ] React calls the backend API
[ ] React does not directly query Supabase
[ ] Tenders page displays real database records
[ ] Loading state works
[ ] Empty state works
[ ] Error state works
[ ] Existing UI design is preserved
[ ] Backend tests pass
[ ] Frontend tests pass if configured
[ ] Existing /health endpoints still work
[ ] Existing functionality outside Tenders is not broken
[ ] No unrelated files were modified

STOP AFTER TASK 03.

Do not automatically implement TASK 04.

---

## FINAL REPORT

After completion, report:

1. Files modified.
2. GET /api/v1/tenders response example.
3. Supabase table used.
4. Number of database records tested.
5. Frontend API service used.
6. Whether static Tenders data was removed from the production path.
7. Tests executed and results.
8. Manual tests performed.
9. Any issues encountered.

STOP.

````

---

# 🧪 Your manual verification

After the coder finishes, **you should personally do this 5-minute test**.

### Test 1 — Supabase

Go into your Supabase table:

```text
tenders
````

Put 2–3 records there.

---

### Test 2 — API

Open FastAPI Swagger:

```text
/api/docs
```

Find:

```text
GET /api/v1/tenders
```

Execute it.

You should see your actual Supabase records.

---

### Test 3 — Change the database

This is the **most important test**.

Change:

```text
CPCL Procurement Tender
```

to:

```text
CPCL Procurement Tender — UPDATED
```

in Supabase.

Refresh React.

If you see:

```text
CPCL Procurement Tender — UPDATED
```

🎉 **you've successfully eliminated the static data path.**

---

# ⚠️ Don't worry if `demoData.js` still exists

This is intentional.

You might have:

```text
demoData.js
```

being used by:

```text
Dashboard
Bidders
Verification
Audit
```

We don't want the coder to delete the whole thing.

For now:

```text
Tenders
    ↓
REAL API

Everything else
    ↓
Demo data
```

That's perfectly fine.

We'll progressively replace those connections.

---

# The sequence from here

After TASK 03 succeeds:

```text
TASK 04
↓
Make Bidders dynamic

TASK 05
↓
Make Tender Details dynamic

TASK 06
↓
Make Bidder Details dynamic

TASK 07
↓
Document system

TASK 08
↓
Document upload/storage

TASK 09
↓
Verification job creation

...
```

We're deliberately going **one vertical slice at a time** rather than trying to connect the entire application simultaneously.

**Run TASK 03, verify that changing a Supabase tender changes the React UI, and then we can move to TASK 04.**
