# 🚀 TASK 19 — Tender Document Processing & AI Requirement Extraction Workspace

Assuming **TASK 18** is completed successfully, TASK 19 should now make the **tender-document side of the system genuinely usable end-to-end**.

The distinction is important:

* **TASK 18** = officer manages/reviews requirements.
* **TASK 19** = officer uploads a tender document and watches it go through **OCR → AI requirement extraction → review queue**.

This is where the tender-side AI workflow becomes demonstrable.

---

# 🎯 Objective

Build the workflow:

```text
Officer uploads Tender PDF
        ↓
Document stored securely
        ↓
OCR processing
        ↓
Extracted tender text
        ↓
AI requirement extraction
        ↓
AI Suggested Requirements
        ↓
Officer reviews them
        ↓
TASK 18 approval workflow
```

The system should **not automatically approve extracted requirements**.

---

# 🧠 Final Tender Processing Flow

After TASK 19:

```text
                    TENDER
                      │
                      ▼
              Tender Documents
                      │
                      ▼
                    OCR
                      │
                      ▼
              Extracted Text
                      │
                      ▼
             AI Requirement
               Extraction
                      │
                      ▼
             AI_SUGGESTED
             Requirements
                      │
                      ▼
              Officer Review
                 TASK 18
                      │
             ┌────────┴────────┐
             ▼                 ▼
          APPROVED          REJECTED
             │
             ▼
      Compliance Engine
```

---

# 📁 Files to create

First inspect TASK 07, TASK 08, TASK 09, TASK 12 and TASK 18.

Reuse existing document/OCR/AI infrastructure wherever possible.

Only create these if equivalent files do not already exist:

```text
backend/
└── app/
    └── tender_processing/
        ├── __init__.py
        ├── schemas.py
        ├── service.py
        ├── repository.py
        └── router.py

frontend/
└── src/
    ├── services/
    │   └── tenderProcessingService.js
    │
    └── components/
        └── tender-documents/
            ├── TenderDocumentWorkspace.jsx
            ├── TenderDocumentUpload.jsx
            ├── ProcessingStatus.jsx
            ├── OCRTextViewer.jsx
            └── ExtractionStatus.jsx
```

If TASK 12 already contains processing logic:

> **Extend it instead of creating another processing pipeline.**

---

# 🔐 Allowed modifications

Allowed:

```text
backend/app/main.py
```

for route registration.

Existing tender-detail routing/navigation may be modified.

Existing document/OCR/AI components may be minimally extended.

---

# ❌ Do NOT modify

Do not rewrite:

```text
backend/app/ocr/
backend/app/ai/
backend/app/government/
backend/app/compliance/
backend/app/review/
backend/app/dashboard/
```

Reuse their interfaces.

Do not create:

* another OCR processor
* another AI provider
* another document storage system
* another requirement engine

---

# STEP 1 — Tender Document Metadata

Tender documents belong to the **tender**, not a bidder.

Use the existing document architecture where possible.

Conceptually:

```text
TenderDocument
```

should contain:

```text
id
tender_id
document_type
filename
storage_path
mime_type
size
ocr_status
ocr_text
ai_status
created_at
updated_at
```

Document types:

```text
TENDER_DOCUMENT
TENDER_CORRIGENDUM
TENDER_ADDENDUM
TENDER_OTHER
```

Do not store PDF binary data directly inside PostgreSQL.

---

# 📤 STEP 2 — Tender Document Upload

Create:

```http
POST /api/v1/tenders/{tender_id}/documents
```

Support:

```text
PDF
PNG
JPG
JPEG
```

Use the existing document validation from TASK 07.

Validate:

* tender exists
* supported MIME type
* file size
* filename
* storage path

Store the actual document in private Supabase Storage.

---

# 🔒 Storage Structure

Prefer something like:

```text
bidder-documents/
    tenders/
        {tender_id}/
            {document_id}/
                original.pdf
```

If the existing bucket architecture uses a different structure, preserve the established convention.

Do not create unnecessary buckets.

---

# 🔄 STEP 3 — Processing Lifecycle

Implement a clear lifecycle.

Example:

```text
UPLOADED
   ↓
QUEUED
   ↓
OCR_PROCESSING
   ↓
OCR_COMPLETED
   ↓
AI_PROCESSING
   ↓
AI_COMPLETED
```

Failure states:

```text
OCR_FAILED
AI_FAILED
```

The original document remains available even when processing fails.

---

# 🤖 STEP 4 — AI Requirement Extraction

Once OCR finishes:

```text
OCR text
   ↓
TenderRequirementExtractor
   ↓
Structured candidate requirements
```

Use the existing AI provider abstraction from TASK 09.

Do **not** send the original PDF/image to the LLM.

Send:

```text
OCR text
```

only.

---

# 🧾 STEP 5 — Structured AI Output

The extractor should produce structured candidates.

Example:

```json
{
  "requirements": [
    {
      "title": "Valid GST Registration",
      "description": "Tenderer shall possess a valid and active GST registration.",
      "category": "GST",
      "mandatory": true,
      "suggested_rule_type": "STATUS_EQUALS",
      "suggested_parameters": {
        "source": "GST",
        "field": "status",
        "operator": "EQUALS",
        "expected_value": "ACTIVE"
      },
      "source": {
        "page": 2,
        "section": "Eligibility",
        "text": "Tenderer shall possess a valid and active GST registration."
      }
    }
  ]
}
```

The exact schema should reuse TASK 12's existing schema if already implemented.

---

# 🚨 STEP 6 — No Hallucinated Requirements

This is critical.

Given:

```text
Tender document:
"The bidder must possess a valid GST registration."
```

AI may suggest:

```text
GST Registration
```

But it must **not invent**:

```text
PAN
UDYAM
EPFO
ESIC
OEM
Tamil Nadu registration
```

unless those requirements actually appear in the OCR text.

---

# 🧪 Negative AI Test

Input:

```text
The bidder must submit a valid GST certificate.
```

Expected:

```text
GST → suggested
```

Not:

```text
PAN → suggested
UDYAM → suggested
EPFO → suggested
```

This should be an automated test.

---

# 📄 STEP 7 — Source Traceability

Every extracted candidate requirement should contain:

```text
document_id
page
section
source_text
```

Example:

```text
GST Registration

Source:
Tender_2026.pdf

Page:
2

Section:
Eligibility Criteria

Text:
"Bidder shall possess a valid and active GST registration."
```

If page/section cannot be reliably determined:

```text
page = null
section = null
```

Do not invent them.

---

# 🖥️ STEP 8 — Tender Document Workspace

Create:

```text
Tender
 ↓
Documents
```

Example:

```text
Tender Documents

┌───────────────────────────────────────────┐
│ Tender_2026.pdf                           │
│ TENDER_DOCUMENT                            │
│                                           │
│ OCR: ✓ Completed                          │
│ AI Extraction: ✓ Completed                │
│ Requirements Found: 8                     │
│                                           │
│ [View Document] [View OCR] [Requirements] │
└───────────────────────────────────────────┘

┌───────────────────────────────────────────┐
│ Corrigendum_01.pdf                        │
│ TENDER_CORRIGENDUM                         │
│                                           │
│ OCR: Processing...                        │
│ AI Extraction: Waiting                    │
└───────────────────────────────────────────┘
```

---

# 📊 STEP 9 — Processing Status

Create a clear status component.

Example:

```text
Document Processing

✓ Uploaded
✓ OCR Completed
✓ Text Extracted
⟳ AI Requirement Extraction
○ Officer Review
```

Failure:

```text
✓ Uploaded
✕ OCR Failed

Error:
Unable to process document.

[Retry OCR]
```

Do not expose raw stack traces to the officer.

---

# 📖 STEP 10 — OCR Viewer

Allow the officer to inspect OCR text.

Example:

```text
Extracted Tender Text
────────────────────────────

1. Eligibility

Tenderer shall possess a valid and
active GST registration.

The bidder shall submit a valid PAN.

The bidder must be registered in
Tamil Nadu.

...
```

This is extremely useful for the demo because the officer can visually verify:

```text
Document
   ↓
OCR
   ↓
AI interpretation
```

---

# 🤖 STEP 11 — Extraction Results

After AI processing:

```text
AI Requirement Extraction

8 requirements identified

✓ GST Registration
✓ PAN
✓ Tamil Nadu Registration
✓ Debarment
...
```

Every item should initially be:

```text
AI_SUGGESTED
```

not:

```text
APPROVED
```

---

# 🔗 STEP 12 — Connect to TASK 18

Click:

```text
Review Requirements
```

should open the TASK 18 workspace.

For example:

```text
Tender Document
      ↓
AI Extraction
      ↓
8 AI Suggestions
      ↓
[Review Requirements]
      ↓
Tender Requirements
```

Do not implement a second approval UI.

---

# ⚙️ STEP 13 — Processing API

Implement/reuse:

```http
POST /api/v1/tenders/{tender_id}/documents/{document_id}/process
```

This should initiate:

```text
OCR
 ↓
AI extraction
```

using the existing worker architecture.

Do not execute a long OCR/LLM process synchronously inside the HTTP request.

---

# 📊 STEP 14 — Status API

Provide:

```http
GET /api/v1/tenders/{tender_id}/documents/{document_id}/processing
```

Example:

```json
{
  "document_id": "doc-001",
  "ocr_status": "OCR_COMPLETED",
  "ai_status": "AI_COMPLETED",
  "requirements_found": 8,
  "last_updated": "2026-09-11T10:30:00"
}
```

---

# ⚡ STEP 15 — Worker Integration

Reuse TASK 08/09 worker infrastructure.

Preferred flow:

```text
Upload
 ↓
Create processing job
 ↓
Worker
 ↓
OCR
 ↓
Persist OCR
 ↓
AI extraction
 ↓
Persist suggestions
```

Do not create another worker framework.

---

# 🔁 STEP 16 — Retry

Support safe retry.

Example:

```text
OCR_FAILED
    ↓
Retry
    ↓
QUEUED
```

or:

```text
AI_FAILED
    ↓
Retry AI
```

Avoid rerunning OCR unnecessarily when OCR has already succeeded.

For example:

```text
OCR_COMPLETED
AI_FAILED
```

should preferably retry:

```text
AI only
```

rather than:

```text
OCR + AI
```

---

# 🧪 STEP 17 — Backend Tests

Test:

### Upload

```text
valid PDF → stored
invalid file → rejected
oversized file → rejected
```

### OCR flow

```text
UPLOADED
→ QUEUED
→ OCR_PROCESSING
→ OCR_COMPLETED
```

### AI flow

```text
OCR_COMPLETED
→ AI_PROCESSING
→ AI_COMPLETED
```

### Failure

```text
OCR_FAILED
```

and:

```text
AI_FAILED
```

must preserve the original document.

---

# 🧪 STEP 18 — Requirement Extraction Tests

Given:

```text
Tenderer shall possess a valid and active GST registration.

The bidder shall submit a valid PAN.

The bidder must be registered in Tamil Nadu.

The bidder shall not be debarred by any government authority.
```

Expected candidates:

```text
GST
PAN
Tamil Nadu Registration
Debarment
```

All should initially be:

```text
AI_SUGGESTED
```

---

# 🧪 STEP 19 — Hallucination Test

Input:

```text
The bidder shall possess a valid GST registration.
```

Expected:

```text
GST → AI_SUGGESTED
```

Expected absent:

```text
PAN
UDYAM
EPFO
ESIC
NSIC
OEM
```

unless explicitly present in the source text.

---

# 🧪 STEP 20 — End-to-End Manual Test

Use a demo PDF containing:

```text
Eligibility Requirements

1. Tenderer shall possess a valid and active GST registration.

2. The bidder shall submit a valid PAN.

3. The bidder must be registered in Tamil Nadu.

4. The bidder shall not be debarred by any government authority.
```

Upload it.

Expected:

```text
Uploaded ✓
```

Then:

```text
OCR Processing
```

Then:

```text
OCR Completed ✓
```

Open OCR viewer.

Verify the text.

Then:

```text
AI Processing
```

Then:

```text
AI Completed ✓
```

Open requirements.

Expected:

```text
GST Registration       AI_SUGGESTED
PAN                    AI_SUGGESTED
Tamil Nadu Registration AI_SUGGESTED
Debarment              AI_SUGGESTED
```

Approve one requirement through TASK 18.

Expected:

```text
GST Registration
APPROVED
```

The remaining three stay:

```text
AI_SUGGESTED
```

Run compliance evaluation.

Only the approved requirement should be active.

🔥 This is the complete human-in-the-loop demonstration.

---

# 🎨 UI Style

Continue the existing style:

```text
white/light background
simple cards
clear borders
standard buttons
minimal animation
```

Status colors:

```text
COMPLETED       green
PROCESSING      blue
AI_SUGGESTED    orange
FAILED          red
INFORMATION     blue
```

No flashy AI effects.

The application should look like a **government procurement system with AI assistance**, not an AI chatbot.

---

# 🚫 Do NOT implement

Do not add:

```text
automatic requirement approval
automatic compliance decisions
automatic bidder qualification
automatic bidder rejection
real government API integrations
document summarization chatbot
tender ranking
bid price analysis
OCR replacement
new AI provider
new worker system
```

Those are outside TASK 19.

---

# ✅ Definition of Done

TASK 19 is complete when:

* [ ] Tender documents can be uploaded
* [ ] Documents are stored securely
* [ ] Tender documents are associated with the correct tender
* [ ] OCR uses existing TASK 08 architecture
* [ ] AI extraction uses existing TASK 09 architecture
* [ ] Tender requirements use TASK 12/18 architecture
* [ ] OCR text is viewable
* [ ] AI extraction status is visible
* [ ] AI suggestions are visible
* [ ] Source page/section/text is preserved where available
* [ ] AI cannot automatically approve requirements
* [ ] Failed processing preserves original documents
* [ ] Retry works
* [ ] OCR is not unnecessarily repeated during AI retry
* [ ] Processing is asynchronous
* [ ] No duplicate worker system exists
* [ ] Hallucination test passes
* [ ] End-to-end upload → OCR → AI → review works
* [ ] Existing TASK 01–18 functionality remains intact

---

# 📋 COPY THIS DIRECTLY TO YOUR VIBE CODER

```text
TASK 19 — Build the Tender Document Processing & AI Requirement Extraction Workspace.

Assume TASKS 01–18 are fully implemented and working.

OBJECTIVE:

Build the tender-side document processing workflow:

Tender Document
↓
Secure Storage
↓
OCR
↓
Extracted Text
↓
AI Requirement Extraction
↓
AI_SUGGESTED Requirements
↓
TASK 18 Officer Review

CRITICAL RULE:

AI-generated requirements are suggestions only.

AI MUST NOT automatically approve or activate requirements.

Only an explicitly APPROVED requirement from TASK 18 may be consumed by the compliance engine.

FIRST:

Inspect existing implementations from:
TASK 07 Document Management
TASK 08 OCR
TASK 09 AI Extraction
TASK 12 Requirement Extraction
TASK 18 Requirement Review

Reuse existing abstractions.

DO NOT create duplicate:
- document storage
- OCR processor
- AI provider
- worker
- requirement system
- audit system

BACKEND:

Create/reuse:

backend/app/tender_processing/
    __init__.py
    schemas.py
    service.py
    repository.py
    router.py

Tender documents belong to the tender.

Use existing document architecture.

Document types:

TENDER_DOCUMENT
TENDER_CORRIGENDUM
TENDER_ADDENDUM
TENDER_OTHER

Processing lifecycle:

UPLOADED
QUEUED
OCR_PROCESSING
OCR_COMPLETED
AI_PROCESSING
AI_COMPLETED

Failure states:

OCR_FAILED
AI_FAILED

Original documents must remain available after processing failures.

UPLOAD API:

POST
/api/v1/tenders/{tender_id}/documents

Support:
PDF
PNG
JPG
JPEG

Validate:
- tender exists
- MIME type
- file size
- filename

Store binaries in private Supabase Storage.

Do not store binary files in PostgreSQL.

PROCESS API:

POST
/api/v1/tenders/{tender_id}/documents/{document_id}/process

Processing must be asynchronous.

Reuse the existing worker architecture from TASK 08/09.

STATUS API:

GET
/api/v1/tenders/{tender_id}/documents/{document_id}/processing

Return:

document_id
ocr_status
ai_status
requirements_found
last_updated

OCR:

Use the existing OCR processor.

Do NOT create a second OCR implementation.

Store OCR text separately from original document.

AI:

Use the existing AI provider abstraction.

AI receives OCR TEXT ONLY.

Do not send the original PDF/image to the LLM.

Use the existing TenderRequirementExtractor from TASK 12 if available.

Structured requirement output should include, where available:

title
description
category
mandatory
suggested_rule_type
suggested_parameters
source_document_id
source_page
source_section
source_text

Do not invent source information.

If page or section cannot be determined, use null.

ALL extracted requirements must initially have:

AI_SUGGESTED

They must not become APPROVED automatically.

HALLUCINATION PROTECTION:

If OCR text says:

"The bidder shall possess a valid GST registration."

AI should suggest GST.

It must NOT invent:
PAN
UDYAM
EPFO
ESIC
NSIC
OEM
etc.

unless explicitly supported by the source text.

RETRY:

If OCR fails:
retry OCR.

If AI fails after OCR succeeds:
retry AI only.

Do not unnecessarily rerun successful OCR.

FRONTEND:

Create/reuse:

frontend/src/services/tenderProcessingService.js

frontend/src/components/tender-documents/
    TenderDocumentWorkspace.jsx
    TenderDocumentUpload.jsx
    ProcessingStatus.jsx
    OCRTextViewer.jsx
    ExtractionStatus.jsx

Tender page should contain:

Documents
Requirements
Evaluation Dashboard

Tender Document Workspace should show:

filename
document type
upload date
OCR status
AI status
requirements found

Actions:

View Document
View OCR
View Requirements
Process
Retry

Processing status should visually show:

Uploaded
OCR Processing
OCR Completed
AI Processing
AI Completed
Officer Review

OCR viewer must display actual extracted OCR text.

AI extraction result should show:

AI Suggested Requirements

Every requirement must remain AI_SUGGESTED until TASK 18 officer approval.

REQUIREMENT INTEGRATION:

"Review Requirements" must open the existing TASK 18 requirement workspace.

Do not create another approval workflow.

SECURITY:

Use backend-controlled access to private storage.

Frontend must not directly bypass backend document authorization.

TESTS:

1. Valid PDF upload
2. Invalid file rejection
3. Oversized file rejection
4. OCR lifecycle
5. OCR failure
6. AI lifecycle
7. AI failure
8. Retry OCR
9. Retry AI without rerunning successful OCR
10. Requirement extraction
11. Source traceability
12. AI hallucination protection
13. Only AI_SUGGESTED status after extraction
14. Approved requirement from TASK 18 enters compliance
15. Unapproved requirement does not enter compliance

MANUAL TEST:

Use a demo tender PDF containing:

Eligibility Requirements

1. Tenderer shall possess a valid and active GST registration.

2. The bidder shall submit a valid PAN.

3. The bidder must be registered in Tamil Nadu.

4. The bidder shall not be debarred by any government authority.

Upload the document.

Verify:

Upload complete
→ OCR processing
→ OCR completed
→ OCR text visible
→ AI processing
→ AI completed

Expected requirements:

GST Registration
PAN
Tamil Nadu Registration
Debarment

All must initially be:

AI_SUGGESTED

Approve only GST through TASK 18.

Verify:

GST = APPROVED
PAN = AI_SUGGESTED
Tamil Nadu = AI_SUGGESTED
Debarment = AI_SUGGESTED

Run compliance evaluation.

Only APPROVED requirements should participate.

Then create an AI_SUGGESTED requirement that has not been approved and verify it cannot participate in compliance evaluation.

STRICT SCOPE:

Do NOT modify:

backend/app/ocr/
backend/app/ai/
backend/app/government/
backend/app/compliance/
backend/app/review/
backend/app/dashboard/

Reuse existing functionality.

Do not create duplicate workers.

Do not create duplicate requirement approval logic.

Do not introduce automatic qualification/rejection.

Do not start TASK 20.

At the end report:

1. Files created
2. Files modified
3. APIs added
4. Database changes
5. Worker changes
6. Tests executed
7. Manual test results
8. Confirmation that AI suggestions cannot bypass officer approval

STOP AFTER TASK 19.
```

### 🏗️ Your architecture after TASK 19

You now have two complete major pipelines:

```text
                  ┌─────────────────────┐
                  │   TENDER DOCUMENT   │
                  └──────────┬──────────┘
                             ↓
                            OCR
                             ↓
                       AI EXTRACTION
                             ↓
                    AI REQUIREMENTS
                             ↓
                    OFFICER APPROVAL
                             ↓
                    APPROVED REQUIREMENTS
                             ↓
                     COMPLIANCE ENGINE
                             ↓
                      BIDDER EVALUATION
                             ↓
                       EVIDENCE TRACE
                             ↓
                      OFFICER REVIEW
                             ↓
                    TENDER DASHBOARD
```

And on the bidder side:

```text
Bidder Document
      ↓
OCR
      ↓
AI Extraction
      ↓
Government Verification
      ↓
Evidence
      ↓
Compliance
      ↓
Officer Review
```

**That separation is exactly what you want for a team of vibe coders:** each major subsystem has a clear responsibility and the AI is never allowed to silently cross the human-approval boundary.
