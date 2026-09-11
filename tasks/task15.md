# 🚀 TASK 15 — Evidence Traceability, Explainability & Audit Trail

Assuming **TASK 14 passed**, this is a very important milestone for the SIH demo.

You now have:

```text
Tender
 ↓
Approved Requirements
 ↓
Bidder
 ↓
Documents
 ↓
OCR
 ↓
AI Extraction
 ↓
Government Verification
 ↓
Compliance Engine
 ↓
PASS / FAIL / NOT_VERIFIED
```

But a procurement officer needs to ask:

> **“Why did the system give me this result?”**

TASK 15 makes every result **traceable and explainable**.

For example:

```text
GST State Requirement
        ↓
FAIL
        ↓
Rule: state == Tamil Nadu
        ↓
Government value: Karnataka
        ↓
Government Verification #123
        ↓
GST Certificate
        ↓
OCR text
        ↓
Original uploaded document
```

That's the evidence chain we want.

---

# 🎯 TASK 15 GOAL

Build a complete:

**Evidence → Decision Explanation → Audit Trail**

layer.

The system should allow an officer to go from:

```text
FAIL
```

all the way to:

```text
Original Document
```

without manually searching through the database.

---

# 📋 EXACT VIBE-CODING PROMPT

```text
TASK 15 — EVIDENCE TRACEABILITY, EXPLAINABILITY AND AUDIT TRAIL

TASK 14 has been completed successfully.

The platform currently supports:

Tender
    ↓
Approved Requirements
    ↓
Bidder
    ↓
Documents
    ↓
OCR
    ↓
AI Extraction
    ↓
Government Verification
    ↓
Compliance Evaluation
    ↓
PASS / FAIL / NOT_VERIFIED

Now implement the EVIDENCE TRACEABILITY, EXPLAINABILITY AND AUDIT TRAIL layer.

--------------------------------------------------
CORE PURPOSE
--------------------------------------------------

Every compliance result must be explainable and traceable.

A procurement officer must be able to answer:

1. What requirement was checked?
2. What rule was applied?
3. What evidence was used?
4. Which bidder document supplied the evidence?
5. What did OCR extract?
6. What did AI extract?
7. What did the government source return?
8. Which fields matched?
9. Which fields failed?
10. When was the verification performed?
11. Which evaluation produced the result?
12. Why did the requirement PASS/FAIL/NOT_VERIFIED?

The system must provide a complete evidence chain.

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

The system must never present a compliance result without being able to identify the evidence used to produce it.

Every result should be traceable:

Requirement
    ↓
Rule
    ↓
Evaluation
    ↓
Evidence
    ↓
Verification / Extraction
    ↓
Document
    ↓
Original File

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- automatic bidder approval
- automatic bidder rejection
- bid award
- procurement recommendation
- new government integrations
- new OCR
- new AI provider
- new compliance rules
- risk scoring
- predictive scoring
- automatic final procurement decisions

Reuse existing:

- OCR
- AI extraction
- Government Verification
- Compliance Engine
- Compliance Evaluation
- Tender Requirements
- Document Management

--------------------------------------------------
STEP 1 — INSPECT EXISTING STRUCTURE
--------------------------------------------------

Inspect:

backend/app/models/**
backend/app/schemas/**
backend/app/services/**
backend/app/verification/**
backend/app/integrations/**
backend/app/ai/**
backend/app/ocr/**
backend/app/api/**
backend/app/workers/**
backend/tests/**
supabase/migrations/**

Frontend:

frontend/src/pages/**
frontend/src/components/**
frontend/src/services/**

Inspect existing:

- requirement evaluation
- compliance evaluation
- evidence resolver
- government verification
- AI extraction
- OCR storage
- document metadata
- audit mechanisms

Reuse existing structures.

Do not create duplicate audit systems.

--------------------------------------------------
STEP 2 — EVIDENCE OBJECT
--------------------------------------------------

Create or standardize a normalized evidence object.

Conceptually:

{
  "evidence_id": "...",
  "source_type": "GOVERNMENT",
  "source": "GST",
  "document_id": "...",
  "verification_id": "...",
  "extraction_id": "...",
  "field": "status",
  "value": "ACTIVE",
  "retrieved_at": "..."
}

Not every evidence source will contain every field.

Use nullable references where appropriate.

--------------------------------------------------
STEP 3 — EVIDENCE TYPES
--------------------------------------------------

Support:

DOCUMENT
OCR
AI_EXTRACTION
GOVERNMENT_VERIFICATION

Future sources may include:

MANUAL_ENTRY
EXTERNAL_CERTIFICATE
OEM
OTHER

Do not implement unnecessary future sources.

--------------------------------------------------
STEP 4 — EVIDENCE CHAIN
--------------------------------------------------

The system should be able to construct:

Requirement
    ↓
Requirement Evaluation
    ↓
Evidence
    ↓
Government Verification
    ↓
Document
    ↓
OCR
    ↓
AI Extraction
    ↓
Original Storage File

Example:

Requirement:

GST Active

Evaluation:

PASS

Evidence:

GST Government Verification

Verification ID:

VER-123

Document:

DOC-123

Original file:

Supabase Storage path

--------------------------------------------------
STEP 5 — FIELD-LEVEL EVIDENCE
--------------------------------------------------

Evidence should be as specific as reasonably possible.

Example:

Requirement:

GST status == ACTIVE

Evidence:

source:
GST

field:
status

document_value:
ACTIVE

government_value:
ACTIVE

result:
MATCH

This allows the officer to understand exactly what was checked.

--------------------------------------------------
STEP 6 — EXPLANATION OBJECT
--------------------------------------------------

Create a structured explanation.

Example:

{
  "result": "PASS",
  "statement":
    "GST status returned by the verification source is ACTIVE.",
  "rule": {
    "field": "status",
    "operator": "EQUALS",
    "expected": "ACTIVE"
  },
  "actual_value": "ACTIVE",
  "evidence": [
    {
      "source": "GST",
      "verification_id": "..."
    }
  ]
}

Do not generate this explanation using an LLM.

It must be deterministic.

--------------------------------------------------
STEP 7 — EXPLANATION FOR FAIL
--------------------------------------------------

Example:

Rule:

state == Tamil Nadu

Government value:

Karnataka

Explanation:

"GST state is Karnataka, while the tender requirement specifies Tamil Nadu."

The explanation must be generated from:

rule
+
actual value
+
expected value

Do not ask AI to generate the explanation.

--------------------------------------------------
STEP 8 — EXPLANATION FOR NOT VERIFIED
--------------------------------------------------

Example:

Requirement:

GST status == ACTIVE

Evidence:

AI extraction exists.

Government verification:

missing.

Explanation:

"GST information was extracted from the submitted document, but the required government verification is unavailable."

This must clearly distinguish:

missing evidence

from:

failed evidence.

--------------------------------------------------
STEP 9 — EXPLANATION FOR SOURCE ERROR
--------------------------------------------------

Example:

Government provider unavailable.

Explanation:

"Government verification could not be completed because the verification source was unavailable."

Do not claim:

"GST is invalid."

Do not convert infrastructure failure into compliance failure.

--------------------------------------------------
STEP 10 — EVIDENCE REFERENCES
--------------------------------------------------

Every requirement evaluation should contain references to its evidence.

Example:

{
  "evaluation_id": "...",
  "requirement_id": "...",
  "result": "PASS",
  "evidence": [
    {
      "type": "GOVERNMENT_VERIFICATION",
      "verification_id": "...",
      "document_id": "..."
    }
  ]
}

--------------------------------------------------
STEP 11 — DOCUMENT TRACE
--------------------------------------------------

The officer must be able to navigate:

Compliance Result
      ↓
Evidence
      ↓
Document
      ↓
Original File

Use existing secure document access mechanisms.

Do NOT expose private Supabase storage directly.

If signed URLs already exist, reuse them.

--------------------------------------------------
STEP 12 — OCR TRACE
--------------------------------------------------

The officer should be able to view OCR text associated with the evidence.

Example:

Source Document:
GST Certificate

OCR Text:

GST CERTIFICATE

GSTIN: 29ABCDE1234F1Z5

LEGAL NAME:
ABC TECHNOLOGIES PRIVATE LIMITED

REGISTRATION DATE:
12/04/2024

Do not modify OCR processing.

Only expose existing OCR results.

--------------------------------------------------
STEP 13 — AI EXTRACTION TRACE
--------------------------------------------------

The officer should be able to view:

AI Extracted Information

Example:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
ABC TECHNOLOGIES PRIVATE LIMITED

Registration Date:
2024-04-12

The UI must clearly label this:

AI Extracted

not:

Government Verified

--------------------------------------------------
STEP 14 — GOVERNMENT TRACE
--------------------------------------------------

Show:

Government Verification

Source:
GST

Provider:
Demo

Status:
FOUND

Identifier:
29ABCDE1234F1Z5

Retrieved:

timestamp

Data:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
ABC TECHNOLOGIES PRIVATE LIMITED

Status:
ACTIVE

State:
Tamil Nadu

--------------------------------------------------
STEP 15 — EVIDENCE COMPARISON
--------------------------------------------------

For fields where both document and government values exist:

show:

Field

Document

Government

Result

Example:

GSTIN

29ABCDE1234F1Z5

29ABCDE1234F1Z5

MATCH

Legal Name

ABC TECHNOLOGIES PRIVATE LIMITED

ABC TECHNOLOGIES PRIVATE LIMITED

MATCH

State

Tamil Nadu

Tamil Nadu

MATCH

--------------------------------------------------
STEP 16 — CONFLICT DISPLAY
--------------------------------------------------

If:

AI:

ACTIVE

Government:

CANCELLED

show:

AI Extracted:
ACTIVE

Government:
CANCELLED

Government verification takes precedence where the requirement requires government verification.

The conflict must remain visible.

Do not overwrite AI evidence.

--------------------------------------------------
STEP 17 — EVALUATION HISTORY
--------------------------------------------------

For each compliance evaluation show:

Evaluation ID
Tender
Bidder
Started
Completed
Status

Example:

Evaluation:

EVAL-001

Tender:

CPCL Demo Tender

Bidder:

ABC Technologies

Status:

COMPLETED

Timestamp:

2026-09-11 10:30

--------------------------------------------------
STEP 18 — REQUIREMENT HISTORY
--------------------------------------------------

For each requirement result show:

Requirement
Rule
Result
Evidence
Evaluation timestamp

If a requirement was evaluated again:

show the new evaluation separately.

Do not overwrite previous evidence.

--------------------------------------------------
STEP 19 — AUDIT EVENT
--------------------------------------------------

Reuse any existing audit mechanism.

If no audit mechanism exists, introduce a minimal audit_events structure.

Possible fields:

id
entity_type
entity_id
action
actor
metadata
created_at

Examples:

REQUIREMENT_APPROVED
COMPLIANCE_EVALUATION_STARTED
COMPLIANCE_EVALUATION_COMPLETED
GOVERNMENT_VERIFICATION_COMPLETED

Do not create a giant generic event system.

Only implement events directly useful for auditability.

--------------------------------------------------
STEP 20 — ACTOR
--------------------------------------------------

If the current application already has authentication/users:

record the user responsible for:

- requirement approval
- manual edits
- evaluation initiation
- other auditable actions

If authentication does not yet exist:

use the existing placeholder mechanism.

Do NOT implement a complete authentication system in this task.

--------------------------------------------------
STEP 21 — AUDIT IMMUTABILITY
--------------------------------------------------

Audit events should not be casually edited through normal CRUD APIs.

Do not provide a normal:

PATCH /audit-event

endpoint.

Historical audit events should be append-oriented.

--------------------------------------------------
STEP 22 — AUDIT API
--------------------------------------------------

Create/read APIs following existing conventions.

Conceptually:

GET /api/v1/compliance/evaluations/{evaluation_id}/evidence

Returns all evidence.

GET /api/v1/compliance/evaluations/{evaluation_id}/audit

Returns relevant audit events.

GET /api/v1/requirements/{requirement_id}/evidence

Returns evidence used by requirement evaluations.

Use existing naming conventions if different.

--------------------------------------------------
STEP 23 — EVIDENCE DETAIL API
--------------------------------------------------

Provide a detailed evidence endpoint where appropriate.

Conceptually:

GET /api/v1/evidence/{evidence_id}

Return:

source
source_type
document
OCR
AI extraction
government verification
field
value
timestamp

Do not expose private credentials or storage internals.

--------------------------------------------------
STEP 24 — FRONTEND COMPLIANCE REPORT
--------------------------------------------------

Enhance the existing compliance report.

Example:

COMPLIANCE REPORT

ABC TECHNOLOGIES PRIVATE LIMITED

------------------------------------

GST Registration

✓ PASS

Rule:
GST status = ACTIVE

Actual:
ACTIVE

Evidence:
GST Government Verification

[View Evidence]

------------------------------------

Tamil Nadu Registration

✗ FAIL

Rule:
GST state = Tamil Nadu

Actual:
Karnataka

Evidence:
GST Government Verification

[View Evidence]

------------------------------------

PAN

✓ PASS

Rule:
PAN status = ACTIVE

Evidence:
PAN Government Verification

[View Evidence]

--------------------------------------------------
STEP 25 — EVIDENCE DRAWER / PAGE
--------------------------------------------------

When the officer clicks:

[View Evidence]

show:

Evidence Details

Source:
GST Government Verification

Status:
FOUND

Identifier:
29ABCDE1234F1Z5

------------------------------------

Document

GST Certificate.pdf

[View Document]

------------------------------------

AI Extraction

GSTIN:
29ABCDE1234F1Z5

Legal Name:
ABC TECHNOLOGIES PRIVATE LIMITED

------------------------------------

Government Data

GSTIN:
29ABCDE1234F1Z5

Status:
ACTIVE

State:
Tamil Nadu

------------------------------------

Comparison

GSTIN → MATCH
Legal Name → MATCH
Status → MATCH

------------------------------------

OCR Text

[View OCR Text]

--------------------------------------------------
STEP 26 — ORIGINAL DOCUMENT ACCESS
--------------------------------------------------

If the user clicks:

[View Document]

use the existing secure signed URL mechanism.

Do NOT expose:

private bucket paths

service-role credentials

Supabase access tokens

Do not make the storage bucket public.

--------------------------------------------------
STEP 27 — OCR VIEW
--------------------------------------------------

Add:

[View OCR Text]

This should display the stored OCR text.

Do not rerun OCR.

Do not call AI.

--------------------------------------------------
STEP 28 — AI EXTRACTION VIEW
--------------------------------------------------

Add:

[View AI Extraction]

Show structured extracted fields.

Clearly label:

AI EXTRACTED

Do not use wording:

VERIFIED

unless it refers specifically to government verification.

--------------------------------------------------
STEP 29 — GOVERNMENT DATA VIEW
--------------------------------------------------

Show government response separately.

Clearly label:

GOVERNMENT VERIFICATION

If provider is demo:

DEMO PROVIDER

Do not hide this distinction.

--------------------------------------------------
STEP 30 — EVIDENCE TIMELINE
--------------------------------------------------

Where useful, provide a simple timeline:

Document Uploaded
       ↓
OCR Completed
       ↓
AI Extraction Completed
       ↓
Government Verification Completed
       ↓
Compliance Evaluated

Show timestamps if available.

Do not create excessive animation.

--------------------------------------------------
STEP 31 — AUDIT PAGE
--------------------------------------------------

Create/update an audit view.

Example:

AUDIT TRAIL

10:30
Requirement approved
Active GST Registration

10:32
GST verification completed
Source: Demo GST Provider

10:33
Compliance evaluation started

10:33
GST requirement evaluated
PASS

10:34
Compliance evaluation completed

Each event should link to the relevant entity where practical.

--------------------------------------------------
STEP 32 — NO FAKE AUDIT EVENTS
--------------------------------------------------

Do not generate fake audit events simply to make the demo look active.

Events must correspond to actual operations.

Demo seed data may have clearly identified demo history if already present.

--------------------------------------------------
STEP 33 — AUDIT FILTERING
--------------------------------------------------

If practical, allow filtering by:

- tender
- bidder
- evaluation
- requirement
- event type
- date

Do not build a complex analytics system.

Basic filtering is enough.

--------------------------------------------------
STEP 34 — DATA CONSISTENCY
--------------------------------------------------

Ensure evidence references remain valid.

If:

requirement evaluation references verification_id

that verification must exist.

If:

verification references document_id

that document must exist.

Do not allow orphaned evidence references.

--------------------------------------------------
STEP 35 — DELETION SAFETY
--------------------------------------------------

Do not allow deletion of a document that would silently destroy historical compliance evidence.

If existing document deletion exists:

protect documents referenced by:

- verification
- evaluation
- audit

Use archive/deactivation if appropriate.

Do not implement destructive cascading deletion of audit evidence.

--------------------------------------------------
STEP 36 — EVIDENCE SNAPSHOT
--------------------------------------------------

For historical evaluations, preserve enough information to understand what was evaluated at the time.

If the existing architecture already stores government response JSON and evaluation results:

reuse it.

Do not rely solely on a mutable pointer to current government data.

Example:

Evaluation 001:

GST status:
ACTIVE

Later:

Government status:
CANCELLED

Evaluation 001 should still show:

ACTIVE

because that was the evidence used at evaluation time.

--------------------------------------------------
STEP 37 — EXPLANATION DETERMINISM
--------------------------------------------------

Run the same evaluation twice with the same evidence.

The explanation must remain the same.

Do not use an LLM to generate explanations.

Do not generate random language.

--------------------------------------------------
STEP 38 — SECURITY
--------------------------------------------------

Verify:

- only authorized users can view sensitive documents
- signed URLs are used where required
- private storage remains private
- API keys remain backend-only
- audit events cannot be edited normally
- users cannot access another bidder's evidence
- users cannot access another tender's evidence
- evaluation relationships are validated

--------------------------------------------------
STEP 39 — TEST: PASS TRACE
--------------------------------------------------

Create:

Requirement:

GST status == ACTIVE

Evidence:

Government GST:

ACTIVE

Expected:

PASS

Then follow:

PASS
 ↓
Evidence
 ↓
Verification
 ↓
Document
 ↓
OCR
 ↓
AI extraction
 ↓
Original file

Every step must resolve correctly.

--------------------------------------------------
STEP 40 — TEST: FAIL TRACE
--------------------------------------------------

Requirement:

GST state == Tamil Nadu

Government:

Karnataka

Expected:

FAIL

Explanation:

GST state is Karnataka while the requirement specifies Tamil Nadu.

Evidence must link to:

GST verification.

--------------------------------------------------
STEP 41 — TEST: NOT VERIFIED TRACE
--------------------------------------------------

Requirement:

GST status == ACTIVE

AI extraction exists.

Government verification does not exist.

Expected:

NOT_VERIFIED

Evidence should show:

AI extraction available

Government verification unavailable.

--------------------------------------------------
STEP 42 — TEST: HISTORY
--------------------------------------------------

Evaluation 1:

GST status:
ACTIVE

Result:

PASS

Change government demo data:

CANCELLED

Evaluation 2:

Result:

FAIL

Verify:

Evaluation 1 remains PASS.

Evaluation 2 is FAIL.

Historical evidence is preserved.

--------------------------------------------------
STEP 43 — TEST: AUDIT
--------------------------------------------------

Perform:

Approve requirement

Run government verification

Run compliance evaluation

Verify audit events exist for these operations.

--------------------------------------------------
STEP 44 — TEST: SECURITY
--------------------------------------------------

Attempt to access:

- another bidder's evidence
- another tender's requirement
- another evaluation's document

Expected:

controlled authorization error.

--------------------------------------------------
STEP 45 — FRONTEND UX
--------------------------------------------------

Keep the design:

minimal
government portal style
clear
dense but readable

Use:

green → PASS
red → FAIL
orange → NOT_VERIFIED / pending
blue → information/evidence links

Do not introduce:

- excessive gradients
- glassmorphism
- large animations
- unnecessary charts

--------------------------------------------------
STEP 46 — TESTING
--------------------------------------------------

Create tests for:

1. Evidence object.
2. Evidence reference.
3. Evidence chain.
4. PASS explanation.
5. FAIL explanation.
6. NOT_VERIFIED explanation.
7. SOURCE_ERROR explanation.
8. Document trace.
9. OCR trace.
10. AI extraction trace.
11. Government verification trace.
12. Evidence conflict.
13. Evaluation history.
14. Evidence snapshot.
15. Audit event creation.
16. Audit event retrieval.
17. Audit immutability.
18. Evidence API.
19. Audit API.
20. Authorization.
21. Orphan evidence prevention.
22. Historical evaluation preservation.
23. Deterministic explanations.
24. Signed document access.

External APIs must remain mocked.

--------------------------------------------------
STEP 47 — FULL END-TO-END TEST
--------------------------------------------------

Use fictional bidder:

ABC TECHNOLOGIES PRIVATE LIMITED

Requirement:

Active GST Registration

Rule:

GST status == ACTIVE

Document:

GST Certificate

OCR:

GSTIN:
29ABCDE1234F1Z5

Legal Name:
ABC TECHNOLOGIES PRIVATE LIMITED

AI:

GSTIN:
29ABCDE1234F1Z5

Government:

GSTIN:
29ABCDE1234F1Z5

Status:
ACTIVE

Run compliance evaluation.

Expected:

PASS

Then click:

View Evidence

Verify complete trace:

PASS
 ↓
Rule
 ↓
Government Verification
 ↓
GST Certificate
 ↓
AI Extraction
 ↓
OCR
 ↓
Original Document

--------------------------------------------------
STEP 48 — FULL FAILURE TEST
--------------------------------------------------

Use:

Requirement:

GST state == Tamil Nadu

Government:

state = Karnataka

Run evaluation.

Expected:

FAIL

Click:

View Evidence

Verify:

Rule:
state == Tamil Nadu

Actual:
Karnataka

Source:
GST Government Verification

Document:
GST Certificate

--------------------------------------------------
STEP 49 — PRESERVE EXISTING FEATURES
--------------------------------------------------

Verify:

- Tender list
- Tender Details
- Bidder list
- Bidder Details
- Documents
- OCR
- AI Extraction
- GST verification
- PAN verification
- Udyam verification
- other demo providers
- Tender Requirements
- Compliance Engine
- Compliance Evaluation
- Supabase

continue working.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Allowed:

backend/app/models/**
backend/app/schemas/**
backend/app/services/**
backend/app/verification/**
backend/app/api/**
backend/app/workers/**
backend/tests/**
supabase/migrations/**

Frontend:

frontend/src/pages/**
frontend/src/components/**
frontend/src/services/**

Modify integration/AI/OCR files only if absolutely required for traceability interfaces.

Do NOT rewrite:

backend/app/ocr/**

Do NOT rewrite:

backend/app/ai/**

Do NOT rewrite:

backend/app/integrations/**

Do NOT rewrite the core ComplianceEngine.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

[ ] Normalized evidence object exists
[ ] Evidence types exist
[ ] Evidence chain is traceable
[ ] Requirement → evaluation link exists
[ ] Evaluation → evidence link exists
[ ] Evidence → verification link exists
[ ] Verification → document link exists
[ ] Document → OCR link exists
[ ] Document → AI extraction link exists
[ ] Original document can be securely opened
[ ] OCR can be viewed
[ ] AI extraction can be viewed
[ ] Government data can be viewed
[ ] Field comparisons can be viewed
[ ] PASS explanation is deterministic
[ ] FAIL explanation is deterministic
[ ] NOT_VERIFIED explanation is deterministic
[ ] SOURCE_ERROR explanation is deterministic
[ ] Evidence conflicts remain visible
[ ] Evaluation history is preserved
[ ] Evidence snapshots are preserved
[ ] Audit events exist
[ ] Audit events are append-oriented
[ ] Audit API exists
[ ] Evidence API exists
[ ] Authorization checks exist
[ ] Orphan evidence is prevented
[ ] Destructive evidence deletion is prevented
[ ] Signed document access works
[ ] Compliance report has View Evidence
[ ] Evidence detail UI works
[ ] OCR detail UI works
[ ] AI detail UI works
[ ] Government verification detail UI works
[ ] Audit trail UI works
[ ] Demo sources are clearly marked
[ ] No AI-generated explanations
[ ] No automatic bidder approval
[ ] No automatic bidder rejection
[ ] No procurement recommendation
[ ] Tests pass
[ ] PASS trace test passes
[ ] FAIL trace test passes
[ ] NOT_VERIFIED trace test passes
[ ] Historical evaluation test passes
[ ] Audit test passes
[ ] Security test passes
[ ] Existing functionality remains intact

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

Every compliance result must answer:

WHAT was checked?
        ↓
WHAT rule was used?
        ↓
WHAT evidence was used?
        ↓
WHERE did the evidence come from?
        ↓
WHAT values were compared?
        ↓
WHY did it PASS/FAIL/NOT_VERIFIED?
        ↓
WHEN was this evaluated?

The system must make this information available to the procurement officer.

--------------------------------------------------
STOP AFTER TASK 15
--------------------------------------------------

Do NOT implement TASK 16 automatically.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Evidence model.
3. Evidence types.
4. Evidence chain.
5. Explanation system.
6. PASS explanation.
7. FAIL explanation.
8. NOT_VERIFIED explanation.
9. SOURCE_ERROR explanation.
10. Document trace.
11. OCR trace.
12. AI trace.
13. Government verification trace.
14. Evidence conflict handling.
15. Evaluation history.
16. Evidence snapshot behavior.
17. Audit events.
18. Audit APIs.
19. Evidence APIs.
20. Security checks.
21. Frontend changes.
22. Tests executed.
23. PASS trace result.
24. FAIL trace result.
25. NOT_VERIFIED trace result.
26. Historical evaluation result.
27. Audit result.
28. Security test result.
29. Confirmation no AI-generated compliance explanations exist.
30. Confirmation no automatic bidder decision exists.
31. Confirmation existing functionality remains intact.

STOP.
```

---

# 🧪 Your most important manual test

Don't just check whether the UI says **PASS**.

Click through the entire chain.

Start here:

```text
GST Registration
      ↓
     PASS
```

Click **View Evidence**.

You should be able to reach:

```text
PASS
 ↓
Requirement
 ↓
Rule:
status == ACTIVE
 ↓
Government Verification
 ↓
GSTIN
29ABCDE1234F1Z5
 ↓
Status
ACTIVE
 ↓
GST Certificate
 ↓
AI Extraction
 ↓
OCR Text
 ↓
Original PDF
```

If you can demonstrate this smoothly, that's a **very strong SIH demo feature**.

---

# 🔥 Second critical test: historical evidence

Run evaluation #1:

```text
GST status = ACTIVE
→ PASS
```

Then change demo government data:

```text
ACTIVE → CANCELLED
```

Run evaluation #2:

```text
GST status = CANCELLED
→ FAIL
```

Now open **Evaluation #1** again.

It should **still say PASS**.

You don't want:

```text
Old evaluation
   ↓
reads today's government data
   ↓
FAIL
```

You want:

```text
Evaluation #1
   ↓
Evidence snapshot at T1
   ↓
ACTIVE
   ↓
PASS

Evaluation #2
   ↓
Evidence snapshot at T2
   ↓
CANCELLED
   ↓
FAIL
```

That's the foundation of a proper procurement audit trail.

---

# 🧠 Architecture after TASK 15

Your platform now looks like this:

```text
                         TENDER
                            │
                            ▼
                   TENDER REQUIREMENTS
                            │
                     AI SUGGESTION
                            │
                     OFFICER APPROVAL
                            │
                            ▼
                  APPROVED REQUIREMENTS
                            │
                            │
                            ▼
BIDDER ─────────► COMPLIANCE ORCHESTRATOR
 │                          │
 │                          ▼
 │                   EVIDENCE RESOLVER
 │                          │
 ├── DOCUMENT               │
 │     ↓                    │
 │    OCR                   │
 │     ↓                    │
 │    AI                    │
 │     ↓                    │
 │  EXTRACTED DATA ─────────┤
 │                          │
 └── GOVERNMENT             │
       VERIFICATION ────────┘
                            │
                            ▼
                   COMPLIANCE ENGINE
                            │
                            ▼
                  REQUIREMENT RESULT
                            │
                            ▼
                    EXPLANATION
                            │
                            ▼
                    EVIDENCE TRACE
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          DOCUMENT         OCR       GOVERNMENT
              │             │        VERIFICATION
              ▼             ▼             │
          ORIGINAL        TEXT            │
           FILE                            │
              └─────────────┬──────────────┘
                            ▼
                       AUDIT TRAIL
```

At this stage, you've built the **core evidence architecture** of the platform.

The next major milestone should be **TASK 16 — Realistic Tender & Bidder Workflow / Bulk Evaluation**, where instead of testing one bidder against one requirement, the platform evaluates **multiple bidders against the same tender simultaneously** and gives the procurement officer a side-by-side compliance matrix.
