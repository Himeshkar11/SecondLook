# TASK 08 — Document Processing + OCR Pipeline

Perfect. Assuming **TASK 07 passed completely**, we now have:

```text
Tender                    ✅ Dynamic
Tender Details            ✅ Dynamic
Bidders                   ✅ Dynamic
Bidder Details            ✅ Dynamic
Document metadata         ✅ Supabase
Actual files              ✅ Supabase Storage
Document upload           ✅ Working
```

Now we build the next layer:

```text
Uploaded Document
       ↓
Processing Job
       ↓
OCR
       ↓
Extracted Text
       ↓
Stored in Database
```

### Very important

**TASK 08 does NOT use an LLM yet.**

We first need to reliably convert:

```text
GST_Certificate.pdf
```

into:

```text
GSTIN: 29ABCDE1234F1Z5
Legal Name: ABC Technologies Pvt Ltd
Date of Registration: ...
...
```

Then **TASK 09** can take that extracted text and send it to the AI extraction service.

This separation is important:

```text
                DOCUMENT PIPELINE

PDF/Image
   │
   ▼
Storage
   │
   ▼
OCR
   │
   ▼
Raw extracted text
   │
   ▼
Database
   │
   ▼
AI Extraction       ← TASK 09
   │
   ▼
Structured JSON
```

---

# 🎯 TASK 08 Objective

When a document is uploaded, the system should be capable of processing it asynchronously.

For example:

```text
Upload GST certificate
        ↓
Document stored
        ↓
Processing job created
        ↓
OCR worker
        ↓
Extract text
        ↓
Save extracted text
        ↓
Document status = OCR_COMPLETED
```

The UI should be able to show:

```text
GST Certificate

Status:
● OCR Processing

or

✓ OCR Completed
```

---

# 🏗️ Architecture

We're introducing the processing pipeline carefully:

```text
                 FastAPI
                    │
             Upload Document
                    │
                    ▼
            Supabase Storage
                    │
                    ▼
             Processing Job
                    │
                    ▼
                 Worker
                    │
                    ▼
              OCRProcessor
                    │
                    ▼
             Extracted Text
                    │
                    ▼
             Supabase DB
```

Eventually it becomes:

```text
Upload
  ↓
Storage
  ↓
Job
  ↓
OCR
  ↓
AI
  ↓
Verification
```

---

# 📁 Files allowed to modify

Likely:

```text
backend/app/ocr/processor.py
backend/app/workers/worker.py
backend/app/workers/jobs.py

backend/app/services/document_service.py
backend/app/models/document.py
backend/app/schemas/document.py
backend/app/database/repository.py

backend/app/api/documents.py

backend/tests/ocr/**
backend/tests/workers/**
backend/tests/...

frontend/src/pages/Documents.jsx
frontend/src/services/documentService.js
frontend/src/components/...
```

And, **only if required**, the database migration/seed files for OCR fields.

### Do NOT modify

```text
frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/BidderDetailPage.jsx
frontend/src/pages/Dashboard.jsx

backend/app/integrations/**
backend/app/verification/**
backend/app/ai/**
```

Especially:

```text
backend/app/ai/**
```

We don't want the AI extraction implementation creeping into this task.

---

# 📋 Exact vibe-coding prompt

```text id="fkw9br"
TASK 08 — DOCUMENT PROCESSING AND OCR PIPELINE

TASK 07 has been completed successfully.

The application currently has:

- React frontend
- FastAPI backend
- Supabase PostgreSQL
- Supabase private Storage
- Dynamic Tenders
- Dynamic Tender Details
- Dynamic Bidders
- Dynamic Bidder Details
- Working document upload
- Document metadata stored in PostgreSQL
- Actual document files stored in Supabase Storage

Now implement the DOCUMENT PROCESSING + OCR PIPELINE.

--------------------------------------------------
VERY IMPORTANT
--------------------------------------------------

THIS TASK DOES NOT IMPLEMENT AI.

DO NOT call an LLM.

DO NOT implement:

- AI extraction
- LLM prompts
- structured AI JSON extraction
- compliance rules
- compliance scoring
- risk scoring
- PAN verification
- GST verification
- Udyam verification
- government integrations

Those belong to later tasks.

The ONLY goal is:

Document
   ↓
Processing Job
   ↓
OCR
   ↓
Extracted Text
   ↓
Database

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

The target architecture is:

React
   ↓
FastAPI
   ↓
DocumentService
   ↓
Processing Job
   ↓
Worker
   ↓
OCRProcessor
   ↓
Extracted Text
   ↓
Supabase PostgreSQL

The original document remains in:

Supabase Storage

The OCR output is stored separately in:

Supabase PostgreSQL

--------------------------------------------------
STEP 1 — INSPECT EXISTING OCR STRUCTURE
--------------------------------------------------

Before modifying anything inspect:

- backend/app/ocr/
- backend/app/workers/
- document service
- document model
- document schema
- documents API
- Supabase documents table
- existing job/processing structures
- existing tests
- Docker configuration

Reuse existing architecture.

Do not create duplicate:

- OCR processors
- workers
- job systems
- document services
- database clients

--------------------------------------------------
STEP 2 — DOCUMENT PROCESSING STATUS
--------------------------------------------------

Establish a controlled document processing status system.

Possible states:

UPLOADED
QUEUED
OCR_PROCESSING
OCR_COMPLETED
OCR_FAILED

Use the existing project's naming conventions if already established.

Do not add AI status values yet.

Do not add verification status values yet unless they already exist.

--------------------------------------------------
STEP 3 — OCR DATA STORAGE
--------------------------------------------------

The system needs to store OCR results.

Use the existing documents table if it already has suitable fields.

If necessary, minimally extend the database schema with fields such as:

ocr_status
ocr_text
ocr_error
ocr_completed_at

Do not create a separate OCR table unless the existing architecture genuinely requires it.

The raw OCR text must be stored separately from the original file.

The original PDF/image remains in Supabase Storage.

--------------------------------------------------
STEP 4 — OCR PROCESSOR INTERFACE
--------------------------------------------------

Implement the existing:

backend/app/ocr/processor.py

as an abstraction.

Conceptually:

OCRProcessor
    ↓
process(file)
    ↓
ExtractedText

The processor should have a clear interface so that different OCR implementations can later be plugged in.

For example:

DemoOCRProcessor
TesseractOCRProcessor
CloudOCRProcessor

Do not lock the rest of the application to one OCR vendor.

--------------------------------------------------
STEP 5 — INITIAL OCR IMPLEMENTATION
--------------------------------------------------

Implement a working OCR provider suitable for development.

If the project already specifies an OCR library, use it.

Otherwise use a reasonable local OCR implementation for development.

The implementation must support:

- PDF documents
- image documents

If PDF pages need to be converted to images before OCR, handle that inside the OCR layer.

Do not put OCR implementation inside:

- API routes
- React
- DocumentService

Keep OCR logic inside:

backend/app/ocr/

--------------------------------------------------
STEP 6 — DEMO FALLBACK
--------------------------------------------------

The system should retain a deterministic demo OCR implementation for testing.

For example:

DemoOCRProcessor

can return predefined text for known test fixtures.

This is useful for:

- automated tests
- CI
- development without OCR dependencies
- deterministic testing

Do not use demo OCR as the production OCR result when a real OCR provider is configured.

--------------------------------------------------
STEP 7 — PROCESSING JOB
--------------------------------------------------

After successful document upload:

Create an OCR processing job.

The preferred flow is:

Upload
 ↓
Save document
 ↓
Set status = QUEUED
 ↓
Create processing job
 ↓
Worker processes job

Do not make the upload HTTP request perform a long OCR operation synchronously.

--------------------------------------------------
STEP 8 — WORKER
--------------------------------------------------

Use the existing:

backend/app/workers/

architecture.

The worker should:

1. Retrieve queued OCR job.
2. Mark job as OCR_PROCESSING.
3. Retrieve the document from Supabase Storage.
4. Pass it to OCRProcessor.
5. Receive extracted text.
6. Save OCR text to PostgreSQL.
7. Mark document/job as OCR_COMPLETED.

If OCR fails:

1. Store a safe error state.
2. Mark status = OCR_FAILED.
3. Preserve the original document.
4. Do not delete the original uploaded file.

--------------------------------------------------
STEP 9 — JOB IDEMPOTENCY
--------------------------------------------------

Avoid accidentally processing the same document multiple times simultaneously.

Before processing:

Check the current processing status.

Do not start another OCR job if the document is already:

OCR_PROCESSING

or:

OCR_COMPLETED

unless an explicit retry operation exists.

--------------------------------------------------
STEP 10 — RETRY
--------------------------------------------------

Implement basic retry capability if the existing job architecture supports it.

A failed OCR job should be retryable.

Do not create infinite automatic retries.

Use a reasonable retry limit if retries are implemented.

For example:

MAX_OCR_RETRIES

must be configurable.

--------------------------------------------------
STEP 11 — OCR TEXT QUALITY
--------------------------------------------------

Store the raw OCR output.

Do NOT attempt to make the OCR text into JSON.

Do NOT normalize it with an LLM.

Do NOT extract GSTIN/PAN/etc. in this task.

The output should simply be text.

Example:

GSTIN: 29ABCDE1234F1Z5

Legal Name: ABC Technologies Pvt Ltd

Date of Registration: 12/04/2024

Address:
Chennai, Tamil Nadu

This raw text will be processed by the AI extraction layer in TASK 09.

--------------------------------------------------
STEP 12 — API FOR OCR STATUS
--------------------------------------------------

Expose document processing information through the backend.

The existing document API may be extended or a dedicated endpoint can be used.

For example:

GET /api/v1/documents/{document_id}

should expose safe processing information such as:

{
  "id": "...",
  "status": "OCR_COMPLETED",
  "ocr_status": "COMPLETED"
}

If appropriate, provide:

GET /api/v1/documents/{document_id}/ocr

which can return OCR status and extracted text to authorized users.

Follow the existing API architecture.

Do not expose internal worker details.

--------------------------------------------------
STEP 13 — FRONTEND DOCUMENT STATUS
--------------------------------------------------

Update Documents.jsx so that the UI reflects OCR processing status.

Example:

UPLOADED
QUEUED
OCR PROCESSING
OCR COMPLETED
OCR FAILED

Use the existing badge/status components.

Do not redesign the page.

Do not add flashy animations.

Use the existing government-portal design.

--------------------------------------------------
STEP 14 — OCR TEXT VIEW
--------------------------------------------------

If appropriate for the existing Documents page, provide an action:

"View Extracted Text"

When selected, display the raw OCR text.

This is useful for debugging and for demonstrating the project's document intelligence pipeline.

Do not transform the text into structured JSON yet.

--------------------------------------------------
STEP 15 — POLLING / STATUS REFRESH
--------------------------------------------------

Because OCR may be asynchronous, the frontend needs a way to observe status changes.

Use the simplest approach compatible with the existing architecture.

Polling is acceptable for this stage.

For example:

GET /api/v1/documents/{id}

every few seconds while status is:

QUEUED
or
OCR_PROCESSING

Stop polling when:

OCR_COMPLETED
or
OCR_FAILED

Do not create WebSockets unless the existing architecture already uses them.

--------------------------------------------------
STEP 16 — PRESERVE ORIGINAL FILE
--------------------------------------------------

Never replace the original uploaded file with OCR output.

Storage:

original PDF/image

Database:

OCR text

The two must remain separate.

--------------------------------------------------
STEP 17 — SECURITY
--------------------------------------------------

OCR text may contain sensitive bidder information.

Do not expose OCR text through unauthenticated endpoints.

Use the existing authorization architecture.

Do not expose:

- Supabase service-role keys
- database credentials
- storage credentials
- internal worker information

Do not make the storage bucket public.

--------------------------------------------------
STEP 18 — TESTING
--------------------------------------------------

Add backend tests for:

1. OCRProcessor interface.
2. Demo OCR processor.
3. Valid document processing.
4. OCR status transitions.
5. Successful OCR result storage.
6. OCR failure handling.
7. Duplicate processing prevention.
8. Missing document handling.
9. Storage retrieval failure.
10. Retry behavior if implemented.
11. OCR API/status endpoint.

Mock Supabase Storage and database interactions where appropriate.

Do not require real OCR for every unit test.

--------------------------------------------------
STEP 19 — OCR FIXTURE TEST
--------------------------------------------------

Create or use a safe test fixture.

Example:

backend/tests/fixtures/documents/sample_gst.pdf

The fixture should contain clearly fictional data.

Use it to test the OCR pipeline.

If creating binary fixtures is impractical, use the deterministic DemoOCRProcessor for automated tests and a manually supplied PDF for local OCR testing.

Do not use real people's documents.

--------------------------------------------------
STEP 20 — MANUAL TEST
--------------------------------------------------

Use the existing Documents page.

Select a bidder.

Upload a fictional PDF containing text such as:

GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5

LEGAL NAME: ABC TECHNOLOGIES PRIVATE LIMITED

REGISTRATION DATE: 12/04/2024

Then observe:

UPLOAD
 ↓
QUEUED
 ↓
OCR PROCESSING
 ↓
OCR COMPLETED

The original file must remain in Supabase Storage.

The extracted OCR text must be stored in Supabase PostgreSQL.

--------------------------------------------------
STEP 21 — DATABASE TEST
--------------------------------------------------

Open the documents table.

Verify:

- document exists
- OCR status is recorded
- OCR text is present after completion
- completion timestamp exists
- original storage path remains unchanged

--------------------------------------------------
STEP 22 — FAILURE TEST
--------------------------------------------------

Cause or simulate an OCR failure.

Verify:

status = OCR_FAILED

The original document must remain available.

The application must not crash.

The UI should show a user-friendly failure state.

--------------------------------------------------
STEP 23 — REFRESH TEST
--------------------------------------------------

Start OCR processing.

Refresh the browser.

The document's processing status must still be retrieved from the backend/database.

The UI must not rely only on local React state.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Only modify files directly required for:

- OCR
- document processing
- worker/job processing
- document status
- document API
- document UI status

Do NOT modify:

frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/BidderDetailPage.jsx
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Audit.jsx

Do NOT modify:

backend/app/ai/**
backend/app/verification/**
backend/app/integrations/**

Do not implement AI in this task.

Do not implement compliance logic.

Do not implement government API calls.

Do not redesign the architecture.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

TASK 08 is complete only when:

[ ] Uploaded documents can enter an OCR processing job
[ ] OCR processing is asynchronous
[ ] Worker/job architecture is used
[ ] OCRProcessor abstraction exists
[ ] Real/local OCR implementation works OR existing OCR implementation works
[ ] Deterministic demo OCR implementation exists for testing
[ ] PDF/image documents are supported
[ ] OCR text is stored in PostgreSQL
[ ] Original document remains in Supabase Storage
[ ] OCR status is stored
[ ] OCR completion is stored
[ ] OCR failures are handled
[ ] Duplicate processing is prevented
[ ] Retry works if implemented
[ ] OCR status API works
[ ] Frontend displays OCR status
[ ] Frontend can retrieve OCR text if exposed by the UI
[ ] Frontend does not directly access Supabase
[ ] Private storage remains private
[ ] No secrets are exposed
[ ] Backend tests pass
[ ] Frontend tests pass if configured
[ ] Existing document upload still works
[ ] Existing Tenders still work
[ ] Existing Bidders still work
[ ] Existing Tender Details still work
[ ] Existing Bidder Details still work
[ ] No unrelated functionality is broken
[ ] No unrelated files were modified

STOP AFTER TASK 08.

DO NOT automatically implement TASK 09.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. OCR implementation used.
3. OCRProcessor implementation.
4. Worker/job implementation.
5. Document status states.
6. Database fields used for OCR.
7. Storage behavior.
8. OCR API endpoints.
9. Frontend status behavior.
10. Test results.
11. Manual OCR test result.
12. Example of extracted text.
13. Failure test result.
14. Confirmation original file remains in Storage.
15. Confirmation OCR text is stored in PostgreSQL.
16. Any issues encountered.

STOP.
```

---

# 🧪 Your manual test

Use a **fictional document**.

Create something like:

```text
GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED

REGISTRATION DATE:
12/04/2024

STATE:
Tamil Nadu
```

Upload it.

Then watch:

```text
UPLOADED
   ↓
QUEUED
   ↓
OCR PROCESSING
   ↓
OCR COMPLETED
```

Then check Supabase:

```text
documents
```

You should have something conceptually like:

```text
document_id
bidder_id
document_type = GST
storage_path = bidder/.../gst.pdf

ocr_status = OCR_COMPLETED

ocr_text =
"GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5
LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED
..."

ocr_completed_at = ...
```

---

# 🔥 The most important test

**Refresh the page while OCR is processing.**

If after refresh you still see:

```text
OCR PROCESSING
```

and later:

```text
OCR COMPLETED
```

you know the status is actually coming from:

```text
Supabase
   ↓
FastAPI
   ↓
React
```

rather than:

```text
React local state
```

That's a big milestone.

---

# What we've achieved by TASK 08

Your pipeline is now becoming:

```text
                    BIDDER
                       │
                       ▼
                  DOCUMENT
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
         Supabase DB      Supabase Storage
         metadata             actual file
              │                 │
              └────────┬────────┘
                       ▼
                  OCR JOB
                       │
                       ▼
                    WORKER
                       │
                       ▼
                  OCR ENGINE
                       │
                       ▼
                EXTRACTED TEXT
                       │
                       ▼
                 PostgreSQL
```

And now we're ready for the **AI layer**.

### TASK 09 will be:

```text
OCR extracted text
       ↓
AI Extraction Service
       ↓
Structured JSON
       ↓
Validation
       ↓
Store extracted fields
```

For example:

```json
{
  "document_type": "GST",
  "gstin": "29ABCDE1234F1Z5",
  "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "registration_date": "2024-04-12"
}
```

That will be the point where your original idea of **“OCR first → send only text to AI → structured JSON”** actually becomes part of the working system.
