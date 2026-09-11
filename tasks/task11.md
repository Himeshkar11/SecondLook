# 🚀 TASK 11 — Compliance Evidence & Rule Engine Foundation

Assuming **TASK 10 passed**, we now reach the core of the SIH solution.

Until now, the system can answer:

```text
Document → OCR
OCR → AI extracted information
Extracted GSTIN → Government verification
```

Now we need to answer:

> **What does this verification mean for a specific tender requirement?**

For example:

```text
Tender Requirement:
"Bidder must have an active GST registration."

        ↓

GST Government Verification:
GSTIN → VERIFIED
Status → ACTIVE

        ↓

Requirement Evaluation:
PASS
```

But another tender could say:

```text
"Bidder must be registered in Tamil Nadu."
```

Then the same GST response needs a different rule:

```text
GST State = Tamil Nadu
        ↓
PASS
```

So we're introducing the **Compliance Engine**, but only its foundation in this task.

---

# 🎯 TASK 11 GOAL

Build:

```text
Tender
  ↓
Tender Requirements
  ↓
Evidence
  ↓
Rule Evaluation
  ↓
Requirement Result
```

The engine should produce:

```text
PASS
FAIL
PARTIAL
NOT_VERIFIED
NOT_APPLICABLE
```

But **it must NOT make the final bidder decision**.

The distinction is:

```text
Requirement Result
        ↓
Compliance Engine

Final Bidder Decision
        ↓
Procurement Officer
```

---

# 📋 Exact vibe-coding prompt

```text
TASK 11 — COMPLIANCE EVIDENCE AND RULE ENGINE FOUNDATION

TASK 10 has been completed successfully.

The application currently supports:

Document Upload
      ↓
Supabase Storage
      ↓
OCR
      ↓
AI Extraction
      ↓
Structured Information
      ↓
Government Verification
      ↓
MATCH / MISMATCH / NOT_FOUND / ERROR

Now implement the FOUNDATION OF THE COMPLIANCE ENGINE.

--------------------------------------------------
CORE PURPOSE
--------------------------------------------------

The Compliance Engine connects:

1. Tender requirements
2. Extracted document information
3. Government verification results
4. Deterministic compliance rules

and produces a requirement-level result.

Example:

Tender Requirement:

"Bidder must have an active GST registration."

Evidence:

GST verification:
VERIFIED

Government GST status:
ACTIVE

Result:

PASS

--------------------------------------------------
CRITICAL ARCHITECTURAL RULE
--------------------------------------------------

The Compliance Engine evaluates REQUIREMENTS.

It does NOT make the final procurement decision.

The engine may say:

Requirement 1 → PASS
Requirement 2 → FAIL
Requirement 3 → NOT_VERIFIED

It must NOT say:

"Bidder is awarded."

"Bidder is approved."

"Bidder is disqualified."

"Bidder should win."

The final decision remains with the Procurement Officer.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- automatic bid award
- automatic bidder rejection
- final qualification
- final disqualification
- procurement officer decision
- AI-based compliance decisions
- risk scoring
- recommendation to award
- government API integrations
- OCR
- AI extraction
- GST provider
- PAN provider
- Udyam verification
- EPFO verification
- ESIC verification
- MCA verification
- Startup India verification
- NSIC verification
- DigiLocker verification
- blacklisting verification

Reuse TASK 10 verification results.

--------------------------------------------------
STEP 1 — INSPECT EXISTING STRUCTURE
--------------------------------------------------

Before modifying anything inspect:

backend/app/
backend/app/models/
backend/app/schemas/
backend/app/services/
backend/app/api/
backend/app/verification/
backend/tests/
supabase/migrations/

Also inspect:

- tender model
- tender detail model
- bidder model
- document model
- AI extraction model
- government verification model
- existing verification directory
- existing demo tender data
- existing database migrations

Do NOT create duplicate models or services.

--------------------------------------------------
STEP 2 — TENDER REQUIREMENTS
--------------------------------------------------

A tender needs individual compliance requirements.

Conceptually:

Tender
   │
   ├── Requirement 1
   ├── Requirement 2
   ├── Requirement 3
   └── Requirement 4

Each requirement should have:

- requirement_id
- tender_id
- requirement_code
- title
- description
- requirement_type
- rule_type
- parameters
- mandatory
- display_order
- created_at

Use the project's existing schema conventions.

--------------------------------------------------
STEP 3 — REQUIREMENT TYPES
--------------------------------------------------

Create a controlled set of requirement types.

At minimum support:

GST
PAN
UDYAM
DOCUMENT
TEXT
NUMERIC
DATE
OTHER

Do not implement full verification for every type.

Only GST and PAN need working evidence evaluation initially.

The others should exist so the architecture can expand later.

--------------------------------------------------
STEP 4 — RULE TYPES
--------------------------------------------------

Create a controlled set of deterministic rule types.

At minimum support:

IDENTIFIER_MATCH
STATUS_EQUALS
FIELD_EQUALS
FIELD_EXISTS
FIELD_NOT_EMPTY

Examples:

GST status must equal ACTIVE:

rule_type:
STATUS_EQUALS

field:
status

expected:
ACTIVE

Another:

GST state must equal Tamil Nadu:

rule_type:
FIELD_EQUALS

field:
state

expected:
Tamil Nadu

Another:

GSTIN must exist:

rule_type:
FIELD_EXISTS

field:
gstin

--------------------------------------------------
STEP 5 — RULE CONFIGURATION
--------------------------------------------------

Rules must NOT be hardcoded directly into API endpoints.

Store rule configuration as structured data.

Example:

{
  "source": "GST",
  "field": "status",
  "operator": "EQUALS",
  "expected_value": "ACTIVE"
}

Another:

{
  "source": "GST",
  "field": "state",
  "operator": "EQUALS",
  "expected_value": "Tamil Nadu"
}

This allows future tender requirements to have different rules.

--------------------------------------------------
STEP 6 — COMPLIANCE ENGINE INTERFACE
--------------------------------------------------

Create a clean service interface.

Conceptually:

ComplianceEngine

    evaluate_requirement(
        requirement,
        evidence
    )

returns:

RequirementEvaluation

Do not put this logic into:

- React
- API routes
- database repositories
- government providers

The rule engine should be independently testable.

--------------------------------------------------
STEP 7 — EVIDENCE MODEL
--------------------------------------------------

The Compliance Engine must consume existing evidence.

Evidence can come from:

1. AI extracted information
2. Government verification
3. Document metadata
4. Future verification providers

For TASK 11, prioritize:

Government Verification
AI Extraction

Do NOT re-run OCR or AI inside the Compliance Engine.

Do NOT call government APIs directly from the Compliance Engine.

--------------------------------------------------
STEP 8 — EVIDENCE ADAPTER
--------------------------------------------------

Create an internal normalized evidence representation.

Conceptually:

{
  "source": "GST",
  "identifier": "29ABCDE1234F1Z5",
  "verified": true,
  "data": {
    "gstin": "29ABCDE1234F1Z5",
    "legal_name": "ABC TECHNOLOGIES PRIVATE LIMITED",
    "status": "ACTIVE",
    "state": "Tamil Nadu"
  }
}

The engine should consume this normalized structure rather than knowing how Supabase or an external API works.

--------------------------------------------------
STEP 9 — REQUIREMENT EVALUATION STATES
--------------------------------------------------

Use controlled requirement evaluation states.

At minimum:

PASS
FAIL
PARTIAL
NOT_VERIFIED
NOT_APPLICABLE

Meaning:

PASS:
Required evidence exists and rule passed.

FAIL:
Required evidence exists and rule failed.

PARTIAL:
Some rule conditions passed but others could not be satisfied.

NOT_VERIFIED:
Required evidence does not currently have sufficient verification.

NOT_APPLICABLE:
Requirement does not apply to this bidder/document context.

Do not confuse:

NOT_VERIFIED

with:

FAIL

A missing government response is not automatically proof of non-compliance.

--------------------------------------------------
STEP 10 — RULE EVALUATION
--------------------------------------------------

Implement deterministic rule evaluation.

Example:

Rule:

status == ACTIVE

Evidence:

status = ACTIVE

Result:

PASS

Evidence:

status = CANCELLED

Result:

FAIL

Evidence:

status = null

Result:

NOT_VERIFIED

Do not use an LLM to evaluate deterministic rules.

--------------------------------------------------
STEP 11 — MULTIPLE RULES
--------------------------------------------------

A requirement may contain multiple conditions.

Example:

"Bidder must have active GST registration in Tamil Nadu."

Conditions:

status == ACTIVE

AND

state == Tamil Nadu

If:

ACTIVE + Tamil Nadu:

PASS

ACTIVE + Karnataka:

FAIL

INACTIVE + Tamil Nadu:

FAIL

Missing state:

NOT_VERIFIED

Use deterministic AND semantics.

If the project needs OR conditions later, keep the architecture extensible but do not over-engineer it now.

--------------------------------------------------
STEP 12 — FIELD NORMALIZATION
--------------------------------------------------

Before comparing values:

- trim whitespace
- normalize case for textual equality
- normalize repeated spaces
- normalize dates where appropriate

Example:

"ACTIVE"

and:

" active "

should compare as equal for a case-insensitive textual rule.

Do not use AI or fuzzy matching for deterministic compliance rules.

--------------------------------------------------
STEP 13 — IDENTIFIER MATCH
--------------------------------------------------

For IDENTIFIER_MATCH:

Compare the extracted identifier with the verified government identifier.

Example:

Document:

29ABCDE1234F1Z5

Government:

29ABCDE1234F1Z5

Result:

PASS

If:

Document:

29ABCDE1234F1Z5

Government:

29XYZDE1234F1Z5

Result:

FAIL

Do not attempt fuzzy matching for identifiers.

Identifiers must match exactly after safe normalization.

--------------------------------------------------
STEP 14 — REQUIREMENT RESULT
--------------------------------------------------

Return a structured result.

Example:

{
  "requirement_id": "...",
  "status": "PASS",
  "mandatory": true,
  "rule_results": [
    {
      "rule": "STATUS_EQUALS",
      "field": "status",
      "expected": "ACTIVE",
      "actual": "ACTIVE",
      "status": "PASS"
    }
  ],
  "evidence": [
    {
      "source": "GST",
      "verification_id": "...",
      "document_id": "..."
    }
  ]
}

The result should be explainable.

A procurement officer should be able to understand:

WHAT was checked
AGAINST WHAT
USING WHICH EVIDENCE
WHY it passed/failed

--------------------------------------------------
STEP 15 — EXPLANATION
--------------------------------------------------

Every evaluation should contain a deterministic explanation.

Example:

"GST status is ACTIVE and matches the tender requirement."

Or:

"GST state is Karnataka but the tender requires Tamil Nadu."

Or:

"GST government verification is not available."

Do not ask an LLM to generate the explanation.

Generate explanations from the rule evaluation itself.

--------------------------------------------------
STEP 16 — EVIDENCE REFERENCES
--------------------------------------------------

Requirement results should reference their evidence.

For example:

requirement
    ↓
verification_id
    ↓
document_id
    ↓
original document

This is important for auditability.

A procurement officer should eventually be able to trace:

Requirement
   ↓
Result
   ↓
Government Verification
   ↓
Document
   ↓
Original file

--------------------------------------------------
STEP 17 — DATABASE
--------------------------------------------------

Add database structures necessary for:

Tender Requirements
Requirement Rules if needed
Requirement Evaluations

Do not create unnecessary duplication.

A reasonable conceptual structure is:

tender_requirements

- id
- tender_id
- code
- title
- description
- type
- mandatory
- display_order
- created_at

Rules may either be stored inside a JSONB configuration field or a separate table depending on the existing architecture.

For evaluation results:

requirement_evaluations

- id
- requirement_id
- bidder_id
- status
- result
- evidence
- evaluated_at

Use JSONB for structured rule results/evidence where appropriate.

--------------------------------------------------
STEP 18 — PRESERVE AUDITABILITY
--------------------------------------------------

Do not overwrite the only copy of an old evaluation if the existing architecture supports historical records.

Store:

- requirement
- bidder
- evidence reference
- evaluation result
- timestamp

A later government verification may change.

Therefore the system should be able to determine which evidence was used for an evaluation.

--------------------------------------------------
STEP 19 — API
--------------------------------------------------

Create APIs following existing project conventions.

Conceptually:

GET /api/v1/tenders/{tender_id}/requirements

Returns requirements.

POST /api/v1/tenders/{tender_id}/requirements

Creates a requirement if the existing application supports tender administration.

GET /api/v1/bidders/{bidder_id}/compliance

Returns requirement-level compliance results where applicable.

POST /api/v1/bidders/{bidder_id}/compliance/evaluate

Triggers evaluation for the bidder against the relevant tender.

If tender_id is required by the existing architecture, include it explicitly.

Do not allow the API to make final award/rejection decisions.

--------------------------------------------------
STEP 20 — FRONTEND
--------------------------------------------------

Add a simple Compliance section to the appropriate tender/bidder UI.

Do NOT redesign the application.

Example:

Compliance Verification

--------------------------------------------

GST Registration
Mandatory

✓ PASS

GST Status:
ACTIVE

Required:
ACTIVE

Evidence:
GST Certificate
Government Verification

--------------------------------------------

GST State
Mandatory

✗ FAIL

Detected:
Karnataka

Required:
Tamil Nadu

Evidence:
GST Government Verification

--------------------------------------------

Do not show:

"Bidder rejected"

Instead show:

"Requirement failed"

The procurement officer makes the final decision.

--------------------------------------------------
STEP 21 — REQUIREMENT SUMMARY
--------------------------------------------------

The UI may show:

Requirements:

8 total

5 PASS
1 FAIL
2 NOT_VERIFIED

But do NOT convert this into:

"Bidder rejected"

or:

"Bidder approved"

The summary is informational.

--------------------------------------------------
STEP 22 — DEMO REQUIREMENTS
--------------------------------------------------

Create deterministic demo requirements for an existing fictional tender.

Example:

REQ-GST-001

Title:
Active GST Registration

Rule:

GST status == ACTIVE

Mandatory:
true

REQ-GST-002

Title:
Tamil Nadu GST Registration

Rule:

GST state == Tamil Nadu

Mandatory:
true

REQ-PAN-001

Title:
Valid PAN

Rule:

PAN status == ACTIVE

Mandatory:
true

Use existing demo tender IDs and bidders where possible.

Do not create duplicate demo data if equivalent data already exists.

--------------------------------------------------
STEP 23 — DEMO PASS
--------------------------------------------------

Use:

GST:

status = ACTIVE

state = Tamil Nadu

PAN:

status = ACTIVE

Expected:

REQ-GST-001 → PASS

REQ-GST-002 → PASS

REQ-PAN-001 → PASS

--------------------------------------------------
STEP 24 — DEMO FAILURE
--------------------------------------------------

Use a fictional government response:

GST:

status = ACTIVE

state = Karnataka

Expected:

REQ-GST-001 → PASS

REQ-GST-002 → FAIL

Do not mark the bidder as globally failed.

Only the specific requirement fails.

--------------------------------------------------
STEP 25 — NOT VERIFIED
--------------------------------------------------

Simulate:

GST government provider:

NOT_FOUND

Expected:

REQ-GST-001 → NOT_VERIFIED

Do NOT automatically convert it into:

FAIL

unless the specific rule semantics explicitly require a verified source and the architecture documents that behavior.

Keep:

source verification result

separate from:

requirement evaluation.

--------------------------------------------------
STEP 26 — MULTIPLE REQUIREMENTS
--------------------------------------------------

Test one bidder against multiple requirements.

Example:

GST active:
PASS

GST state:
PASS

PAN active:
PASS

Expected:

3 independent requirement results.

The engine must not stop after the first result.

--------------------------------------------------
STEP 27 — TESTING
--------------------------------------------------

Create unit tests for:

1. ComplianceEngine interface.
2. STATUS_EQUALS.
3. FIELD_EQUALS.
4. FIELD_EXISTS.
5. IDENTIFIER_MATCH.
6. MATCH result.
7. MISMATCH result.
8. Missing evidence.
9. NOT_VERIFIED result.
10. Multiple AND conditions.
11. Text normalization.
12. Case normalization.
13. Identifier exact matching.
14. Requirement with multiple rules.
15. Evidence reference.
16. Deterministic explanation.
17. Requirement evaluation storage.
18. Multiple bidders.
19. Multiple requirements.
20. API response.
21. Government verification prerequisite.
22. AI extraction prerequisite where applicable.

Tests must not call real government APIs.

--------------------------------------------------
STEP 28 — NEGATIVE TEST
--------------------------------------------------

Test:

Requirement:

GST status == ACTIVE

Evidence:

GST status == CANCELLED

Expected:

FAIL

Explanation:

GST status is CANCELLED but the requirement requires ACTIVE.

Do NOT return:

NOT_VERIFIED

because verified evidence exists and contradicts the rule.

--------------------------------------------------
STEP 29 — MISSING EVIDENCE TEST
--------------------------------------------------

Requirement:

GST status == ACTIVE

Evidence:

No government verification.

Expected:

NOT_VERIFIED

Do not invent:

ACTIVE

Do not call the government provider from inside the rule engine.

--------------------------------------------------
STEP 30 — AUDIT TEST
--------------------------------------------------

After evaluating:

REQ-GST-001

verify the result contains a traceable evidence reference.

Expected chain:

Requirement
   ↓
Evaluation
   ↓
Verification ID
   ↓
Document ID
   ↓
Original document

This will become important for the final audit trail.

--------------------------------------------------
STEP 31 — MANUAL TEST
--------------------------------------------------

Open a fictional tender.

Ensure requirements are displayed.

Select a fictional bidder.

Run compliance evaluation.

Expected:

GST Registration
PASS

GST State
PASS

PAN
PASS

Now change the demo government data so GST state becomes:

Karnataka

Run evaluation again.

Expected:

GST Registration
PASS

GST State
FAIL

PAN
PASS

The UI must NOT say:

"Bidder rejected."

--------------------------------------------------
STEP 32 — PRESERVE EXISTING FEATURES
--------------------------------------------------

Verify:

- document upload works
- OCR works
- AI extraction works
- government verification works
- tenders work
- bidders work
- tender details work
- bidder details work
- Supabase works

Do not break existing modules.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Primary files allowed:

backend/app/verification/**
backend/app/models/**
backend/app/schemas/**
backend/app/services/**
backend/app/api/**
backend/tests/**
supabase/migrations/**

Frontend:

frontend/src/pages/**
frontend/src/components/**
frontend/src/services/**

Only modify files directly related to compliance requirements/evaluation.

Do NOT modify:

backend/app/ocr/**
backend/app/ai/**
backend/app/integrations/**

unless an unavoidable interface integration issue exists.

Do not rewrite existing government providers.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

[ ] Tender requirements exist
[ ] Requirements are associated with tenders
[ ] Requirement rules are structured
[ ] ComplianceEngine exists
[ ] Evidence abstraction exists
[ ] Government verification can be consumed as evidence
[ ] AI extraction can be referenced as evidence
[ ] STATUS_EQUALS works
[ ] FIELD_EQUALS works
[ ] FIELD_EXISTS works
[ ] IDENTIFIER_MATCH works
[ ] Multiple AND conditions work
[ ] PASS works
[ ] FAIL works
[ ] PARTIAL works where applicable
[ ] NOT_VERIFIED works
[ ] NOT_APPLICABLE works
[ ] Text normalization works
[ ] Identifier comparison is exact
[ ] Deterministic explanations exist
[ ] Evidence references exist
[ ] Requirement evaluations are stored
[ ] Evaluation timestamp is stored
[ ] Historical evidence is preserved where supported
[ ] API exists
[ ] Frontend displays requirement results
[ ] PASS is displayed correctly
[ ] FAIL is displayed correctly
[ ] NOT_VERIFIED is displayed correctly
[ ] No automatic bidder rejection exists
[ ] No automatic bidder approval exists
[ ] No award decision exists
[ ] No LLM is used for deterministic rule evaluation
[ ] Government APIs are not called directly from the rule engine
[ ] Tests pass
[ ] Manual PASS test passes
[ ] Manual FAIL test passes
[ ] Manual NOT_VERIFIED test passes
[ ] Existing OCR works
[ ] Existing AI extraction works
[ ] Existing government verification works
[ ] Existing tender functionality works
[ ] Existing bidder functionality works

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

The system now has three different layers:

LAYER 1 — EXTRACTION

"What does the document say?"

LAYER 2 — VERIFICATION

"Does the extracted information match the government source?"

LAYER 3 — COMPLIANCE

"Does the verified evidence satisfy this tender requirement?"

Do NOT combine these layers.

And there is a fourth layer that is NOT being implemented yet:

LAYER 4 — PROCUREMENT OFFICER DECISION

"Based on all evidence, what should be done with this bid?"

The application must never automatically make that final decision.

--------------------------------------------------
STOP AFTER TASK 11
--------------------------------------------------

Do NOT implement TASK 12 automatically.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Database changes.
3. Tender requirement structure.
4. Rule structure.
5. ComplianceEngine structure.
6. Evidence structure.
7. Supported rule types.
8. Requirement status values.
9. Evaluation result format.
10. Evidence traceability.
11. API endpoints.
12. Frontend changes.
13. Demo requirements.
14. Tests executed.
15. Test results.
16. PASS test result.
17. FAIL test result.
18. NOT_VERIFIED test result.
19. Audit/evidence trace test.
20. Confirmation that no automatic bidder decision exists.
21. Confirmation that no government provider was moved into the rule engine.
22. Confirmation that OCR and AI extraction remain unchanged.

STOP.
```

---

## 🧪 Your three manual tests

Once the agent finishes, test these in order.

### Test A — Everything passes

```text
GST status = ACTIVE
GST state = Tamil Nadu
PAN status = ACTIVE
```

Expected:

| Requirement    | Result |
| -------------- | ------ |
| Active GST     | ✅ PASS |
| Tamil Nadu GST | ✅ PASS |
| Active PAN     | ✅ PASS |

---

### Test B — One requirement fails

Change only:

```text
GST state = Karnataka
```

Expected:

| Requirement    | Result |
| -------------- | ------ |
| Active GST     | ✅ PASS |
| Tamil Nadu GST | ❌ FAIL |
| Active PAN     | ✅ PASS |

The **bidder itself should not become "rejected."**

---

### Test C — Government source unavailable

Make the provider return:

```text
NOT_FOUND
```

Expected:

```text
GST Requirement
        ↓
NOT_VERIFIED
```

Not:

```text
FAIL
```

This distinction is going to matter enormously when you eventually have multiple government sources.

---

# 🧠 Architecture after TASK 11

You now have the complete basic evidence chain:

```text
                         BIDDER
                            │
                            ▼
                       DOCUMENT
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
            OCR                         STORAGE
             │
             ▼
        OCR TEXT
             │
             ▼
       AI EXTRACTION
             │
             ▼
      STRUCTURED DATA
             │
             ▼
    GOVERNMENT VERIFICATION
             │
             ▼
       VERIFIED EVIDENCE
             │
             ▼
     ┌────────────────────┐
     │  COMPLIANCE ENGINE │
     └─────────┬──────────┘
               │
               ▼
      TENDER REQUIREMENTS
               │
               ▼
       ┌────────────────┐
       │ PASS / FAIL /  │
       │ NOT VERIFIED   │
       └───────┬────────┘
               │
               ▼
       PROCUREMENT OFFICER
```

### 🔥 The important milestone

Before TASK 11, you had a system that could **verify pieces of information**.

After TASK 11, you have a system that can say:

> **“This particular tender requirement passed/failed, and here is the exact evidence used to reach that result.”**

That is a much stronger SIH architecture because it makes the eventual dashboard, audit trail, and explainability possible without putting everything into one giant AI prompt.

**TASK 12 should build the Tender Requirement Management layer**—creating/parsing actual tender requirements and associating them with individual bidders, so the Compliance Engine isn't limited to manually seeded demo rules.
