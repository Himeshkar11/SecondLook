# TASK 07 — Document Management Foundation

Perfect. Assuming **TASK 06 passed**, we now have:

```text
Tenders          → Dynamic ✅
Tender Details   → Dynamic ✅
Bidders          → Dynamic ✅
Bidder Details   → Dynamic ✅
Supabase         → Connected ✅
```

Now we start the **actual compliance pipeline**.

But we're going to be disciplined:

> **TASK 07 does NOT do OCR, AI, verification, or compliance checking.**

It only establishes the document system.

The architecture will become:

```text
Bidder
   │
   ▼
Documents
   │
   ├── Metadata → Supabase PostgreSQL
   │
   └── Actual file → Supabase Storage
```

Then later:

```text
Supabase Storage
       ↓
     OCR
       ↓
Extracted Text
       ↓
      AI
```

---

# 🎯 TASK 07 Objective

A procurement officer should be able to open a bidder and see something like:

```text
┌────────────────────────────────────────────────────┐
│ Bidder Documents                                   │
│                                                    │
│ ABC Technologies Pvt Ltd                          │
│                                                    │
│ ┌────────────────────────────────────────────────┐ │
│ │ GST Certificate        PDF      VERIFIED       │ │
│ │ Uploaded: 11 Sep 2026                  View   │ │
│ ├────────────────────────────────────────────────┤ │
│ │ PAN Card               PDF      PENDING        │ │
│ │ Uploaded: 11 Sep 2026                  View   │ │
│ ├────────────────────────────────────────────────┤ │
│ │ Udyam Certificate      PDF      PENDING        │ │
│ │ Uploaded: 11 Sep 2026                  View   │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│              [ Upload Document ]                   │
└────────────────────────────────────────────────────┘
```

The data should actually come from Supabase.

---

# 🏗️ Architecture

We want to establish this:

```text
                    React
                      │
                      │ REST
                      ▼
                  FastAPI
                      │
                DocumentService
                 /           \
                /             \
               ▼               ▼
       Supabase DB       Supabase Storage
       metadata              files
```

For example:

### PostgreSQL

```text
documents

id
bidder_id
document_type
file_name
storage_path
mime_type
file_size
status
uploaded_at
```

### Supabase Storage

```text
documents/
    bidder-id/
        gst_certificate.pdf
        pan_card.pdf
        udyam_certificate.pdf
```

**The database stores metadata and the Storage bucket stores the actual file.**

---

# ⚠️ Important security decision

Do **not** make the document bucket publicly accessible just to make development easier.

These are bidder documents and may contain sensitive information.

Prefer:

```text
Private bucket
     ↓
Backend-authorized access
     ↓
Temporary/signed URL
```

We'll make the proper access controls stronger later.

---

# 📁 Files allowed to modify

Likely:

```text
backend/app/api/documents.py
backend/app/services/document_service.py
backend/app/models/document.py
backend/app/schemas/document.py
backend/app/database/repository.py

backend/tests/...

frontend/src/pages/Documents.jsx
frontend/src/services/documentService.js
frontend/src/api/client.js

frontend tests/...

supabase/
```

Use existing files if they already exist.

### Do NOT touch

```text
frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/BidderDetailPage.jsx
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Verification.jsx
frontend/src/pages/Audit.jsx

backend/app/ai/**
backend/app/ocr/**
backend/app/verification/**
backend/app/integrations/**
backend/app/workers/**
```

Do not modify unrelated modules.

---

# 📋 Vibe-coding prompt

Give the coder this exact prompt:

```text
TASK 07 — DOCUMENT MANAGEMENT FOUNDATION

TASK 06 has been completed successfully.

The application currently has:

- React frontend
- FastAPI backend
- Supabase PostgreSQL
- Dynamic Tenders
- Dynamic Tender Details
- Dynamic Bidders
- Dynamic Bidder Details
- Working REST API architecture
- Existing service/repository architecture

Now implement the DOCUMENT MANAGEMENT FOUNDATION.

IMPORTANT:

This task is ONLY for document metadata, file storage, upload, listing, and basic retrieval.

DO NOT implement:

- OCR
- AI extraction
- document verification
- compliance checking
- PAN verification
- GST verification
- Udyam verification
- risk scoring
- compliance scoring
- government integrations
- document parsing

Those belong to later tasks.

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

The target architecture is:

React
  ↓
Document API service
  ↓
FastAPI
  ↓
DocumentService
  ↓
Supabase
  ├── PostgreSQL → document metadata
  └── Storage → actual files

The React frontend MUST NOT directly interact with Supabase Storage.

All document operations must go through the backend API.

--------------------------------------------------
STEP 1 — INSPECT EXISTING DOCUMENT STRUCTURE
--------------------------------------------------

Before modifying anything inspect:

- existing Documents.jsx
- existing document components
- existing document model
- existing document schema
- existing document service
- existing database/repository layer
- existing Supabase schema
- existing Supabase Storage configuration
- existing bidder relationships
- existing API routing

Reuse existing architecture.

Do NOT create duplicate:

- document models
- document services
- repositories
- database clients
- API clients

--------------------------------------------------
STEP 2 — DATABASE DOCUMENT MODEL
--------------------------------------------------

Use the existing documents table if it already exists.

If a documents table exists:

DO NOT create another documents table.

Inspect its actual schema.

If the existing schema is incomplete for the required document functionality, make only the minimal necessary database/schema changes.

Document metadata should support at minimum:

- document ID
- bidder ID
- document type
- original filename
- storage path
- MIME type
- file size
- upload timestamp
- document status

Do not store the actual PDF/image binary inside PostgreSQL.

The actual file must be stored in Supabase Storage.

--------------------------------------------------
STEP 3 — DOCUMENT TYPES
--------------------------------------------------

Establish a controlled document type system.

Potential document types include:

PAN
GST
UDYAM
MCA
INCOME_TAX
EPFO
ESIC
STARTUP_INDIA
NSIC
OEM_AUTHORIZATION
MAKE_IN_INDIA
OTHER

Use the existing application's naming conventions if already defined.

Do not allow arbitrary uncontrolled document types if the architecture already supports enums/constants.

Do not implement verification logic for these types yet.

--------------------------------------------------
STEP 4 — SUPABASE STORAGE
--------------------------------------------------

Create/configure a PRIVATE Supabase Storage bucket for bidder documents.

Preferred bucket name:

bidder-documents

If a bucket already exists for this purpose, reuse it.

Do NOT create duplicate buckets.

Files should be organized logically.

Recommended structure:

bidder-documents/
    {bidder_id}/
        {document_id}_{filename}

Do not use user-controlled filenames as the only storage identifier.

Avoid path traversal/security issues.

--------------------------------------------------
STEP 5 — STORAGE SECURITY
--------------------------------------------------

The bucket should remain private.

Do NOT make bidder documents publicly accessible.

Do NOT expose Supabase service-role credentials to React.

The frontend must never receive:

- service-role key
- database password
- private Supabase credentials

If files need to be viewed/downloaded, the backend should provide an authorized temporary/signed access mechanism.

Keep the implementation simple for this task.

Advanced authorization policies can be improved later.

--------------------------------------------------
STEP 6 — DOCUMENT SERVICE
--------------------------------------------------

Implement the existing DocumentService.

It should support:

1. Upload document.
2. Save document metadata.
3. List documents for a bidder.
4. Retrieve document metadata.
5. Generate authorized access to a stored file if required.

Use:

API route
   ↓
DocumentService
   ↓
Repository / Supabase layer

Do not place all logic inside FastAPI routes.

--------------------------------------------------
STEP 7 — UPLOAD API
--------------------------------------------------

Implement an endpoint similar to:

POST /api/v1/bidders/{bidder_id}/documents

The endpoint should accept:

- document file
- document type

The exact request format should follow FastAPI best practices and the existing API architecture.

Validate:

- bidder exists
- supported document type
- file is present
- reasonable file size
- allowed MIME types/extensions

Initially support common document formats such as:

PDF
PNG
JPG/JPEG

Do not accept arbitrary executable or dangerous file types.

--------------------------------------------------
STEP 8 — FILE SIZE
--------------------------------------------------

Implement a reasonable configurable maximum upload size.

Do not hard-code the limit throughout the codebase.

Put it in configuration if the existing configuration architecture supports it.

For example:

MAX_DOCUMENT_SIZE_MB

Choose a reasonable development value.

The exact value can be changed later.

--------------------------------------------------
STEP 9 — STORAGE + DATABASE TRANSACTION FLOW
--------------------------------------------------

The upload flow should be:

1. Validate bidder.
2. Validate file.
3. Validate document type.
4. Generate safe storage path.
5. Upload file to Supabase Storage.
6. Create document metadata record in PostgreSQL.
7. Return document information.

If the database insert fails after the storage upload succeeds:

Attempt to clean up the uploaded storage object.

Avoid leaving orphaned files whenever reasonably possible.

If storage upload fails:

Do not create a successful document metadata record.

--------------------------------------------------
STEP 10 — DOCUMENT LIST API
--------------------------------------------------

Implement:

GET /api/v1/bidders/{bidder_id}/documents

It should return documents belonging to the specified bidder.

Example response:

{
  "items": [
    {
      "id": "...",
      "bidder_id": "...",
      "document_type": "GST",
      "file_name": "gst_certificate.pdf",
      "mime_type": "application/pdf",
      "file_size": 123456,
      "status": "PENDING",
      "uploaded_at": "..."
    }
  ],
  "total": 1
}

Do not blindly use this exact schema.

Adapt to the existing project conventions.

Do not return private storage credentials.

--------------------------------------------------
STEP 11 — DOCUMENT DETAIL API
--------------------------------------------------

Implement if appropriate:

GET /api/v1/documents/{document_id}

Return document metadata.

Do not return raw storage credentials.

If the existing architecture requires a separate endpoint to access/download the file, implement an authorized temporary/signed access mechanism.

--------------------------------------------------
STEP 12 — FRONTEND DOCUMENT SERVICE
--------------------------------------------------

Create or implement:

frontend/src/services/documentService.js

Use the existing API client.

The service should provide methods conceptually equivalent to:

getBidderDocuments(bidderId)

uploadDocument(bidderId, file, documentType)

getDocument(documentId)

Use the project's existing naming conventions.

Do not place raw API calls throughout Documents.jsx.

--------------------------------------------------
STEP 13 — FRONTEND DOCUMENT PAGE
--------------------------------------------------

Convert Documents.jsx from static/demo data to API-backed data.

The page should:

- load documents for the selected bidder
- display document name
- display document type
- display upload date
- display status
- provide upload functionality
- provide a way to view/access a document if supported

Do not implement document verification.

--------------------------------------------------
STEP 14 — UPLOAD UI
--------------------------------------------------

Create a simple government-portal-style upload interface.

The user should be able to select:

Document Type

and:

File

Then:

[ Upload Document ]

Keep the UI minimal.

Do NOT introduce:

- drag-and-drop animations
- flashy upload animations
- unnecessary visual effects

Follow the existing application's white/green/orange/blue design.

--------------------------------------------------
STEP 15 — UPLOAD FEEDBACK
--------------------------------------------------

During upload:

Show a loading/uploading state.

On success:

Show a simple success message and refresh the document list.

On failure:

Show a user-friendly error.

Do not expose backend stack traces or storage internals.

--------------------------------------------------
STEP 16 — EMPTY STATE
--------------------------------------------------

If the bidder has no documents:

Display:

"No documents uploaded."

Do not display demo documents.

--------------------------------------------------
STEP 17 — FILE ACCESS
--------------------------------------------------

If the user clicks "View" or "Download":

Use a secure backend-generated access mechanism.

Do NOT expose the bucket publicly.

Do NOT put a permanent public URL into the database if the bucket is private.

Prefer a short-lived signed URL or backend-controlled access.

--------------------------------------------------
STEP 18 — DEMO DATA
--------------------------------------------------

Do NOT globally delete demoData.js.

Other modules may still use it.

Only remove the Documents page's production dependency on static document data.

Do not fake uploaded documents after this task.

Documents displayed in the Documents page should come from the database.

--------------------------------------------------
STEP 19 — TESTING
--------------------------------------------------

Add backend tests for:

1. Valid document upload.
2. Invalid bidder ID.
3. Unsupported file type.
4. File size limit.
5. Invalid document type.
6. Document metadata creation.
7. Document listing.
8. Document retrieval.
9. Storage upload failure.
10. Database failure after storage upload.
11. Proper cleanup of storage object when metadata creation fails.

Mock Supabase Storage/database calls where appropriate.

Do not require live Supabase for every unit test.

--------------------------------------------------
STEP 20 — FRONTEND TESTING
--------------------------------------------------

If frontend testing is configured, test:

1. Loading documents.
2. Rendering document list.
3. Empty state.
4. Upload form.
5. Upload success.
6. Upload failure.

Do not rewrite unrelated tests.

--------------------------------------------------
STEP 21 — MANUAL TEST
--------------------------------------------------

Select an existing bidder.

Open:

Bidder → Documents

Upload:

GST Certificate
PDF

Verify:

1. File upload succeeds.
2. Document appears in UI.
3. Record appears in Supabase documents table.
4. Actual file appears in Supabase Storage.
5. File metadata is correct.

--------------------------------------------------
STEP 22 — CRITICAL STORAGE TEST
--------------------------------------------------

Open Supabase Storage.

Verify the actual PDF exists inside the private bucket.

Do NOT make the bucket public.

--------------------------------------------------
STEP 23 — DATABASE TEST
--------------------------------------------------

Open the documents table.

Verify:

- bidder_id is correct
- document_type is correct
- filename is correct
- storage_path exists
- MIME type is correct
- file size is correct
- upload timestamp exists

--------------------------------------------------
STEP 24 — FRONTEND REFRESH TEST
--------------------------------------------------

Upload a document.

Refresh the browser completely.

The document must still appear.

This proves:

React
 ↓
FastAPI
 ↓
Supabase DB

rather than local React state.

--------------------------------------------------
STEP 25 — FILE ACCESS TEST
--------------------------------------------------

Use the View/Download action.

Verify that the file can be accessed through the intended secure mechanism.

Verify that the Supabase bucket itself remains private.

--------------------------------------------------
STEP 26 — SECURITY TEST
--------------------------------------------------

Inspect the frontend source/configuration.

Confirm that no:

- service-role key
- database password
- private credential

is exposed to React.

Only public/client-safe configuration may exist on the frontend.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Only modify files directly related to document management.

Do NOT modify:

frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/BidderDetailPage.jsx
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Verification.jsx
frontend/src/pages/Audit.jsx

Do NOT modify:

backend/app/ai/**
backend/app/ocr/**
backend/app/verification/**
backend/app/integrations/**
backend/app/workers/**

Do NOT redesign the architecture.

Do not create duplicate:

- Supabase clients
- database clients
- API clients
- Document services
- Document models
- repositories

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

TASK 07 is complete only when:

[ ] Private Supabase Storage bucket exists
[ ] Document metadata is stored in Supabase PostgreSQL
[ ] Actual files are stored in Supabase Storage
[ ] DocumentService exists/works
[ ] Upload API works
[ ] Document list API works
[ ] Document retrieval works
[ ] Bidder validation works
[ ] Document type validation works
[ ] File type validation works
[ ] File size validation works
[ ] Storage/database failure handling works
[ ] Orphan storage cleanup is attempted when appropriate
[ ] React uses FastAPI for document operations
[ ] React does not directly access Supabase
[ ] Documents page uses real database data
[ ] Upload UI works
[ ] Loading state works
[ ] Empty state works
[ ] Error state works
[ ] File access works securely
[ ] Supabase bucket remains private
[ ] No secrets are exposed to frontend
[ ] Backend tests pass
[ ] Frontend tests pass if configured
[ ] Existing Tenders functionality still works
[ ] Existing Bidders functionality still works
[ ] Existing Tender Details functionality still works
[ ] Existing Bidder Details functionality still works
[ ] No unrelated modules are broken
[ ] No unrelated files were modified

STOP AFTER TASK 07.

Do NOT automatically implement TASK 08.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Supabase Storage bucket used.
3. Bucket privacy configuration.
4. Documents table used.
5. Upload API.
6. List API.
7. Document access mechanism.
8. Validation rules.
9. Maximum file size.
10. Storage/database failure handling.
11. Tests executed and results.
12. Manual tests performed.
13. Confirmation that the uploaded file exists in Storage.
14. Confirmation that metadata exists in PostgreSQL.
15. Confirmation that no secrets are exposed to frontend.
16. Any issues encountered.

STOP.
```

---

# 🧪 Your manual testing checklist

After the agent finishes, don't just trust the UI.

## Test 1 — Upload

Go:

```text
Bidders
  ↓
ABC Technologies
  ↓
Documents
```

Upload:

```text
Type: GST
File: gst_certificate.pdf
```

You should see the document appear.

---

## Test 2 — Supabase database

Go to:

```text
Supabase
 → Table Editor
 → documents
```

You should find something like:

```text
id              ...
bidder_id       ...
document_type   GST
file_name       gst_certificate.pdf
storage_path    ...
mime_type       application/pdf
file_size       ...
status          PENDING
uploaded_at     ...
```

---

## Test 3 — Supabase Storage

Go to:

```text
Supabase
 → Storage
 → bidder-documents
```

The actual file should exist.

This is important:

```text
PostgreSQL
    ↓
metadata

Storage
    ↓
actual PDF
```

---

## Test 4 — Refresh

Upload the document.

Then do:

```text
Ctrl + R
```

The document should still be there.

This confirms the UI isn't just maintaining local React state.

---

## Test 5 — Private bucket

Make sure:

```text
bidder-documents
```

is **not public**.

That's particularly important for this project because bidder documents may contain PAN, GST, financial and other sensitive information.

---

# 🚨 One thing I want you to watch carefully

The vibe coder might try to simplify this by doing:

```text
React
   ↓
Supabase Storage directly
```

**Don't accept that.**

Your architecture should remain:

```text
React
   ↓
FastAPI
   ↓
DocumentService
   ├── Supabase DB
   └── Supabase Storage
```

That keeps the backend in control of:

* authorization
* validation
* file naming
* document ownership
* audit logging
* future OCR
* future AI processing

---

# Where we are after TASK 07

The application now has a genuine document foundation:

```text
Tender
   │
   ▼
Bidder
   │
   ▼
Documents
   │
   ├───────────────┐
   ▼               ▼
PostgreSQL       Storage
metadata          PDF/Image
```

And **TASK 08** should be the next major step:

> **Document Processing Pipeline — uploaded file → processing job → OCR → extracted text storage.**

We still won't introduce the LLM immediately. First we'll make sure the application can reliably take an uploaded document and turn it into **clean extracted text**, which is exactly the foundation you identified earlier for reducing unnecessary AI token usage.
