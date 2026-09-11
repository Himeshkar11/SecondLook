# 🚀 TASK 10 — Government Verification Integration Layer

Assuming **TASK 09 passed completely**, we now move from:

```text
Document
   ↓
OCR
   ↓
AI Extraction
   ↓
Structured Data
```

to the first actual **verification** step:

```text
AI Extracted Data
        ↓
Government Verification Adapter
        ↓
Government/Demo Source
        ↓
Comparison
        ↓
Verification Result
```

For this task, **only GST and PAN** should be implemented as real verification targets, because those are the government/public API integrations you've decided to support initially.

Everything else remains behind the integration framework with mock/demo providers.

The most important architectural rule:

> **Government verification must be completely separate from AI extraction.**

AI says:

> “The document appears to contain GSTIN X.”

The government source says:

> “GSTIN X has these registered details.”

Your future compliance engine will decide what that means for the tender.

---

# 🎯 TASK 10 OBJECTIVES

Implement:

* Government integration abstraction
* GST verification adapter
* PAN verification adapter
* Demo/mock government providers
* Government verification status
* Extracted-data vs government-data comparison
* Verification result storage
* Verification API
* Tests
* Manual verification flow

Do **not** implement tender compliance rules yet.

---

# 🏗️ TARGET ARCHITECTURE

The architecture should become:

```text
                    DOCUMENT
                       │
                       ▼
                      OCR
                       │
                       ▼
                AI EXTRACTION
                       │
                       ▼
              STRUCTURED DATA
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        GST Verification   PAN Verification
              │                 │
              ▼                 ▼
       Government Adapter  Government Adapter
              │                 │
              ▼                 ▼
       Gov/Demo Response   Gov/Demo Response
              │                 │
              └────────┬────────┘
                       ▼
                  COMPARISON
                       │
                       ▼
              VERIFICATION RESULT
```

Then later:

```text
VERIFICATION RESULT
        ↓
COMPLIANCE ENGINE
        ↓
TENDER REQUIREMENTS
        ↓
COMPLIANT / NON-COMPLIANT
```

**Not in TASK 10.**

---

# 📁 Exact vibe-coding prompt

Give this entire prompt to your vibe coder:

```text
TASK 10 — GOVERNMENT VERIFICATION INTEGRATION LAYER

TASK 09 has been completed successfully.

The application currently supports:

Document Upload
      ↓
Supabase Storage
      ↓
OCR
      ↓
Extracted OCR Text
      ↓
AI Extraction
      ↓
Structured JSON
      ↓
Supabase

Now implement the GOVERNMENT VERIFICATION INTEGRATION LAYER.

--------------------------------------------------
CORE PURPOSE
--------------------------------------------------

The purpose of this task is to verify extracted bidder information against government/public data sources.

For the first implementation:

1. GST verification
2. PAN verification

must be supported.

The application must use an abstraction layer so additional government integrations can be added later without rewriting the verification system.

--------------------------------------------------
CRITICAL ARCHITECTURAL RULE
--------------------------------------------------

AI extraction and government verification are separate responsibilities.

AI extraction answers:

"What information can be extracted from the document?"

Government verification answers:

"Does the supplied identifier/data correspond to information returned by the verification source?"

The government verification layer MUST NOT:

- decide tender compliance
- decide bidder qualification
- calculate risk
- approve bidders
- reject bidders
- interpret tender clauses
- assign final compliance scores

Those responsibilities belong to a future Compliance Engine.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- tender compliance rules
- tender requirement matching
- risk scoring
- final qualification
- disqualification
- compliance score
- procurement officer decision
- Udyam verification
- MCA verification
- EPFO verification
- ESIC verification
- Startup India verification
- NSIC verification
- OEM verification
- Make in India verification
- DigiLocker verification
- blacklisting verification

Only create the reusable framework for future integrations.

--------------------------------------------------
STEP 1 — INSPECT EXISTING STRUCTURE
--------------------------------------------------

Before changing anything inspect:

backend/app/integrations/
backend/app/ai/
backend/app/services/
backend/app/models/
backend/app/schemas/
backend/app/workers/
backend/app/api/
backend/tests/
supabase/migrations/

Also inspect:

- existing Government Integration Framework
- existing demo government data
- existing document model
- existing AI extraction model
- existing bidder model
- existing configuration system
- existing database client
- existing worker architecture

Reuse existing components.

Do NOT create duplicate clients or services.

--------------------------------------------------
STEP 2 — GOVERNMENT PROVIDER INTERFACE
--------------------------------------------------

Create or complete a provider-independent government integration interface.

Conceptually:

GovernmentProvider

    verify(identifier/data)
        ↓
    GovernmentVerificationResponse

The rest of the application must not depend directly on:

- a GST API SDK
- an HTTP implementation
- a specific vendor
- demo data

Providers should be replaceable.

Example:

GovernmentProvider
    ├── DemoGSTProvider
    ├── GSTProvider
    ├── DemoPANProvider
    └── PANProvider

Use the project's existing naming conventions where possible.

--------------------------------------------------
STEP 3 — STANDARD RESPONSE FORMAT
--------------------------------------------------

All government integrations should return a normalized response.

Example:

{
  "source": "GST",
  "status": "FOUND",
  "identifier": "29ABCDE1234F1Z5",
  "data": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "trade_name": "ABC TECHNOLOGIES",
    "registration_date": "2024-04-12",
    "status": "ACTIVE",
    "state": "Tamil Nadu"
  }
}

Possible source status values:

FOUND
NOT_FOUND
ERROR
UNAVAILABLE

Follow existing project conventions if they already exist.

Do not create compliance statuses here.

--------------------------------------------------
STEP 4 — DEMO GST PROVIDER
--------------------------------------------------

Create a deterministic DemoGSTProvider.

It must work without an external API.

Use fictional demo data.

For example:

GSTIN:

29ABCDE1234F1Z5

Return:

{
  "gstin": "29ABCDE1234F1Z5",
  "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "trade_name": "ABC TECHNOLOGIES",
  "registration_date": "2024-04-12",
  "status": "ACTIVE",
  "state": "Tamil Nadu"
}

Also create deterministic negative cases.

Example:

GSTIN:

29NOTFOUND1234F1

returns:

NOT_FOUND

Do not use real taxpayer information.

--------------------------------------------------
STEP 5 — DEMO PAN PROVIDER
--------------------------------------------------

Create a deterministic DemoPANProvider.

Use fictional demo data.

Example:

PAN:

ABCDE1234F

Return:

{
  "pan": "ABCDE1234F",
  "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "status": "ACTIVE"
}

Create a deterministic NOT_FOUND example.

Do not use real personal PAN data.

--------------------------------------------------
STEP 6 — REAL API ADAPTERS
--------------------------------------------------

If an official/public API is already available and configured in the project, implement the adapter behind the GovernmentProvider interface.

If no usable official API credentials or endpoint are available:

DO NOT invent an API endpoint.

DO NOT scrape a government website.

DO NOT bypass authentication.

Do NOT hard-code credentials.

Keep the real provider as an integration-ready adapter/configuration point.

The Demo providers must remain usable.

--------------------------------------------------
STEP 7 — CONFIGURATION
--------------------------------------------------

Government providers must be configurable.

Use environment variables/configuration.

Possible configuration:

GST_PROVIDER=demo
PAN_PROVIDER=demo

Potential real-provider configuration can later include:

GST_API_URL
GST_API_KEY
PAN_API_URL
PAN_API_KEY

Use names consistent with the existing project.

Never commit credentials.

Never expose credentials to React.

--------------------------------------------------
STEP 8 — VERIFICATION SERVICE
--------------------------------------------------

Create a service responsible for orchestrating verification.

Conceptually:

GovernmentVerificationService

Input:

document/extracted data

Example:

{
  "document_type": "GST",
  "fields": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED"
  }
}

The service should:

1. validate required identifier exists
2. select correct provider
3. call provider
4. receive normalized government response
5. compare extracted information with government information
6. produce normalized verification result
7. store result

--------------------------------------------------
STEP 9 — IDENTIFIER VALIDATION
--------------------------------------------------

Before calling a provider validate the identifier format where appropriate.

GSTIN should have basic structural validation.

PAN should have basic structural validation.

Do not treat format validity as government verification.

For example:

VALID FORMAT

does NOT mean:

GOVERNMENT VERIFIED

The result should distinguish:

format validation
from
government lookup

--------------------------------------------------
STEP 10 — DATA COMPARISON
--------------------------------------------------

After receiving government data compare relevant extracted fields.

For GST compare, where available:

- GSTIN
- legal name
- trade name
- registration date
- status
- state

For PAN compare:

- PAN
- name
- status

Do not make overly aggressive comparisons.

For names:

- trim whitespace
- normalize casing
- normalize repeated whitespace

Do not use fuzzy matching unless the existing project explicitly requires it.

Do not declare two names equal solely because they "look similar" unless the comparison algorithm is deterministic and documented.

--------------------------------------------------
STEP 11 — FIELD-LEVEL RESULTS
--------------------------------------------------

Produce field-level comparison results.

Example:

{
  "gstin": {
    "document_value": "29ABCDE1234F1Z5",
    "government_value": "29ABCDE1234F1Z5",
    "status": "MATCH"
  },
  "legal_name": {
    "document_value": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "government_value": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "status": "MATCH"
  },
  "status": {
    "document_value": "ACTIVE",
    "government_value": "ACTIVE",
    "status": "MATCH"
  }
}

Possible field comparison states:

MATCH
MISMATCH
MISSING_FROM_DOCUMENT
MISSING_FROM_SOURCE

Use existing project conventions if available.

--------------------------------------------------
STEP 12 — OVERALL VERIFICATION RESULT
--------------------------------------------------

Create an overall government verification result.

Possible states:

VERIFIED
MISMATCH
NOT_FOUND
SOURCE_ERROR
PENDING

Important:

VERIFIED means:

"The government source response matched the fields that were successfully compared."

It does NOT mean:

"The bidder is compliant."

It does NOT mean:

"The bidder is qualified."

It does NOT mean:

"The bidder should be awarded the tender."

--------------------------------------------------
STEP 13 — GOVERNMENT RESPONSE STORAGE
--------------------------------------------------

Store the verification result in Supabase.

The stored result should contain enough information for auditability.

Possible fields:

verification_id
document_id
bidder_id
source
provider
identifier
status
government_data
field_results
created_at
completed_at
error

Use JSONB where appropriate.

Do not store unnecessary secrets.

Do not store API credentials.

--------------------------------------------------
STEP 14 — VERSIONING / AUDITABILITY
--------------------------------------------------

A government verification can change over time.

Therefore preserve:

- source
- provider
- verification timestamp
- identifier
- returned data
- comparison result

Do not simply overwrite historical verification information if the existing architecture supports audit records.

If the current schema already has an audit/versioning mechanism, reuse it.

Do not build a completely separate audit system in this task.

--------------------------------------------------
STEP 15 — IDEMPOTENCY
--------------------------------------------------

Do not accidentally start duplicate government verification requests.

Before processing:

check whether an identical verification is already PROCESSING.

Avoid simultaneous duplicate calls.

If the application supports explicit re-verification, allow a new verification record rather than destroying historical results.

--------------------------------------------------
STEP 16 — STATUS FLOW
--------------------------------------------------

Government verification should have its own status.

For example:

PENDING
PROCESSING
COMPLETED
FAILED

The normalized result can then be:

VERIFIED
MISMATCH
NOT_FOUND
SOURCE_ERROR

Do NOT mix:

AI_STATUS
OCR_STATUS
GOVERNMENT_VERIFICATION_STATUS
COMPLIANCE_STATUS

These are separate concepts.

--------------------------------------------------
STEP 17 — WORKER INTEGRATION
--------------------------------------------------

Integrate government verification with the existing job/worker architecture if appropriate.

The flow should be:

AI extraction completed
        ↓
Government verification job
        ↓
PROCESSING
        ↓
Provider
        ↓
Government response
        ↓
Comparison
        ↓
COMPLETED
        ↓
Store result

Do NOT trigger verification when AI extraction failed.

Do NOT call government APIs with missing identifiers.

--------------------------------------------------
STEP 18 — API
--------------------------------------------------

Expose a backend API for government verification.

Follow existing API conventions.

Conceptually:

POST /api/v1/documents/{document_id}/verify

or the equivalent existing architecture.

The endpoint should:

1. validate document
2. verify AI extraction exists
3. identify supported document type
4. queue/run verification
5. return verification status

Also provide a way to retrieve the latest verification result.

For example:

GET /api/v1/documents/{document_id}/verification

Use the project's existing API naming conventions if different.

--------------------------------------------------
STEP 19 — FRONTEND
--------------------------------------------------

Update the document UI only where necessary.

For supported documents display:

Government Verification

Example:

GST Certificate

AI Extraction
✓ Completed

Government Verification
✓ Verified

Fields:

GSTIN
Document: 29ABCDE1234F1Z5
Government: 29ABCDE1234F1Z5
Result: MATCH

Legal Name
Document: ABC TECHNOLOGIES PRIVATE LIMITED
Government: ABC TECHNOLOGIES PRIVATE LIMITED
Result: MATCH

Do NOT display:

"Bidder is compliant"

Do NOT display:

"Bidder is qualified"

Do NOT display:

"Bidder approved"

Those belong to the future compliance layer.

--------------------------------------------------
STEP 20 — MISMATCH UI
--------------------------------------------------

Test a fictional mismatch.

Example document:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
XYZ TECHNOLOGIES PRIVATE LIMITED

Government demo source:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
ABC TECHNOLOGIES PRIVATE LIMITED

The UI should clearly show:

GSTIN → MATCH

Legal Name → MISMATCH

Overall:

MISMATCH

Do not convert this into "bidder rejected."

--------------------------------------------------
STEP 21 — NOT FOUND
--------------------------------------------------

Test:

GSTIN:
29NOTFOUND1234F1

Expected:

Government source:
NOT_FOUND

Verification result:

NOT_FOUND

Do not classify this as:

COMPLIANT

or:

NON-COMPLIANT

It is simply a verification-source result.

--------------------------------------------------
STEP 22 — GOVERNMENT SOURCE ERROR
--------------------------------------------------

Simulate provider failure.

Example:

Demo provider configured to return:

UNAVAILABLE

Expected:

verification status:

FAILED / SOURCE_ERROR

The system must:

- preserve the document
- preserve OCR
- preserve AI extraction
- store the verification error safely
- allow retry if supported

Do not erase previous successful verification records.

--------------------------------------------------
STEP 23 — SECURITY
--------------------------------------------------

Government integration credentials must exist only on the backend.

Never expose:

- API keys
- access tokens
- provider credentials
- internal provider URLs if sensitive

to the frontend.

React should communicate only with the FastAPI backend.

--------------------------------------------------
STEP 24 — TESTS
--------------------------------------------------

Create tests for:

1. GovernmentProvider interface.
2. DemoGSTProvider.
3. DemoPANProvider.
4. GST found.
5. GST not found.
6. PAN found.
7. PAN not found.
8. Invalid GST format.
9. Invalid PAN format.
10. Missing identifier.
11. Government source error.
12. GST field matching.
13. GST field mismatch.
14. PAN field matching.
15. PAN field mismatch.
16. Missing document field.
17. Missing government field.
18. Verification status transitions.
19. Duplicate verification prevention.
20. Successful database storage.
21. Failed verification storage.
22. API endpoint.
23. AI extraction prerequisite.
24. Worker integration.

External APIs must be mocked.

Tests must not require real government credentials.

--------------------------------------------------
STEP 25 — END-TO-END TEST
--------------------------------------------------

Use the fictional GST document from TASK 09.

OCR:

GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED

REGISTRATION DATE:
12/04/2024

AI extraction:

{
  "gstin": "29ABCDE1234F1Z5",
  "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "registration_date": "2024-04-12"
}

Demo government source:

{
  "gstin": "29ABCDE1234F1Z5",
  "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "registration_date": "2024-04-12",
  "status": "ACTIVE"
}

Expected:

GSTIN → MATCH

Legal Name → MATCH

Registration Date → MATCH

Overall:

VERIFIED

--------------------------------------------------
STEP 26 — NEGATIVE END-TO-END TEST
--------------------------------------------------

Use:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
XYZ TECHNOLOGIES PRIVATE LIMITED

Demo government source:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
ABC TECHNOLOGIES PRIVATE LIMITED

Expected:

GSTIN → MATCH

Legal Name → MISMATCH

Overall:

MISMATCH

Do not mark the bidder as disqualified.

--------------------------------------------------
STEP 27 — PAN TEST
--------------------------------------------------

Use fictional PAN:

ABCDE1234F

Demo source:

{
  "pan": "ABCDE1234F",
  "name": "ABC TECHNOLOGIES PRIVATE LIMITED",
  "status": "ACTIVE"
}

Expected:

PAN → MATCH

Name → MATCH

Status → MATCH

Overall:

VERIFIED

--------------------------------------------------
STEP 28 — PRESERVE EXISTING FEATURES
--------------------------------------------------

After implementation verify that:

- document upload still works
- OCR still works
- AI extraction still works
- Tenders still work
- Bidders still work
- Tender Details still work
- Bidder Details still work
- Supabase connection still works

Do not break existing modules.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Only modify files directly related to:

- government integrations
- government verification
- verification storage
- verification worker jobs
- document verification API
- document verification UI
- tests
- necessary database migration

Do NOT modify:

backend/app/ocr/**

unless absolutely required to fix an integration break caused by this task.

Do NOT modify:

backend/app/verification/**

if that directory is reserved for the future Compliance Engine.

If an existing integration framework already exists, extend it rather than replacing it.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

[ ] GovernmentProvider abstraction exists
[ ] DemoGSTProvider exists
[ ] DemoPANProvider exists
[ ] Provider selection is configurable
[ ] No credentials are hardcoded
[ ] GST verification works
[ ] PAN verification works
[ ] GST NOT_FOUND works
[ ] PAN NOT_FOUND works
[ ] Source errors are handled
[ ] Identifier format validation exists
[ ] Format validity is separate from government verification
[ ] Extracted data is compared with government data
[ ] Field-level MATCH/MISMATCH results exist
[ ] Overall verification result exists
[ ] Verification status is separate from AI status
[ ] Verification status is separate from compliance status
[ ] Verification result is stored in Supabase
[ ] Verification timestamp is stored
[ ] Provider/source is stored
[ ] Historical verification is preserved where supported
[ ] Duplicate processing is prevented
[ ] Worker integration works
[ ] Verification API exists
[ ] Verification result API exists
[ ] Frontend can display verification
[ ] Mismatch is displayed correctly
[ ] NOT_FOUND is displayed correctly
[ ] Source error is displayed correctly
[ ] AI failure prevents government verification
[ ] Missing identifier prevents unnecessary API call
[ ] External APIs are mocked in tests
[ ] Automated tests pass
[ ] Manual GST verification passes
[ ] Manual GST mismatch test passes
[ ] Manual PAN verification passes
[ ] Existing OCR still works
[ ] Existing AI extraction still works
[ ] Existing tender functionality still works
[ ] Existing bidder functionality still works

--------------------------------------------------
CRITICAL RULE
--------------------------------------------------

Government verification result is NOT compliance.

For example:

VERIFIED

means:

"The supplied information matched the government source."

It does NOT mean:

"The bidder is compliant with the tender."

The future Compliance Engine will make that determination using:

Tender Requirements
+
Government Verification
+
AI Extracted Evidence
+
Documents
+
Other Verification Sources

--------------------------------------------------
STOP AFTER TASK 10
--------------------------------------------------

Do NOT implement TASK 11 automatically.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Existing integration framework reused.
3. GovernmentProvider abstraction.
4. GST provider.
5. PAN provider.
6. Demo providers.
7. Real provider status.
8. Configuration variables.
9. Verification service.
10. Comparison logic.
11. Field-level result format.
12. Overall result format.
13. Database changes.
14. Worker changes.
15. API endpoints.
16. Frontend changes.
17. Tests executed.
18. Test results.
19. Manual GST verification result.
20. GST mismatch test result.
21. PAN verification result.
22. NOT_FOUND test result.
23. Source-error test result.
24. Confirmation that no compliance logic was implemented.
25. Confirmation that existing OCR and AI functionality remains intact.

STOP.
```

---

# 🧪 What you should manually test

After the vibe coder says it's complete, don't immediately move on.

### 1. GST MATCH

Use:

```text
GSTIN: 29ABCDE1234F1Z5
Legal Name: ABC TECHNOLOGIES PRIVATE LIMITED
```

Expected:

```text
GSTIN             MATCH
Legal Name        MATCH
Registration      MATCH
Overall           VERIFIED
```

### 2. GST MISMATCH

Change only the document's extracted/demo value:

```text
Legal Name:
XYZ TECHNOLOGIES PRIVATE LIMITED
```

Expected:

```text
GSTIN             MATCH
Legal Name        MISMATCH
Overall           MISMATCH
```

**Not:**

```text
❌ Bidder rejected
❌ Non-compliant
❌ Disqualified
```

### 3. GST NOT FOUND

```text
29NOTFOUND1234F1
```

Expected:

```text
NOT_FOUND
```

### 4. PAN

```text
ABCDE1234F
```

Expected:

```text
PAN       MATCH
Name      MATCH
Status    MATCH
```

---

# 🧠 Where your architecture is now

After TASK 10, your system has a very clean separation:

```text
┌─────────────────────────────────────┐
│          DOCUMENT LAYER              │
│ Upload + Storage                     │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│             OCR LAYER                │
│ Document → Raw Text                  │
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│          AI EXTRACTION               │
│ Raw Text → Structured Information    │
└──────────────────┬──────────────────┘
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
┌───────────────┐     ┌───────────────┐
│ GST Government│     │ PAN Government│
│ Verification  │     │ Verification  │
└───────┬───────┘     └───────┬───────┘
        └──────────┬──────────┘
                   ↓
         VERIFIED / MISMATCH /
          NOT_FOUND / ERROR
                   │
                   ▼
       ┌─────────────────────────┐
       │   FUTURE COMPLIANCE     │
       │        ENGINE           │
       └─────────────────────────┘
                   │
                   ▼
          Tender Requirement
              Evaluation
                   │
                   ▼
        Officer Decision Support
```

**This separation is exactly what you want for SIH:** if a judge asks *“What happens if the AI makes a mistake?”*, you can demonstrate that AI extraction is only one evidence source, and the government verification layer independently checks the extracted identifier/data.

**TASK 11 should be the Compliance Evidence/Rule Engine foundation**—where we finally introduce tender requirements and connect `MATCH/MISMATCH/NOT_FOUND` results to individual tender clauses, while still keeping the final decision with the procurement officer.
