# TASK 04 — Make the Bidders Module Dynamic

Excellent. Assuming **TASK 03 passed all tests**, we now have our first complete dynamic vertical slice:

```text
Supabase
   ↓
FastAPI
   ↓
TenderService
   ↓
REST API
   ↓
React Tenders
```

Now we repeat the same pattern for **Bidders**, while introducing one important relationship:

```text
Tender
   │
   └── Bidders
```

The goal is that the Bidders page no longer reads from `demoData.js`.

---

## 🎯 What TASK 04 should achieve

Currently:

```text
Bidders.jsx
     ↓
static demo bidders
```

After this task:

```text
Bidders.jsx
     ↓
bidderService.js
     ↓
GET /api/v1/bidders
     ↓
FastAPI
     ↓
BidderService
     ↓
Supabase
     ↓
bidders table
```

And eventually:

```text
Tender
  │
  ├── Bidder A
  ├── Bidder B
  ├── Bidder C
  └── Bidder D
```

For now, **we're only making the bidder listing dynamic**.

We are NOT implementing bidder verification yet.

---

# Files allowed to change

Depending on your existing repository:

```text
backend/app/api/bidders.py
backend/app/services/bidder_service.py
backend/app/models/bidder.py
backend/app/schemas/bidder.py
backend/app/database/repository.py

backend/tests/...

frontend/src/pages/Bidders.jsx
frontend/src/api/client.js
frontend/src/services/bidderService.js
frontend/src/data/demoData.js
frontend tests/...
```

If these files already exist, **modify them instead of creating duplicates**.

### Do NOT touch

```text
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
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

unless an existing architecture dependency absolutely requires a minimal change.

---

# 📋 Prompt for the vibe coder

Copy this as-is:

```text
TASK 04 — MAKE THE BIDDERS MODULE DYNAMIC

TASK 03 has been completed successfully.

The Tenders module is now connected:

React
  ↓
FastAPI
  ↓
TenderService
  ↓
Supabase

Now implement the same architecture for the Bidders module.

The existing Bidders page currently displays static/demo data.

Convert ONLY the Bidders module to use real data from the existing Supabase database through FastAPI REST APIs.

--------------------------------------------------
IMPORTANT ARCHITECTURE RULE
--------------------------------------------------

The frontend MUST NOT query Supabase directly.

The required flow is:

React Bidders page
        ↓
Frontend bidder service
        ↓
FastAPI REST API
        ↓
BidderService
        ↓
Repository/database layer
        ↓
Supabase PostgreSQL
        ↓
bidders table

Do not bypass the backend.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- bidder verification
- compliance checking
- PAN verification
- GST verification
- OCR
- AI
- risk scoring
- compliance scoring
- document processing
- bidder creation
- bidder editing
- bidder deletion
- government API integrations

Those will be implemented later.

This task is ONLY about dynamically displaying bidder data.

--------------------------------------------------
STEP 1 — INSPECT EXISTING CODE
--------------------------------------------------

Before making changes, inspect:

- current Bidders page
- bidder-related components
- bidder demo/static data
- existing Bidder model
- existing Bidder schema
- existing backend routes
- existing services
- existing database/repository layer
- existing Supabase bidders table
- existing relationships between bidders and tenders

Reuse the existing architecture.

Do NOT create duplicate:

- Bidder models
- Bidder services
- database clients
- API clients
- repositories

--------------------------------------------------
STEP 2 — INSPECT SUPABASE SCHEMA
--------------------------------------------------

Use the EXISTING bidders table.

Do NOT create another bidders table.

Inspect the actual columns.

Determine how bidders relate to tenders.

Possible relationship:

tender
  ↓
tender_id
  ↓
bidder

But do NOT assume the column name.

Use the actual existing schema.

If bidder records currently have a tender relationship, preserve it.

--------------------------------------------------
STEP 3 — BACKEND BIDDER SERVICE
--------------------------------------------------

Implement the existing BidderService.

It should retrieve bidder records from Supabase.

The service should:

- query the existing bidders table
- return structured bidder data
- support appropriate filtering if already supported by the architecture
- handle database errors safely
- avoid exposing database internals

Follow:

Route
  ↓
Service
  ↓
Repository
  ↓
Supabase

Do not place large database queries directly inside the FastAPI route.

--------------------------------------------------
STEP 4 — BIDDER API
--------------------------------------------------

Implement:

GET /api/v1/bidders

It should return real bidder records from Supabase.

Use the existing API versioning conventions.

Use a predictable response structure.

For example:

{
  "items": [
    {
      "id": "...",
      "name": "ABC Technologies Pvt Ltd",
      "tender_id": "...",
      "registration_status": "ACTIVE"
    }
  ],
  "total": 1
}

Do NOT blindly use this exact structure.

Adapt the response to the existing database schema and current frontend requirements.

Do not expose unnecessary database fields.

--------------------------------------------------
STEP 5 — OPTIONAL TENDER FILTER
--------------------------------------------------

If the existing database relationship supports it cleanly, implement:

GET /api/v1/bidders?tender_id={tender_id}

This should return only bidders associated with that tender.

Example:

GET /api/v1/bidders?tender_id=123

However, do not redesign the database to support this.

If the existing schema does not support this relationship yet, implement the basic bidder listing only and report it.

--------------------------------------------------
STEP 6 — FRONTEND BIDDER SERVICE
--------------------------------------------------

Use the existing frontend API client.

Create or implement:

frontend/src/services/bidderService.js

only if such a service does not already exist.

It should communicate with:

GET /api/v1/bidders

The Bidders page should call the service rather than directly using fetch/axios throughout the component.

Follow the same API architecture used by the Tenders module.

--------------------------------------------------
STEP 7 — REMOVE STATIC BIDDER DATA FROM PRODUCTION PATH
--------------------------------------------------

The Bidders page currently uses demo/static data.

Replace the production data source with the API response.

IMPORTANT:

Do NOT delete demoData.js globally.

Other pages may still depend on it.

Only remove the Bidders page's dependency on static bidder data.

Demo fixtures may remain for tests.

--------------------------------------------------
STEP 8 — LOADING STATE
--------------------------------------------------

While bidders are being retrieved:

Display the existing loading component/state.

Do not introduce excessive animation.

Keep the UI consistent with the existing minimal government portal design.

--------------------------------------------------
STEP 9 — EMPTY STATE
--------------------------------------------------

If the API returns zero bidders:

Display a clear empty state.

Example:

"No bidders found."

Do not show fake bidder records.

--------------------------------------------------
STEP 10 — ERROR STATE
--------------------------------------------------

If the API fails:

Display a user-friendly error.

Example:

"Unable to load bidders. Please try again."

Do not expose:

- stack traces
- database errors
- API credentials
- internal implementation details

Provide retry functionality if the existing UI supports it.

--------------------------------------------------
STEP 11 — PRESERVE THE EXISTING UI
--------------------------------------------------

Do NOT redesign the Bidders page.

Preserve:

- existing layout
- existing cards
- existing table
- existing buttons
- existing typography
- existing colors
- existing theme system

Only replace the source of the data.

Do not introduce unnecessary UI changes.

--------------------------------------------------
STEP 12 — TESTING
--------------------------------------------------

Add/update backend tests.

Test:

1. GET /api/v1/bidders succeeds.
2. Real bidder data is mapped correctly.
3. Empty bidder result works.
4. Database failure is handled safely.
5. Tender filtering works if implemented.

Use mocks for unit tests where appropriate.

Do not make the test suite dependent entirely on the live Supabase database.

If frontend testing is already configured, test:

1. Loading state.
2. Successful bidder rendering.
3. Empty state.
4. Error state.

Do not rewrite unrelated tests.

--------------------------------------------------
STEP 13 — MANUAL DATABASE TEST
--------------------------------------------------

Use the existing Supabase bidders table.

Ensure at least 3 fictional bidder records exist.

For example:

ABC Technologies Pvt Ltd
XYZ Infrastructure Ltd
DEF Engineering Services Ltd

Use fictional demo information.

If bidders are related to tenders, associate them with the existing demo tenders.

Do not create a new schema.

--------------------------------------------------
STEP 14 — MANUAL API TEST
--------------------------------------------------

Open FastAPI Swagger.

Test:

GET /api/v1/bidders

Confirm that the response contains the records actually stored in Supabase.

The endpoint must NOT return a hardcoded bidder array.

--------------------------------------------------
STEP 15 — MANUAL FRONTEND TEST
--------------------------------------------------

Open the Bidders page.

Verify that the bidders shown in React correspond to the records in Supabase.

Change one bidder's name in Supabase.

Refresh the Bidders page.

The updated name must appear.

This proves the frontend is using:

React
 ↓
FastAPI
 ↓
Supabase

rather than demo data.

--------------------------------------------------
STEP 16 — VERIFY TENDER RELATIONSHIP
--------------------------------------------------

If the existing schema supports bidder → tender relationships:

Open a tender and determine which bidders belong to it.

The relationship must come from the database.

Do not hardcode:

Tender A → Bidder A
Tender A → Bidder B

Use actual database relationships.

If the current Tender Details page is not yet dynamic, do NOT modify it in this task.

Only verify the backend relationship where possible.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Only modify files directly required for the Bidders module.

Do NOT modify:

frontend/src/pages/Tenders.jsx

unless a shared component absolutely requires a non-breaking change.

Do NOT modify:

frontend/src/pages/Dashboard.jsx
frontend/src/pages/Verification.jsx
frontend/src/pages/Documents.jsx
frontend/src/pages/Audit.jsx

Do NOT modify:

backend/app/integrations/**
backend/app/verification/**
backend/app/ai/**
backend/app/ocr/**
backend/app/workers/**

Do NOT modify Supabase migrations.

Do not create duplicate architecture.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

TASK 04 is complete only when:

[ ] GET /api/v1/bidders exists
[ ] API retrieves real Supabase bidder records
[ ] BidderService is used
[ ] Repository/database architecture is preserved
[ ] React uses the bidder API
[ ] React does not query Supabase directly
[ ] Static bidder data is no longer the production data source
[ ] Loading state works
[ ] Empty state works
[ ] Error state works
[ ] Existing Bidders UI is preserved
[ ] Bidder/tender relationship is preserved where supported
[ ] Backend tests pass
[ ] Frontend tests pass if configured
[ ] Existing Tenders functionality still works
[ ] Existing health endpoints still work
[ ] No unrelated modules are broken
[ ] No unrelated files were modified

STOP AFTER TASK 04.

Do NOT automatically implement TASK 05.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. API endpoint created/updated.
3. Supabase table used.
4. Number of bidder records tested.
5. Bidder/tender relationship implementation.
6. Frontend service used.
7. Static data removed from production path.
8. Tests executed and results.
9. Manual tests performed.
10. Any issues encountered.

STOP.
```

---

# 🧪 Manual testing checklist

After the agent finishes, do these tests.

### Test 1 — Supabase

Open:

```text
Supabase
 → Table Editor
 → bidders
```

Make sure you have at least:

```text
ABC Technologies
XYZ Infrastructure
DEF Engineering
```

---

### Test 2 — Backend

Open:

```text
/api/docs
```

Run:

```text
GET /api/v1/bidders
```

You should see the **actual Supabase records**.

---

### Test 3 — Frontend

Open:

```text
Bidders
```

Verify the same records appear.

---

### Test 4 — The critical test

Change:

```text
ABC Technologies Pvt Ltd
```

to:

```text
ABC Technologies Pvt Ltd — UPDATED
```

in Supabase.

Refresh the website.

You should now see:

> **ABC Technologies Pvt Ltd — UPDATED**

If yes → **dynamic bidder pipeline confirmed.** ✅

---

# One important thing we're establishing here

After M03 and M04, your architecture should now look like:

```text
                  SUPABASE
                     │
             ┌───────┴────────┐
             │                │
          tenders          bidders
             │                │
             ▼                ▼
        TenderService    BidderService
             │                │
             └───────┬────────┘
                     │
                  FastAPI
                     │
                  REST API
                     │
             ┌───────┴────────┐
             ▼                ▼
         Tenders.jsx      Bidders.jsx
```

That's a **very good point to be at**.

The next stage, **TASK 05**, should be slightly more interesting: we'll make **Tender Details dynamic**, meaning clicking a tender should fetch its actual data from Supabase and eventually show its associated bidders.
