# TASK 09 — AI Document Extraction → Structured JSON

Excellent. Assuming **TASK 08 passed**, we now have a very important working pipeline:

```text
Bidder
  ↓
Document Upload
  ↓
Supabase Storage
  ↓
OCR Job
  ↓
OCR Worker
  ↓
Extracted Text
  ↓
Supabase
```

Now we add the **AI layer**.

The key principle is exactly what you identified at the beginning:

> **Don't send the original PDF/image to the LLM. OCR it first, then send only the extracted text.**

So TASK 09 becomes:

```text
OCR Text
   ↓
AI Extraction Service
   ↓
Structured JSON
   ↓
Validation
   ↓
Supabase
```

For example:

```text
OCR:

GST CERTIFICATE
GSTIN: 29ABCDE1234F1Z5
LEGAL NAME: ABC TECHNOLOGIES PRIVATE LIMITED
REGISTRATION DATE: 12/04/2024
```

becomes:

```json
{
  "document_type": "GST",
  "fields": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "registration_date": "2024-04-12"
  }
}
```

### ⚠️ Important

The AI **does not decide whether the bidder is compliant**.

It only extracts and normalizes information.

```text
AI
 ↓
"What information does this document contain?"

Compliance Engine
 ↓
"Does this information satisfy the tender requirement?"
```

That separation will be extremely important later.

---

# 🎯 TASK 09 OBJECTIVES

By the end of this task:

* OCR text can be sent to the AI service.
* AI returns predictable JSON.
* JSON is validated against a schema.
* AI failures are handled.
* AI output is stored.
* Demo/mock AI works without an API key.
* Real AI can be plugged in later.
* Existing OCR pipeline remains intact.

---

# 📁 Files allowed to modify

Likely:

```text
backend/app/ai/extractor.py
backend/app/ai/prompts.py

backend/app/services/document_service.py
backend/app/models/document.py
backend/app/schemas/document.py

backend/app/api/documents.py

backend/app/workers/jobs.py
backend/app/workers/worker.py

backend/tests/ai/**
backend/tests/...

supabase/migrations/**
```

Only modify the migration if your current schema doesn't have somewhere appropriate to store AI extraction results.

Potential frontend changes:

```text
frontend/src/pages/Documents.jsx
frontend/src/services/documentService.js
frontend/src/components/...
```

only if needed to display the extracted fields.

### Do NOT touch

```text
frontend/src/pages/Tenders.jsx
frontend/src/pages/TenderDetailPage.jsx
frontend/src/pages/Bidders.jsx
frontend/src/pages/BidderDetailPage.jsx
frontend/src/pages/Dashboard.jsx
frontend/src/pages/Audit.jsx

backend/app/integrations/**
backend/app/verification/**
backend/app/ocr/**
```

Do not modify the OCR implementation.

---

# 📋 Exact prompt for the vibe coder

```text id="8xg8cz"
TASK 09 — AI DOCUMENT EXTRACTION TO STRUCTURED JSON

TASK 08 has been completed successfully.

The application currently has a working:

Document Upload
      ↓
Supabase Storage
      ↓
OCR Job
      ↓
OCR Worker
      ↓
OCRProcessor
      ↓
Extracted Text
      ↓
Supabase PostgreSQL

Now implement the AI DOCUMENT EXTRACTION layer.

--------------------------------------------------
CORE PRINCIPLE
--------------------------------------------------

The AI must NOT process the original PDF/image directly.

The required flow is:

Original Document
      ↓
OCR
      ↓
Extracted Text
      ↓
AI Extraction
      ↓
Structured JSON
      ↓
Schema Validation
      ↓
Database

The purpose of AI in this task is ONLY to extract and normalize information from OCR text.

AI MUST NOT make compliance decisions.

AI MUST NOT determine bidder qualification.

AI MUST NOT calculate risk.

AI MUST NOT determine whether a bidder passes or fails a tender requirement.

Those responsibilities belong to the future Compliance Engine.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- compliance rules
- compliance scoring
- risk scoring
- government API verification
- PAN verification
- GST verification
- Udyam verification
- tender qualification
- bidder qualification
- final officer decisions
- external government integrations

Do NOT modify the OCR implementation.

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

The architecture must be:

OCR text
   ↓
AI Extraction Service
   ↓
Document-specific extraction schema
   ↓
JSON validation
   ↓
Database

The existing OCR layer must remain independent from the AI layer.

--------------------------------------------------
STEP 1 — INSPECT EXISTING AI STRUCTURE
--------------------------------------------------

Before modifying anything inspect:

- backend/app/ai/
- extractor.py
- prompts.py
- document model
- document schema
- document service
- worker/job architecture
- OCR pipeline
- existing database structure
- existing document APIs
- existing tests

Reuse existing architecture.

Do not create duplicate:

- AI clients
- AI services
- document services
- workers
- database clients
- schemas

--------------------------------------------------
STEP 2 — AI EXTRACTOR INTERFACE
--------------------------------------------------

Implement the existing:

backend/app/ai/extractor.py

as a provider-independent abstraction.

Conceptually:

AIExtractor
    ↓
extract(document_type, ocr_text)
    ↓
structured result

The rest of the application should not depend directly on one specific AI provider.

For example:

AIExtractor
    ├── DemoAIExtractor
    └── LLMExtractor

The actual provider can be configured later.

--------------------------------------------------
STEP 3 — DEMO AI EXTRACTOR
--------------------------------------------------

Create a deterministic DemoAIExtractor.

This is REQUIRED.

The application must be able to run and test without an external AI API key.

For known OCR fixture text:

GST:

GST CERTIFICATE
GSTIN: 29ABCDE1234F1Z5
LEGAL NAME: ABC TECHNOLOGIES PRIVATE LIMITED
REGISTRATION DATE: 12/04/2024

The demo extractor should return structured data.

Example:

{
  "document_type": "GST",
  "fields": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "registration_date": "2024-04-12"
  }
}

Do not make the demo extractor randomly generate values.

Results must be deterministic.

--------------------------------------------------
STEP 4 — REAL LLM PROVIDER ABSTRACTION
--------------------------------------------------

If the project already has an AI provider configuration, implement it using the existing architecture.

If no provider has been selected yet, DO NOT force the project to depend on one specific provider.

Create a provider-independent interface.

Configuration should allow the project to later provide:

AI_PROVIDER
AI_MODEL
AI_API_KEY

Do not hard-code credentials.

Do not expose API keys to React.

--------------------------------------------------
STEP 5 — DOCUMENT-SPECIFIC EXTRACTION
--------------------------------------------------

The AI extraction schema should depend on document type.

Start with a limited set of document types.

At minimum support demo extraction for:

PAN
GST
UDYAM

Other document types may return a generic schema initially.

Example GST:

{
  "document_type": "GST",
  "fields": {
    "gstin": "...",
    "legal_name": "...",
    "trade_name": "...",
    "registration_date": "...",
    "status": "...",
    "address": "..."
  }
}

Example PAN:

{
  "document_type": "PAN",
  "fields": {
    "pan": "...",
    "name": "...",
    "date_of_birth_or_incorporation": "..."
  }
}

Example UDYAM:

{
  "document_type": "UDYAM",
  "fields": {
    "udyam_number": "...",
    "enterprise_name": "...",
    "enterprise_type": "...",
    "major_activity": "..."
  }
}

Do not assume all fields are present.

Missing fields should be represented safely.

Do not invent values.

--------------------------------------------------
STEP 6 — STRUCTURED OUTPUT VALIDATION
--------------------------------------------------

AI output must NOT be trusted blindly.

Validate the returned JSON using the backend's schema validation mechanism.

The pipeline should be:

LLM output
   ↓
Parse JSON
   ↓
Validate schema
   ↓
Accept or reject

If invalid:

AI extraction should be marked as failed.

Do not silently accept malformed JSON.

Do not attempt uncontrolled string parsing throughout the application.

--------------------------------------------------
STEP 7 — STRICT AI OUTPUT
--------------------------------------------------

The AI prompt must explicitly require structured JSON.

It should be instructed:

- return JSON only
- do not include Markdown
- do not include explanations
- do not invent missing values
- use null for unavailable fields
- preserve identifiers exactly where possible
- normalize dates into a consistent format
- distinguish extracted values from inferred values

The system should validate the response after receiving it.

--------------------------------------------------
STEP 8 — PROMPT MANAGEMENT
--------------------------------------------------

Use:

backend/app/ai/prompts.py

for AI prompts.

Do NOT place long prompts directly inside:

- API routes
- React components
- worker code
- database code

Prompts should be versionable.

For example:

GST_EXTRACTION_PROMPT_V1

PAN_EXTRACTION_PROMPT_V1

UDYAM_EXTRACTION_PROMPT_V1

Do not over-engineer prompt management.

--------------------------------------------------
STEP 9 — AI TOKEN EFFICIENCY
--------------------------------------------------

The AI request must contain OCR text rather than the original document.

Do not send:

- PDF binary
- image binary
- base64 document
- unnecessary metadata
- unrelated application data

Only provide the information needed for extraction.

The main input should be:

document type
+
OCR text

This is intentional to reduce AI processing and token usage.

--------------------------------------------------
STEP 10 — AI RESULT STORAGE
--------------------------------------------------

Store the structured extraction result in Supabase PostgreSQL.

Use the existing documents table if appropriate.

If necessary, minimally extend the schema.

Possible fields:

ai_status
ai_extraction
ai_error
ai_completed_at
ai_model
ai_prompt_version

Do not create unnecessary duplicate tables.

The original OCR text must remain available.

The original document must remain in Storage.

Therefore the data chain becomes:

Storage:
original document

Database:
OCR text

Database:
AI structured extraction

--------------------------------------------------
STEP 11 — AI STATUS
--------------------------------------------------

Introduce controlled AI processing states.

For example:

AI_PENDING
AI_PROCESSING
AI_COMPLETED
AI_FAILED

Follow existing status conventions if already established.

Do not mix AI status with final compliance status.

For example:

AI_COMPLETED

does NOT mean:

COMPLIANT

It only means:

"Information was successfully extracted."

--------------------------------------------------
STEP 12 — WORKER INTEGRATION
--------------------------------------------------

Integrate AI extraction into the existing worker pipeline.

The flow should become:

Document uploaded
      ↓
OCR
      ↓
OCR_COMPLETED
      ↓
AI job
      ↓
AI_PROCESSING
      ↓
AIExtractor
      ↓
Schema validation
      ↓
AI_COMPLETED
      ↓
Store structured extraction

If OCR fails:

Do NOT run AI.

If OCR succeeds:

AI may run.

--------------------------------------------------
STEP 13 — IDEMPOTENCY
--------------------------------------------------

Do not accidentally run AI extraction multiple times simultaneously.

Before starting:

Check AI status.

If:

AI_PROCESSING

do not start another AI extraction.

If:

AI_COMPLETED

do not run again unless an explicit reprocess operation exists.

--------------------------------------------------
STEP 14 — FAILURE HANDLING
--------------------------------------------------

Handle:

- AI provider unavailable
- API timeout
- malformed JSON
- schema validation failure
- empty OCR text
- unexpected provider response

On failure:

AI status = AI_FAILED

Store a safe error message.

Do not expose provider secrets.

Do not delete the original document.

Do not delete OCR text.

--------------------------------------------------
STEP 15 — EMPTY OCR HANDLING
--------------------------------------------------

If OCR produced no meaningful text:

Do not call the AI provider.

Set an appropriate AI failure/blocked state.

Example:

"AI extraction skipped because OCR text is empty."

This avoids wasting AI requests.

--------------------------------------------------
STEP 16 — RETRY
--------------------------------------------------

If the existing worker architecture supports retries:

Allow failed AI extraction to be retried.

Do not create infinite retries.

Use a configurable retry limit.

Do not retry schema-validation failures endlessly without changing the input/provider behavior.

--------------------------------------------------
STEP 17 — API RESPONSE
--------------------------------------------------

Update the existing document API if necessary so authorized clients can see:

- OCR status
- AI status
- structured extracted fields

For example:

{
  "id": "...",
  "document_type": "GST",
  "ocr_status": "COMPLETED",
  "ai_status": "COMPLETED",
  "extraction": {
    "gstin": "...",
    "legal_name": "...",
    "registration_date": "..."
  }
}

Do not expose:

- AI API keys
- provider credentials
- internal prompts unless explicitly intended
- internal stack traces

Follow existing authorization architecture.

--------------------------------------------------
STEP 18 — FRONTEND DISPLAY
--------------------------------------------------

If the existing Documents page supports it, add a simple:

"Extracted Information"

section.

Example:

Document:
GST Certificate

AI Extraction:
--------------------------------
GSTIN
29ABCDE1234F1Z5

Legal Name
ABC TECHNOLOGIES PRIVATE LIMITED

Registration Date
12/04/2024

Do NOT display this as:

"Verified"

or:

"Compliant"

unless a future verification engine has actually verified it.

Use terminology such as:

"Extracted"

"Detected"

"AI extracted information"

--------------------------------------------------
STEP 19 — DEMO DATA
--------------------------------------------------

Keep deterministic demo AI extraction available.

Create safe fictional test fixtures.

Use:

GST
PAN
UDYAM

documents/text.

Do not use real people's documents.

--------------------------------------------------
STEP 20 — TESTING
--------------------------------------------------

Add backend tests for:

1. AIExtractor interface.
2. DemoAIExtractor.
3. GST extraction.
4. PAN extraction.
5. UDYAM extraction.
6. Empty OCR handling.
7. Valid JSON parsing.
8. Invalid JSON handling.
9. Schema validation.
10. Missing fields.
11. AI provider failure.
12. AI timeout.
13. Duplicate processing prevention.
14. AI status transitions.
15. Successful result storage.
16. Failed result storage.

Mock external AI providers.

Unit tests must NOT require a live external AI API.

--------------------------------------------------
STEP 21 — INTEGRATION TEST
--------------------------------------------------

Test:

Document
 ↓
OCR
 ↓
AI
 ↓
Structured JSON
 ↓
Database

Use a deterministic demo OCR + demo AI path for automated testing.

Example input:

GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED

REGISTRATION DATE:
12/04/2024

Expected extraction:

{
  "document_type": "GST",
  "fields": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "registration_date": "2024-04-12"
  }
}

--------------------------------------------------
STEP 22 — MANUAL TEST
--------------------------------------------------

Upload a fictional GST certificate.

Wait for:

OCR_COMPLETED

Then:

AI_PROCESSING

Then:

AI_COMPLETED

Open the document.

Verify:

1. OCR text exists.
2. AI extraction exists.
3. Extracted GSTIN is correct.
4. Legal name is correct.
5. Date is normalized correctly.
6. Original document remains in Storage.
7. OCR text remains in PostgreSQL.
8. AI JSON remains in PostgreSQL.

--------------------------------------------------
STEP 23 — CRITICAL NEGATIVE TEST
--------------------------------------------------

Create a document with incomplete information.

Example:

GST CERTIFICATE

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED

Do not include GSTIN.

The AI must NOT invent a GSTIN.

Expected:

{
  "gstin": null
}

or the project's equivalent missing-value representation.

This is extremely important.

The AI must extract what exists, not hallucinate missing information.

--------------------------------------------------
STEP 24 — VERIFY SEPARATION OF RESPONSIBILITIES
--------------------------------------------------

Confirm:

OCR answers:

"What text exists in this document?"

AI extraction answers:

"What structured information can be extracted from this text?"

Neither answers:

"Is this bidder compliant?"

Do not implement compliance decisions in this task.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Only modify files directly related to:

- AI extraction
- document processing
- AI status
- AI result storage
- document API
- document extraction UI

Do NOT modify:

backend/app/ocr/**
backend/app/integrations/**
backend/app/verification/**

Do NOT implement compliance logic.

Do NOT implement government API calls.

Do NOT redesign the application.

Do not create duplicate:

- AI clients
- document services
- workers
- database clients
- API clients
- schemas

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

TASK 09 is complete only when:

[ ] OCR text can be passed to AI
[ ] Original document is NOT sent to AI
[ ] AIExtractor abstraction exists
[ ] DemoAIExtractor exists
[ ] AI provider is configurable
[ ] API keys are not hardcoded
[ ] GST extraction works
[ ] PAN extraction works
[ ] UDYAM extraction works
[ ] Structured JSON is generated
[ ] JSON is schema validated
[ ] Invalid AI output is rejected
[ ] Missing fields do not cause hallucinated values
[ ] Empty OCR does not trigger unnecessary AI call
[ ] AI status is stored
[ ] AI extraction result is stored
[ ] OCR text remains stored
[ ] Original document remains in Storage
[ ] AI failure is handled
[ ] AI timeout is handled
[ ] Duplicate AI processing is prevented
[ ] Retry works if implemented
[ ] Worker integration works
[ ] API can return extracted fields
[ ] Frontend can display extracted information if implemented
[ ] Extracted information is clearly distinguished from verification
[ ] Backend tests pass
[ ] Frontend tests pass if configured
[ ] Existing OCR functionality still works
[ ] Existing document upload still works
[ ] Tenders still work
[ ] Bidders still work
[ ] Tender Details still work
[ ] Bidder Details still work
[ ] No unrelated modules are broken
[ ] No unrelated files were modified

STOP AFTER TASK 09.

Do NOT automatically implement TASK 10.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. AI abstraction implemented.
3. Demo AI implementation.
4. Real AI provider implementation, if any.
5. AI model configuration.
6. Prompt versioning approach.
7. Supported document types.
8. JSON schema approach.
9. Database fields used.
10. AI status flow.
11. Worker integration.
12. Failure handling.
13. Retry behavior.
14. Tests executed and results.
15. Manual test result.
16. Negative/hallucination test result.
17. Example structured extraction.
18. Confirmation that original document remains in Storage.
19. Confirmation OCR text remains stored.
20. Confirmation AI result is stored.
21. Confirmation AI does not make compliance decisions.
22. Any issues encountered.

STOP.
```

---

# 🧪 Manual testing

This task has **two particularly important tests**.

## Test 1 — Normal extraction

Upload your fictional GST document:

```text
GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED

REGISTRATION DATE:
12/04/2024
```

You should eventually get:

```text
OCR
✓ COMPLETED

AI EXTRACTION
✓ COMPLETED
```

And:

```json
{
  "document_type": "GST",
  "fields": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "registration_date": "2024-04-12"
  }
}
```

---

# 🚨 Test 2 — Hallucination test

This one is **more important than the first one**.

Upload:

```text
GST CERTIFICATE

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED
```

There is **NO GSTIN**.

The AI should return:

```json
{
  "gstin": null
}
```

or whatever missing-field representation your schema defines.

It should **NOT** magically produce:

```text
29ABCDE1234F1Z5
```

That's critical because eventually your system will be dealing with eligibility decisions.

---

# 🧠 The architecture after TASK 09

We're now here:

```text
                         DOCUMENT
                            │
                            ▼
                    Supabase Storage
                            │
                            ▼
                         OCR JOB
                            │
                            ▼
                          OCR
                            │
                            ▼
                      OCR TEXT
                            │
                            ▼
                    AI EXTRACTION
                            │
                            ▼
                  STRUCTURED JSON
                            │
                            ▼
                       Supabase
```

And notice what **isn't** there yet:

```text
❌ "COMPLIANT"
❌ "NOT COMPLIANT"
❌ "HIGH RISK"
❌ "QUALIFIED"
❌ "DISQUALIFIED"
```

That's intentional.

We now have **evidence extraction**, but not **evidence verification**.

---

# 🚀 TASK 10

The next task should connect the extracted information to your **Government Integration Framework**.

We'll build the first real verification layer:

```text
AI Extracted GSTIN
       ↓
GST Integration
       ↓
Demo Government GST Data
       ↓
Cross-verification
       ↓
MATCH / MISMATCH / NOT_FOUND
```

And similarly for PAN.

This is where the system starts becoming a **bid compliance verification platform**, rather than just a document management system.
