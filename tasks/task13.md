# 🚀 TASK 13 — Multi-Source Compliance Pipeline & Verification Orchestration

Assuming **TASK 12 passed**, we now have all the foundational pieces:

```text
Tender Document
      ↓
AI Requirement Extraction
      ↓
Officer Approval
      ↓
Approved Tender Requirements
      ↓
Compliance Engine
      ↑
      │
AI Extracted Bidder Evidence
      ↑
      │
Government Verification
```

But right now these pieces are still somewhat independent.

**TASK 13 connects them into one orchestrated bidder-evaluation pipeline.**

The goal is that a procurement officer can select:

```text
Tender A
+
Bidder B
```

and the system can determine:

```text
What requirements apply?
        ↓
What evidence is available?
        ↓
What evidence needs verification?
        ↓
Evaluate every approved requirement
        ↓
Produce one complete compliance report
```

⚠️ **Still no automatic final bidder decision.**

---

# 📋 EXACT VIBE-CODING PROMPT

```text
TASK 13 — MULTI-SOURCE COMPLIANCE PIPELINE AND VERIFICATION ORCHESTRATION

TASK 12 has been completed successfully.

The application currently supports:

Tender
    ↓
Tender Documents
    ↓
AI Requirement Extraction
    ↓
Officer Review
    ↓
Approved Tender Requirements

Bidder
    ↓
Bidder Documents
    ↓
OCR
    ↓
AI Extraction
    ↓
Government Verification

Compliance Engine
    ↓
Requirement-level PASS / FAIL / NOT_VERIFIED

Now connect these components into a single orchestrated compliance evaluation pipeline.

--------------------------------------------------
CORE PURPOSE
--------------------------------------------------

The procurement officer should be able to select:

Tender
+
Bidder

and run a complete compliance evaluation.

The system should:

1. Load the tender.
2. Load APPROVED requirements.
3. Load the selected bidder.
4. Discover available bidder evidence.
5. Use existing AI extraction results.
6. Use existing government verification results.
7. Determine whether sufficient evidence exists.
8. Evaluate every approved requirement.
9. Store requirement-level results.
10. Produce a complete compliance evaluation report.

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

This task creates ORCHESTRATION.

It does NOT replace:

- OCR
- AI extraction
- Government verification
- Compliance Engine
- Tender requirements

The orchestrator coordinates them.

It should NOT duplicate their logic.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- automatic bidder approval
- automatic bidder rejection
- automatic disqualification
- bid award
- procurement recommendation
- risk scoring
- government API integrations
- new OCR implementation
- new AI provider
- new government provider
- new rule engine
- tender requirement extraction
- officer final decision

Reuse existing components.

--------------------------------------------------
TARGET ARCHITECTURE
--------------------------------------------------

The desired architecture is:

                    TENDER
                       │
                       ▼
              APPROVED REQUIREMENTS
                       │
                       ▼
                    BIDDER
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Documents    AI Evidence   Gov Evidence
          │            │            │
          └────────────┼────────────┘
                       ▼
              Evidence Resolver
                       │
                       ▼
              Compliance Engine
                       │
                       ▼
          Requirement Evaluations
                       │
                       ▼
             Compliance Report
```

---

## STEP 1 — INSPECT EXISTING STRUCTURE

Inspect:

backend/app/verification/**
backend/app/services/**
backend/app/models/**
backend/app/schemas/**
backend/app/api/**
backend/app/workers/**
backend/app/ai/**
backend/app/integrations/**

Also inspect:

* existing ComplianceEngine
* existing GovernmentVerificationService
* existing AI extraction service
* existing tender requirements
* existing bidder documents
* existing requirement evaluations
* existing database migrations
* existing API conventions

Reuse existing implementations.

Do not create duplicates.

---

## STEP 2 — COMPLIANCE EVALUATION SESSION

Introduce a concept representing one complete evaluation:

Tender + Bidder + approved requirements + evidence.

Conceptually:

ComplianceEvaluation

Fields may include:

evaluation_id
tender_id
bidder_id
status
summary
started_at
completed_at
created_at

Possible statuses:

PENDING
PROCESSING
COMPLETED
FAILED

Do not confuse this with requirement result.

---

## STEP 3 — EVALUATION ID

Every full evaluation should have a unique ID.

Example:

evaluation_id:

UUID

Requirement-level results should reference:

evaluation_id

This allows the system to answer:

"Which evaluation produced this result?"

---

## STEP 4 — EVIDENCE RESOLVER

Create an EvidenceResolver.

Its responsibility:

Given:

tender requirement
+
bidder

find the evidence that can satisfy that requirement.

Example:

Requirement:

GST status == ACTIVE

EvidenceResolver searches for:

1. bidder GST document
2. AI extraction
3. GST government verification

Then produces normalized evidence for the ComplianceEngine.

---

## STEP 5 — DO NOT CALL PROVIDERS FROM RULE ENGINE

The ComplianceEngine must remain deterministic.

The orchestrator/EvidenceResolver may determine that verification is missing.

But the ComplianceEngine itself must NOT:

* call GST API
* call PAN API
* call AI
* run OCR

It only receives evidence.

---

## STEP 6 — EVIDENCE PRIORITY

When evaluating a requirement, prefer stronger evidence.

For GST:

Government verified data should be preferred over AI-only extraction.

Conceptually:

Government Verification
↓
AI Extraction
↓
Raw Document

Do not invent evidence.

If government verification exists:

use it.

If only AI extraction exists:

the requirement may become:

NOT_VERIFIED

depending on the requirement's evidence policy.

---

## STEP 7 — EVIDENCE POLICY

Requirements should be able to specify what evidence is required.

For example:

{
"source": "GST",
"required_verification": true
}

Meaning:

AI extraction alone is insufficient.

Another requirement could allow:

{
"source": "DOCUMENT",
"required_verification": false
}

Do not create an unnecessarily complicated policy engine.

Implement only the minimum required abstraction.

---

## STEP 8 — REQUIREMENT EVALUATION

For every APPROVED requirement:

1. Resolve evidence.
2. Check evidence sufficiency.
3. Pass evidence to ComplianceEngine.
4. Receive result.
5. Store requirement evaluation.

Example:

Requirement 1:
GST ACTIVE

Evidence:
GST government verification

Result:
PASS

Requirement 2:
Tamil Nadu GST

Evidence:
GST government verification

Result:
PASS

Requirement 3:
Active PAN

Evidence:
PAN government verification

Result:
PASS

---

## STEP 9 — MULTIPLE REQUIREMENTS

The orchestrator must evaluate ALL approved requirements.

Do not stop after the first failure.

Example:

8 requirements

Results:

5 PASS
1 FAIL
2 NOT_VERIFIED

All eight results must be retained.

---

## STEP 10 — REQUIREMENT ORDER

Use requirement display_order if available.

Results should be returned in deterministic order.

This makes the UI predictable.

---

## STEP 11 — EVALUATION SUMMARY

Generate a deterministic summary.

Example:

{
"total": 8,
"passed": 5,
"failed": 1,
"not_verified": 2,
"partial": 0,
"not_applicable": 0
}

Do not use AI to generate this summary.

Calculate it directly from requirement results.

---

## STEP 12 — MANDATORY REQUIREMENTS

Each requirement has:

mandatory = true/false

The report should distinguish:

Mandatory requirements
Optional requirements

Example:

Mandatory:
6

Optional:
2

Passed mandatory:
5

Failed mandatory:
1

Do NOT convert this into an automatic bidder decision.

---

## STEP 13 — OVERALL EVALUATION STATUS

The complete evaluation may have a status such as:

COMPLETED

while the result summary contains:

PASS
FAIL
NOT_VERIFIED

Do not introduce:

BIDDER_APPROVED

or:

BIDDER_REJECTED

as automatic statuses.

The evaluation represents an assessment, not a procurement decision.

---

## STEP 14 — BLOCKED EVALUATION

If there are no approved requirements:

return:

NO_APPROVED_REQUIREMENTS

Do not silently report:

PASS

If the bidder has no evidence:

requirements may return:

NOT_VERIFIED

depending on the requirement.

---

## STEP 15 — MISSING DOCUMENT HANDLING

Example:

Requirement:

GST ACTIVE

Bidder:

No GST document

No GST verification

Expected:

NOT_VERIFIED

The system should explain:

"Required GST evidence is unavailable."

Do not invent GST information.

---

## STEP 16 — AI-ONLY EVIDENCE

Example:

GST document exists.

AI extraction:

GSTIN = 29ABCDE1234F1Z5

Government verification:

none

If requirement requires government verification:

Expected:

NOT_VERIFIED

Explanation:

"GST information was extracted from the document but government verification is unavailable."

This distinction is important.

---

## STEP 17 — GOVERNMENT VERIFIED EVIDENCE

Example:

AI extraction:

GSTIN = 29ABCDE1234F1Z5

Government verification:

VERIFIED

Government status:

ACTIVE

Requirement:

status == ACTIVE

Expected:

PASS

---

## STEP 18 — GOVERNMENT MISMATCH

Example:

AI extraction:

GST legal name:
XYZ TECHNOLOGIES PRIVATE LIMITED

Government:

ABC TECHNOLOGIES PRIVATE LIMITED

Government verification:

MISMATCH

The requirement should use the verification result appropriately.

Expected:

FAIL or NOT_VERIFIED according to the specific rule semantics.

Do not hide the mismatch.

The explanation must show the evidence conflict.

---

## STEP 19 — EVIDENCE CONFLICT

If AI extraction says:

GST status:
ACTIVE

Government verification says:

status:
CANCELLED

Government evidence should take precedence for requirements requiring government verification.

Expected:

Requirement:

GST ACTIVE

Result:

FAIL

Explanation should make the conflict traceable.

Do not overwrite the AI extraction.

Both pieces of evidence must remain available.

---

## STEP 20 — EVIDENCE TRACE

Every requirement result should reference:

evaluation_id
requirement_id
bidder_id
tender_id
document_id where applicable
verification_id where applicable
source

Example:

{
"evaluation_id": "...",
"requirement_id": "...",
"status": "PASS",
"evidence": [
{
"source": "GST_GOVERNMENT",
"document_id": "...",
"verification_id": "..."
}
]
}

---

## STEP 21 — FULL REPORT API

Create an API following existing conventions.

Conceptually:

POST /api/v1/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluate

Returns:

evaluation_id
status

Then:

GET /api/v1/compliance/evaluations/{evaluation_id}

Returns:

tender
bidder
summary
requirements
evidence
timestamps

Use existing API conventions if different.

---

## STEP 22 — EVALUATION HISTORY

A bidder may be evaluated multiple times.

Do NOT overwrite all previous evaluations.

Create a new evaluation ID for a new run.

Example:

Evaluation 001:
GST ACTIVE
PASS

Later government data changes.

Evaluation 002:
GST ACTIVE
FAIL

Both should remain auditable.

---

## STEP 23 — RE-EVALUATION

Allow a new evaluation to be created after:

* new document upload
* new AI extraction
* new government verification
* requirement change
* officer-triggered re-evaluation

Do not silently modify the previous evaluation.

---

## STEP 24 — WORKER / ASYNC SUPPORT

Use the existing worker architecture if full evaluation may take time.

Possible flow:

POST evaluate
↓
create evaluation
↓
PROCESSING
↓
resolve evidence
↓
evaluate requirements
↓
store results
↓
COMPLETED

Do not create another worker system.

---

## STEP 25 — PARALLELIZATION

Where safe, independent requirement evaluations may be processed concurrently.

For example:

GST requirement
PAN requirement
Document requirement

may be evaluated independently.

However:

Do NOT parallelize operations that depend on one another.

Do NOT create duplicate government API requests.

Do NOT sacrifice deterministic behavior for unnecessary concurrency.

Use the project's existing async architecture.

---

## STEP 26 — FRONTEND COMPLIANCE REPORT

Create/update a compliance report view.

Example:

COMPLIANCE REPORT

Tender:
CPCL Demo Tender

Bidder:
ABC Technologies Pvt Ltd

---

SUMMARY

8 Requirements

5 PASS
1 FAIL
2 NOT VERIFIED

---

MANDATORY REQUIREMENTS

Active GST Registration
✓ PASS

Tamil Nadu Registration
✗ FAIL

Active PAN
✓ PASS

MSME Registration
⚠ NOT VERIFIED

---

EVIDENCE

GST Government Verification
Verified

GST Certificate
Available

PAN Government Verification
Verified

---

IMPORTANT:

Do NOT display:

"Bidder Approved"

"Bidder Rejected"

"Bid Award Recommended"

Instead display:

"Compliance assessment completed."

---

## STEP 27 — REQUIREMENT DETAIL

Clicking a requirement should show:

Requirement
Rule
Result
Document evidence
AI extraction
Government verification
Explanation
Timestamp

Example:

Requirement:

Active GST Registration

Rule:

status == ACTIVE

Result:

PASS

Evidence:

GST Certificate
GST Government Verification

Government value:

ACTIVE

Expected:

ACTIVE

Explanation:

"GST status returned by the government source is ACTIVE."

---

## STEP 28 — NOT VERIFIED UI

For:

NOT_VERIFIED

display:

"Verification evidence unavailable."

If AI-only evidence exists:

"Information was extracted from the submitted document, but required government verification is unavailable."

Do not display:

"FAIL"

unless the deterministic requirement evaluation actually fails.

---

## STEP 29 — EVALUATION TRIGGER

On the bidder/tender interface provide:

[ Run Compliance Evaluation ]

Before running:

ensure tender exists
ensure bidder exists
ensure approved requirements exist

If no approved requirements:

show:

"No approved tender requirements are available."

---

## STEP 30 — DEMO DATA

Use the existing fictional tender and bidder.

Do not create duplicate entities.

Ensure the demo tender has:

1. Active GST Registration
2. Tamil Nadu GST Registration
3. Active PAN

Use existing demo verification data.

---

## STEP 31 — DEMO FULL PASS

Given:

GST government:

status = ACTIVE
state = Tamil Nadu

PAN government:

status = ACTIVE

Approved requirements:

GST status = ACTIVE
GST state = Tamil Nadu
PAN status = ACTIVE

Expected:

3 PASS

Summary:

{
"total": 3,
"passed": 3,
"failed": 0,
"not_verified": 0
}

---

## STEP 32 — DEMO PARTIAL FAILURE

Change GST state:

Karnataka

Expected:

GST status requirement:
PASS

Tamil Nadu requirement:
FAIL

PAN:
PASS

Summary:

3 total
2 PASS
1 FAIL

The bidder must NOT automatically be rejected.

---

## STEP 33 — DEMO NOT VERIFIED

Remove/disable GST government verification.

Keep AI extracted GST data.

Expected:

GST requirement requiring government verification:

NOT_VERIFIED

Explanation:

"Required government GST verification is unavailable."

---

## STEP 34 — DEMO EVIDENCE CONFLICT

AI:

GST status = ACTIVE

Government:

GST status = CANCELLED

Expected:

Government verification takes precedence.

Requirement:

GST status == ACTIVE

Result:

FAIL

Both AI and government evidence remain visible.

---

## STEP 35 — TESTING

Create tests for:

1. ComplianceEvaluation creation.
2. Evaluation ID generation.
3. Approved requirement loading.
4. Unapproved requirements ignored.
5. EvidenceResolver.
6. GST evidence resolution.
7. PAN evidence resolution.
8. Missing evidence.
9. AI-only evidence.
10. Government verified evidence.
11. Government mismatch.
12. Evidence conflict.
13. Requirement evaluation.
14. Multiple requirements.
15. Summary generation.
16. Mandatory/optional counts.
17. Evaluation history.
18. Re-evaluation.
19. Evidence references.
20. API.
21. Worker.
22. No approved requirements.
23. Deterministic explanations.
24. Existing ComplianceEngine integration.

External APIs must be mocked.

---

## STEP 36 — SECURITY

Ensure users cannot evaluate:

* arbitrary bidder IDs against arbitrary tender IDs
* requirements belonging to another tender
* evidence belonging to another bidder

The backend must validate relationships:

Tender
↓
Requirement

Bidder
↓
Document

Document
↓
Verification

Evaluation
↓
Tender + Bidder

Do not rely only on frontend filtering.

---

## STEP 37 — AUDITABILITY

A completed evaluation must be traceable:

Evaluation
↓
Tender
↓
Approved Requirement
↓
Requirement Evaluation
↓
Evidence
├── Document
├── AI Extraction
└── Government Verification

A procurement officer should eventually be able to answer:

"Why did this requirement pass?"

and:

"Which evidence was used?"

---

## STEP 38 — MANUAL TEST

Select:

Demo Tender

and:

Demo Bidder.

Click:

Run Compliance Evaluation

Expected:

Evaluation created.

Status:

PROCESSING

then:

COMPLETED

Report appears.

Example:

Active GST:
PASS

Tamil Nadu:
PASS

Active PAN:
PASS

---

## STEP 39 — MANUAL FAILURE TEST

Change demo government GST state:

Tamil Nadu
→
Karnataka

Run a NEW evaluation.

Expected:

Previous evaluation remains unchanged.

New evaluation:

Active GST:
PASS

Tamil Nadu:
FAIL

PAN:
PASS

This proves evaluation history works.

---

## STEP 40 — MANUAL NOT VERIFIED TEST

Remove/disable GST government verification.

Run a NEW evaluation.

Expected:

GST requirement:

NOT_VERIFIED

Previous evaluation remains unchanged.

---

## STEP 41 — FINAL DECISION SAFETY

Search the codebase after implementation for automatic final decision logic.

There must NOT be logic such as:

if failed_requirements:
bidder.status = "REJECTED"

or:

if all_pass:
bidder.status = "APPROVED"

or:

if compliance_score >= threshold:
award_bid()

Remove any such logic introduced by this task.

The output is an assessment only.

---

## STEP 42 — PRESERVE EXISTING FEATURES

Verify:

* Tenders
* Tender Details
* Bidders
* Bidder Details
* Document Upload
* OCR
* AI Extraction
* GST Verification
* PAN Verification
* Tender Requirements
* Compliance Engine
* Supabase

all continue to work.

---

## FILES RESTRICTION

Allowed:

backend/app/verification/**
backend/app/services/**
backend/app/models/**
backend/app/schemas/**
backend/app/api/**
backend/app/workers/**
backend/tests/**

frontend/src/pages/**
frontend/src/components/**
frontend/src/services/**

supabase/migrations/**

Modify AI/integration files only if an interface integration is unavoidable.

Do NOT rewrite:

backend/app/ocr/**

Do NOT rewrite:

backend/app/ai/**

Do NOT rewrite:

backend/app/integrations/**

Do NOT rewrite the core ComplianceEngine.

Extend existing architecture.

---

## DEFINITION OF DONE

[ ] ComplianceEvaluation exists
[ ] Evaluation ID exists
[ ] Evaluation status exists
[ ] EvidenceResolver exists
[ ] Approved requirements are loaded
[ ] Unapproved requirements are ignored
[ ] Evidence is resolved correctly
[ ] Government evidence has appropriate priority
[ ] AI-only evidence is handled
[ ] Missing evidence is handled
[ ] Evidence conflicts are handled
[ ] ComplianceEngine is reused
[ ] Every approved requirement is evaluated
[ ] Evaluation summary exists
[ ] Mandatory/optional counts exist
[ ] Requirement results reference evidence
[ ] Evaluation history is preserved
[ ] Re-evaluation creates a new evaluation
[ ] API exists
[ ] Frontend report exists
[ ] Requirement detail exists
[ ] NOT_VERIFIED is displayed correctly
[ ] PASS is displayed correctly
[ ] FAIL is displayed correctly
[ ] No automatic bidder approval exists
[ ] No automatic bidder rejection exists
[ ] No award recommendation exists
[ ] Security relationships are validated
[ ] Audit trail is traceable
[ ] Tests pass
[ ] Full PASS test passes
[ ] Partial failure test passes
[ ] NOT_VERIFIED test passes
[ ] Evidence conflict test passes
[ ] Existing functionality remains intact

---

## CRITICAL ARCHITECTURAL PRINCIPLE

The system now has:

1. DOCUMENT PROCESSING

Document
→ OCR
→ AI extraction

2. GOVERNMENT VERIFICATION

Extracted identifier
→ Government source
→ Verification

3. REQUIREMENT MANAGEMENT

Tender
→ AI suggestions
→ Officer approval
→ Approved requirement

4. COMPLIANCE ENGINE

Approved requirement
+
Evidence
→ Requirement result

5. COMPLIANCE ORCHESTRATOR

Tender
+
Bidder
+
Approved requirements
+
Evidence
→ Complete assessment

6. PROCUREMENT OFFICER

Complete assessment
→ Final human decision

The sixth layer must remain human-controlled.

---

## STOP AFTER TASK 13

Do NOT implement TASK 14 automatically.

---

## FINAL REPORT

Report:

1. Files modified.
2. ComplianceEvaluation model.
3. Evaluation lifecycle.
4. EvidenceResolver.
5. Evidence priority logic.
6. AI-only evidence behavior.
7. Government evidence behavior.
8. Evidence conflict behavior.
9. Requirement evaluation orchestration.
10. Summary calculation.
11. Evaluation history.
12. Re-evaluation behavior.
13. API endpoints.
14. Frontend report.
15. Requirement detail view.
16. Worker integration.
17. Security checks.
18. Auditability.
19. Tests executed.
20. Full PASS test result.
21. Partial FAIL test result.
22. NOT_VERIFIED test result.
23. Evidence conflict test result.
24. Confirmation no automatic bidder approval/rejection exists.
25. Confirmation no award recommendation exists.
26. Confirmation existing OCR, AI, government verification and Compliance Engine remain intact.

STOP.

````

---

# 🧪 Your manual testing sequence

After the vibe coder finishes, test it in this exact order.

### 1️⃣ Full pass

Use:

```text
GST = ACTIVE
State = Tamil Nadu
PAN = ACTIVE
````

Run:

**Compliance Evaluation**

Expected:

```text
3 Requirements
───────────────
GST Active       ✅ PASS
Tamil Nadu GST   ✅ PASS
PAN Active       ✅ PASS
```

---

### 2️⃣ Change one government value

Change:

```text
Tamil Nadu
     ↓
Karnataka
```

**Do not rerun the old evaluation.**

Run a **new** evaluation.

Expected:

```text
Old Evaluation
GST Active       PASS
Tamil Nadu       PASS
PAN              PASS

New Evaluation
GST Active       PASS
Tamil Nadu       FAIL
PAN              PASS
```

🔥 This proves you're preserving an **audit history**, rather than rewriting the past.

---

### 3️⃣ Remove government evidence

Keep:

```text
AI GST extraction = available
```

but:

```text
GST government verification = unavailable
```

Run another evaluation.

Expected:

```text
GST requirement → NOT_VERIFIED
```

This is an important distinction:

```text
AI knows something
       ≠
Government verified it
```

---

### 4️⃣ Test evidence conflict

Make:

```text
AI:
GST status = ACTIVE

Government:
GST status = CANCELLED
```

Then run evaluation.

For a requirement:

```text
GST status == ACTIVE
```

expected:

```text
❌ FAIL
```

while the report should still allow the officer to see:

```text
AI extracted:
ACTIVE

Government:
CANCELLED
```

Nothing should be silently overwritten.

---

# 🧠 Architecture after TASK 13

This is a **big milestone**:

```text
                       TENDER
                         │
                         ▼
                 TENDER DOCUMENT
                         │
                         ▼
                REQUIREMENT AI
                         │
                         ▼
                 OFFICER APPROVAL
                         │
                         ▼
              APPROVED REQUIREMENTS
                         │
                         │
                         ▼
BIDDER ───────► COMPLIANCE ORCHESTRATOR
 │                       │
 ├── Documents           │
 │     ↓                 │
 │    OCR                │
 │     ↓                 │
 │    AI                 │
 │     ↓                 │
 │  Extraction           │
 │                       │
 └── Government ─────────┘
       Verification
              │
              ▼
        EVIDENCE RESOLVER
              │
              ▼
       COMPLIANCE ENGINE
              │
              ▼
       ┌───────────────┐
       │ Requirement   │
       │ Results       │
       └───────┬───────┘
               ▼
       COMPLETE REPORT
               │
               ▼
      PROCUREMENT OFFICER
               │
               ▼
        FINAL DECISION
```

At this point, your system is no longer just a collection of CRUD pages and individual verification demos. You have the beginnings of the **actual end-to-end procurement evaluation workflow**.

**TASK 14 should focus on expanding the evidence sources beyond GST/PAN—starting with Udyam/MSME and the mock integrations for EPFO, ESIC, Startup India, NSIC, Make in India, OEM authorization, etc.—using the same provider architecture rather than creating separate one-off systems.**
