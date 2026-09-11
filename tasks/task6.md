# TASK 06 — Make the Bidder Details Module Dynamic

Perfect. Assuming **TASK 05 passed exactly as expected**, we now have the first complete relationship:

```text
Supabase
   │
   ├── Tenders
   │      ↓
   │   Tender Details
   │      ↓
   │   Associated Bidders
   │
   └── Bidders
```

Now we make the **Bidder Details page** dynamic.

The target becomes:

```text
Bidders
   ↓
Click bidder
   ↓
/bidders/{bidder_id}
   ↓
GET /api/v1/bidders/{bidder_id}
   ↓
FastAPI
   ↓
BidderService
   ↓
Supabase
```

And the bidder detail page can show things such as:

```text
┌─────────────────────────────────────────────┐
│ Bidder Details                              │
│                                             │
│ ABC Technologies Pvt Ltd                   │
│ Bidder ID: BID-001                          │
│                                             │
│ Registration Information                    │
│ ─────────────────────────────────────────── │
│ PAN              •••••1234F                 │
│ GSTIN            29ABCDE1234F1Z5             │
│ Udyam Status     Registered                 │
│                                             │
│ Associated Tender                           │
│ CPCL Equipment Procurement 2026             │
│                                             │
│ Verification Status                         │
│ Pending                                      │
└─────────────────────────────────────────────┘
```

**Important:** We're only displaying the information that already exists. We're **not verifying PAN/GST/Udyam yet**.

---

# 🎯 TASK 06 Objective

Convert:

```text
BidderDetailPage.jsx
        ↓
demoData/static bidder
```

into:

```text
BidderDetailPage.jsx
        ↓
bidderService
        ↓
GET /api/v1/bidders/{bidder_id}
        ↓
BidderService
        ↓
Supabase
        ↓
real bidder
```

If your existing database relationships support it, also retrieve the bidder's associated tender.

---

# 📁 Files allowed to modify

Likely:

```text
backend/app/api/bidders.py
backend/app/services/bidder_service.py
backend/app/schemas/bidder.py
backend/app/database/repository.py

backend/tests/...

frontend/src/pages/BidderDetailPage.jsx
frontend/src/services/bidderService.js
frontend/src/api/client.js

frontend/tests/...
```

Use the **existing files discovered in the previous audit**.

### Do NOT modify

```text
frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/Dashboard.jsx
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

Don't create duplicate services.

---

# 📋 Vibe-coding prompt

```text
TASK 06 — MAKE THE BIDDER DETAILS MODULE DYNAMIC

TASK 05 has been completed successfully.

The application currently has:

- FastAPI connected to Supabase
- Dynamic Tenders API
- Dynamic Tenders page
- Dynamic Bidders API
- Dynamic Bidders page
- Dynamic Tender Details page
- Dynamic Tender → Bidders relationship

Now convert ONLY the Bidder Details page from static/demo data to real Supabase-backed data.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

When a user clicks a bidder, the Bidder Details page must retrieve the actual bidder record from Supabase through the FastAPI REST API.

Required architecture:

Bidders.jsx
    ↓
navigate to /bidders/{bidder_id}
    ↓
BidderDetailPage.jsx
    ↓
bidderService
    ↓
GET /api/v1/bidders/{bidder_id}
    ↓
FastAPI
    ↓
BidderService
    ↓
Repository/database layer
    ↓
Supabase
    ↓
bidders table

The frontend MUST NOT query Supabase directly.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- PAN verification
- GST verification
- Udyam verification
- MCA verification
- EPFO verification
- ESIC verification
- blacklist verification
- document verification
- OCR
- AI
- compliance scoring
- risk scoring
- government integrations
- bidder editing
- bidder deletion
- bidder creation

This task is ONLY about retrieving and displaying bidder details.

--------------------------------------------------
STEP 1 — INSPECT EXISTING IMPLEMENTATION
--------------------------------------------------

Before changing anything inspect:

- BidderDetailPage.jsx
- Bidders.jsx
- bidderService.js
- existing React Router configuration
- Bidder model
- Bidder schema
- BidderService
- repository/database layer
- bidders Supabase table
- tender/bidder relationship

Reuse existing architecture.

Do not create duplicate:

- Bidder models
- Bidder services
- repositories
- database clients
- API clients

--------------------------------------------------
STEP 2 — BIDDER ID FROM ROUTE
--------------------------------------------------

The bidder detail page must use the actual bidder ID from the URL.

Expected concept:

/bidders/{bidder_id}

For example:

/bidders/123

Do NOT identify a bidder using:

- array index
- hardcoded ID
- demoData lookup
- temporary frontend state

The ID in the URL must identify the database record.

Use the existing React Router architecture.

--------------------------------------------------
STEP 3 — BACKEND BIDDER DETAILS API
--------------------------------------------------

Implement:

GET /api/v1/bidders/{bidder_id}

The endpoint must retrieve the actual bidder from Supabase.

Use:

Route
 ↓
BidderService
 ↓
Repository
 ↓
Supabase

Do not place large database queries directly inside the route.

Return only fields needed by the existing Bidder Details UI.

Do not expose unnecessary database fields.

--------------------------------------------------
STEP 4 — 404 HANDLING
--------------------------------------------------

If the bidder does not exist:

Return HTTP 404.

Do not return demo data.

Do not silently fall back to demoData.

Frontend should display:

"Bidder not found."

Provide a navigation option back to Bidders if appropriate.

--------------------------------------------------
STEP 5 — ASSOCIATED TENDER
--------------------------------------------------

If the existing database schema supports bidder → tender relationships:

Retrieve the associated tender information.

Use the real database relationship.

Do NOT hardcode relationships.

Do NOT create a new relationship if one already exists.

If the database currently allows a bidder to participate in multiple tenders, handle the relationship according to the existing schema rather than assuming one tender.

If the schema does not currently support a relationship, do not redesign the database in this task. Report the limitation.

--------------------------------------------------
STEP 6 — FRONTEND SERVICE
--------------------------------------------------

Use the existing frontend API client.

Implement the appropriate method in bidderService.js.

Conceptually:

getBidder(bidderId)

If associated tender information requires a separate endpoint and the existing architecture supports it, implement the appropriate service method.

Do not place raw fetch/axios logic throughout BidderDetailPage.jsx.

--------------------------------------------------
STEP 7 — REMOVE STATIC DATA FROM PRODUCTION PATH
--------------------------------------------------

The Bidder Details page currently uses static/demo data.

Replace the production data source with API data.

Do NOT globally delete demoData.js.

Other pages may still depend on it.

Only remove Bidder Details' production dependency on demo data.

Demo fixtures can remain for testing.

--------------------------------------------------
STEP 8 — LOADING STATE
--------------------------------------------------

While bidder information is loading:

Show the existing loading state/component.

Keep it visually consistent with the application.

Do not introduce excessive animation.

--------------------------------------------------
STEP 9 — ERROR STATE
--------------------------------------------------

If the API request fails:

Display a user-friendly error.

Example:

"Unable to load bidder details. Please try again."

Do not expose:

- stack traces
- SQL errors
- database internals
- credentials
- API keys

--------------------------------------------------
STEP 10 — PRESERVE SENSITIVE DATA HANDLING
--------------------------------------------------

Do not unnecessarily display sensitive identifiers in full.

If the existing UI already masks sensitive information, preserve that behavior.

Do not expose:

- Supabase credentials
- API keys
- database credentials
- internal IDs that are not required by the UI

If PAN/GST information exists in the database, display it only according to the existing UI's intended masking/security approach.

Do not implement verification in this task.

--------------------------------------------------
STEP 11 — PRESERVE EXISTING UI
--------------------------------------------------

Do NOT redesign Bidder Details.

Preserve:

- cards
- tables
- badges
- buttons
- spacing
- typography
- theme
- light/dark mode
- government-portal styling
- green/orange/blue status colors

Only replace static data with API data.

--------------------------------------------------
STEP 12 — BACKEND TESTING
--------------------------------------------------

Add/update tests for:

1. Existing bidder returns successfully.
2. Invalid bidder ID returns 404.
3. Database failure is handled correctly.
4. Bidder fields map correctly.
5. Associated tender relationship works if supported.
6. Missing/empty relationship is handled correctly.

Use mocked database responses for unit tests where appropriate.

Do not require live Supabase for every unit test.

--------------------------------------------------
STEP 13 — FRONTEND TESTING
--------------------------------------------------

If frontend testing is already configured, test:

1. Loading state.
2. Successful bidder rendering.
3. 404/not-found state.
4. API error state.
5. Associated tender rendering if applicable.

Do not rewrite unrelated tests.

--------------------------------------------------
STEP 14 — MANUAL TEST
--------------------------------------------------

Use a real bidder record from Supabase.

From:

Bidders

click a bidder.

Verify:

1. URL contains actual bidder ID.
2. Bidder Details loads.
3. Data corresponds to Supabase.
4. No demo bidder is being used.

--------------------------------------------------
STEP 15 — CRITICAL DATABASE CHANGE TEST
--------------------------------------------------

Change a bidder's name directly in Supabase.

For example:

ABC Technologies Pvt Ltd

change to:

ABC Technologies Pvt Ltd — UPDATED

Refresh Bidder Details.

The updated name must appear.

This proves the page is using:

React
 ↓
FastAPI
 ↓
Supabase

rather than static demo data.

--------------------------------------------------
STEP 16 — DIRECT URL TEST
--------------------------------------------------

Copy the bidder details URL.

Open it directly in a new browser tab.

Example:

/bidders/123

The page must load the bidder from the URL ID.

It must not depend on previously visiting the Bidders page.

--------------------------------------------------
STEP 17 — INVALID ID TEST
--------------------------------------------------

Open a bidder URL using a nonexistent ID.

Example:

/bidders/nonexistent-id

The application must display a proper not-found state.

It must not crash.

It must not show fake data.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Only modify files directly required for Bidder Details.

Do NOT modify:

frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
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

TASK 06 is complete only when:

[ ] GET /api/v1/bidders/{id} exists
[ ] API retrieves real Supabase bidder data
[ ] BidderService is used
[ ] Existing repository architecture is preserved
[ ] Bidder Details gets ID from URL
[ ] React calls FastAPI
[ ] React does not query Supabase directly
[ ] Static bidder detail data is removed from production path
[ ] Loading state works
[ ] Error state works
[ ] 404 state works
[ ] Associated tender information works if supported
[ ] Sensitive information remains appropriately protected
[ ] Existing UI remains intact
[ ] Direct URL works
[ ] Database changes appear in frontend
[ ] Backend tests pass
[ ] Frontend tests pass if configured
[ ] Tenders page still works
[ ] Tender Details still works
[ ] Bidders page still works
[ ] No unrelated modules are broken
[ ] No unrelated files were modified

STOP AFTER TASK 06.

Do NOT automatically implement TASK 07.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Bidder detail API endpoint.
3. Supabase table used.
4. Database relationship used.
5. Frontend service method.
6. Static data removed from production path.
7. Tests executed and results.
8. Manual tests performed.
9. Direct URL test result.
10. 404 test result.
11. Any issues encountered.

STOP.
```

---

# 🧪 Manual testing

After the coder finishes:

### Test 1

Go to:

```text
Bidders
```

Click:

```text
ABC Technologies
```

You should get:

```text
/bidders/<actual-id>
```

---

### Test 2

Change the bidder directly in Supabase.

For example:

```text
ABC Technologies Pvt Ltd
```

→

```text
ABC Technologies Pvt Ltd — UPDATED
```

Refresh.

The updated value should appear.

---

### Test 3

Try:

```text
/bidders/fake-id-123
```

You should get:

```text
Bidder not found
```

—not a random demo bidder.

---

### Test 4

Open the bidder URL directly in a fresh tab.

It should work without first opening `/bidders`.

---

# 🧩 After TASK 06

At this point, your core navigation becomes genuinely database-driven:

```text
                 SUPABASE
                    │
          ┌─────────┴─────────┐
          │                   │
       Tenders             Bidders
          │                   │
          ▼                   ▼
   TenderService        BidderService
          │                   │
          └─────────┬─────────┘
                    │
                  FastAPI
                    │
              ┌─────┴─────┐
              │           │
          Tenders       Bidders
              │           │
              ▼           ▼
        TenderDetail   BidderDetail
              │           │
              └─────┬─────┘
                    │
             Database relationships
```

🔥 **This is the point where we can start the more important part of the project: documents.**

### TASK 07 will be:

**Document Management Foundation**

We'll establish:

```text
Bidder
   ↓
Documents
   ↓
Document metadata in Supabase
   ↓
Actual file in storage
```

and we'll use **Supabase Storage** for the uploaded PDF/document files rather than stuffing files into PostgreSQL. Then we'll build the upload flow before touching OCR or AI.
