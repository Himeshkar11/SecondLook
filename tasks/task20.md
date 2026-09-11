# 🚀 TASK 20 — Complete End-to-End Procurement Workflow

Assuming **TASK 19** is completed successfully, TASK 20 should now connect the major modules into **one complete working workflow**.

This is a major milestone: instead of testing each subsystem separately, we prove that a procurement officer can start with a tender and reach a complete, auditable bid-compliance review.

---

# 🎯 Objective

Build and verify this complete flow:

```text
                    TENDER
                      │
          ┌───────────┴───────────┐
          │                       │
   Tender Documents            Bidders
          │                       │
          ↓                       ↓
         OCR                 Bidder Documents
          │                       │
          ↓                       ↓
   AI Requirement            OCR + AI
     Extraction                  │
          │                       ↓
          ↓                Government Verification
   AI Suggestions                 │
          │                       ↓
          ↓                    Evidence
   Officer Approval                │
          │                       │
          └───────────┬───────────┘
                      ↓
              Compliance Engine
                      ↓
             Compliance Evaluation
                      ↓
                Evidence
                      ↓
              Officer Review
                      ↓
             Tender Dashboard
                      ↓
             AUDIT TRAIL
```

The goal is **integration**, not creating another subsystem.

---

# 🚨 Critical principle

TASK 20 should **not introduce new business logic**.

All major functionality already exists:

```text
TASK 07 → Documents
TASK 08 → OCR
TASK 09 → AI extraction
TASK 10 → Government verification
TASK 11 → Compliance engine
TASK 12 → Tender requirements
TASK 13 → Orchestration
TASK 14 → Government providers
TASK 15 → Evidence/audit
TASK 16 → Officer review
TASK 17 → Tender dashboard
TASK 18 → Requirement approval
TASK 19 → Tender document processing
```

TASK 20 simply connects them.

---

# 🏗️ STEP 1 — Define the Golden Demo Workflow

Create one deterministic demo scenario.

Use:

```text
Tender:
Industrial Equipment Procurement

Bidder:
ABC Technologies Pvt Ltd
```

Tender requirements:

```text
1. Valid GST registration
2. Valid PAN
3. UDYAM registration
4. Active EPFO registration
5. Active ESIC registration
6. Startup India registration
7. Valid NSIC registration
8. Minimum 50% local content
9. Valid OEM authorization
10. Bidder must not be blacklisted
```

The exact number may be adjusted to match existing demo data, but **do not create a second incompatible demo-data system**.

---

# 📁 STEP 2 — Integration Test Structure

Create/reuse:

```text id="0xg2a7"
backend/
└── tests/
    └── integration/
        ├── __init__.py
        ├── test_tender_workflow.py
        ├── test_bidder_workflow.py
        └── test_compliance_workflow.py
```

Frontend:

```text id="n3s6br"
frontend/
└── src/
    └── pages/
        └── TenderWorkflowPage.jsx
```

Only create the page if the current architecture does not already have an appropriate workflow page.

---

# 🔄 STEP 3 — Workflow State

Create a high-level read-only workflow status.

Example:

```json id="3rj8p2"
{
  "tender_id": "tender-001",
  "stages": {
    "tender_created": "COMPLETED",
    "documents_uploaded": "COMPLETED",
    "ocr": "COMPLETED",
    "requirement_extraction": "COMPLETED",
    "requirements_approved": "COMPLETED",
    "bidder_documents": "COMPLETED",
    "government_verification": "COMPLETED",
    "compliance_evaluation": "COMPLETED",
    "officer_review": "IN_PROGRESS"
  }
}
```

This is **workflow visibility**, not a second processing engine.

---

# 🧭 STEP 4 — Workflow Timeline

Create a visual timeline:

```text id="e9j3xu"
Tender Evaluation Workflow

✓ Tender Created
       ↓
✓ Tender Documents Uploaded
       ↓
✓ OCR Completed
       ↓
✓ AI Requirements Extracted
       ↓
✓ Requirements Approved
       ↓
✓ Bidder Documents Processed
       ↓
✓ Government Verification Completed
       ↓
✓ Compliance Evaluation Completed
       ↓
⟳ Officer Review
       ↓
○ Review Completed
```

This should make the entire system understandable during an SIH demo.

---

# 🔗 STEP 5 — Connect Tender Documents

From the workflow:

```text id="p8k1o7"
Tender Documents
      ↓
Processing
      ↓
OCR
      ↓
AI Requirements
```

Verify the existing TASK 19 pipeline is being used.

Do not create another upload/process endpoint.

---

# 🔗 STEP 6 — Connect Approved Requirements

After AI extraction:

```text id="5d0j8s"
AI_SUGGESTED
      ↓
Officer Review
      ↓
APPROVED
```

Verify only approved requirements enter the compliance pipeline.

This is one of the most important integration checks.

---

# 🔗 STEP 7 — Connect Bidder Documents

For:

```text id="j4h1z5"
ABC Technologies
```

upload demo documents:

```text
PAN
GST
UDYAM
EPFO
ESIC
Startup India
NSIC
Make in India
OEM Authorization
```

Do not require every source to have a real government API.

Use the demo providers established in TASK 10/14.

---

# 🔗 STEP 8 — Bidder Document Processing

Verify:

```text id="f6v9s4"
Bidder Document
      ↓
Storage
      ↓
OCR
      ↓
AI Extraction
```

For example:

```text id="s5f9i8"
GST Certificate
      ↓
OCR
      ↓
GSTIN extracted
      ↓
AI JSON
      ↓
GST verification
```

---

# 🔗 STEP 9 — Government Verification

Verify the provider registry from TASK 14.

The demo should execute:

```text id="x1fzgo"
GST
PAN
UDYAM
EPFO
ESIC
STARTUP_INDIA
NSIC
MAKE_IN_INDIA
OEM
BLACKLIST
```

through the common government-provider interface.

Expected:

```text id="s5t5yl"
Government Source
       ↓
Normalized Response
       ↓
Evidence
```

No direct frontend calls to government systems.

---

# 🔗 STEP 10 — Evidence

Every verified field should create traceable evidence.

Example:

```text id="i0m7jz"
Requirement:
Valid GST Registration

        ↓

Compliance Result:
PASS

        ↓

Evidence:
GST Government Verification

        ↓

GSTIN:
29ABCDE1234F1Z5

        ↓

Document:
GST_Certificate.pdf

        ↓

OCR Text

        ↓

Original Document
```

The officer must be able to follow this chain.

---

# ⚙️ STEP 11 — Run Compliance Evaluation

Trigger the existing:

```http id="b8xq37"
POST /api/v1/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluate
```

Do not create another evaluation endpoint.

Expected:

```text id="9c4k0h"
PENDING
 ↓
PROCESSING
 ↓
COMPLETED
```

---

# 📊 STEP 12 — Generate Compliance Summary

Expected demo result could be:

```text id="7q9r5n"
Compliance Assessment

10 Requirements

✓ Passed             8
✕ Failed             1
⚠ Partial            0
! Not Verified       1
```

The actual numbers should come from your demo data.

Do not force the result to be 8/1/0/1 if the underlying data produces something different.

---

# 🧑‍💼 STEP 13 — Officer Review

Open:

```text id="s3u7ct"
/compliance/evaluations/{evaluation_id}/review
```

Officer should be able to:

```text id="m7eq8m"
View requirement
View evidence
Review
Add comment
Flag issue
```

Then choose:

```text id="t5rrg5"
Qualified
Not Qualified
Requires Clarification
Withdrawn
```

The system records this as an:

> **Officer Decision**

not an AI decision.

---

# 📊 STEP 14 — Tender Dashboard

Return to:

```text id="eqf4qt"
/tenders/{tender_id}/dashboard
```

Verify the bidder now appears.

Example:

```text id="j9jsy8"
ABC Technologies

Compliance:
89%

Evaluation:
Completed

Officer Review:
Completed

Officer Decision:
Requires Clarification

[View Evaluation]
[View Review]
```

---

# 📜 STEP 15 — Full Audit Timeline

The complete workflow should be auditable.

Example:

```text id="g4h2b9"
11:00  Tender Created
11:02  Tender Document Uploaded
11:03  OCR Completed
11:04  AI Requirements Extracted
11:06  Requirement Approved
11:10  Bidder Document Uploaded
11:11  OCR Completed
11:12  AI Extraction Completed
11:13  GST Verification Completed
11:13  PAN Verification Completed
11:14  Compliance Evaluation Started
11:15  Compliance Evaluation Completed
11:16  Officer Review Started
11:18  Officer Decision Recorded
11:19  Officer Review Completed
```

Do not invent timestamps for display.

Use actual audit event timestamps.

---

# 🔐 STEP 16 — Authorization Boundaries

Verify that:

### AI cannot:

```text id="2u5z1g"
approve requirement
approve bidder
reject bidder
award tender
```

### Compliance engine cannot:

```text id="c8j3qm"
make officer decisions
```

### Government provider cannot:

```text id="j5pl3f"
approve bidder
```

### Dashboard cannot:

```text id="g6m0xm"
modify compliance results
```

Each layer only performs its assigned responsibility.

---

# 🧪 STEP 17 — Full Integration Test

Create one test representing the entire workflow.

Conceptually:

```text id="8cr8qm"
create tender
      ↓
upload tender document
      ↓
process OCR
      ↓
extract requirements
      ↓
approve requirement
      ↓
create bidder
      ↓
upload bidder document
      ↓
OCR
      ↓
AI extraction
      ↓
government verification
      ↓
compliance evaluation
      ↓
evidence generated
      ↓
officer review
      ↓
officer decision
      ↓
dashboard reflects result
      ↓
audit events exist
```

---

# 🧪 STEP 18 — Integration Assertions

The test should verify:

### Tender

```text id="7o0y6h"
Tender exists
```

### Tender document

```text id="0iv7w8"
Document exists
```

### OCR

```text id="3n5u8c"
OCR_COMPLETED
```

### AI

```text id="d4u9k5"
AI_COMPLETED
```

### Requirement

```text id="ppw0fu"
AI_SUGGESTED
```

then:

```text id="f3xg2a"
APPROVED
```

### Bidder

```text id="j8a6vc"
Bidder exists
```

### Government verification

```text id="b7j9da"
Verification exists
```

### Compliance

```text id="y8k0rm"
Evaluation = COMPLETED
```

### Evidence

```text id="e5k9sw"
Evidence exists
```

### Officer review

```text id="9z4x4x"
Review = COMPLETED
```

### Audit

```text id="0s5c6j"
Expected events exist
```

---

# 🧪 STEP 19 — Failure Scenario

The integration test must also prove the system doesn't falsely report success.

Simulate:

```text id="r7f8ko"
GST Government Provider
        ↓
UNAVAILABLE
```

Expected:

```text id="5n2r3y"
Government Verification:
SOURCE_ERROR
```

Then:

```text id="ak0q8h"
Compliance:
NOT_VERIFIED
```

The system must **not** say:

```text id="h7f0z9"
GST = PASS
```

just because the document contained a GST number.

---

# 🧪 STEP 20 — Historical Evaluation Test

Run evaluation:

```text id="p9g4vc"
Evaluation A
```

Then change demo government data.

Run evaluation again:

```text id="1l5c8h"
Evaluation B
```

Verify:

```text id="x9y5cq"
Evaluation A
```

still contains its original evidence snapshot.

This validates TASK 15's historical traceability.

---

# 🖥️ STEP 21 — Final Workflow Page

Create a simple page:

```text id="p2x7b1"
Tender Evaluation Workflow
```

Top:

```text id="n3o5lc"
Industrial Equipment Procurement

Tender ID: TND-2026-001

Status:
Evaluation in Progress
```

Then:

```text id="9d4m7k"
WORKFLOW

✓ Tender Documents
✓ Requirements
✓ Bidders
✓ Government Verification
✓ Compliance Evaluation
⟳ Officer Review
✓ Audit Trail
```

And actions:

```text id="7e1z8u"
[Documents]
[Requirements]
[Evaluation Dashboard]
[Audit Trail]
```

This page should primarily **navigate to existing modules** rather than duplicating their UI.

---

# 🚨 Do NOT build

TASK 20 should NOT add:

```text id="g0t9l2"
real authentication
role-based access control
payment
bid pricing
financial scoring
bid ranking
award generation
email system
notifications
mobile app
real government API credentials
production deployment
analytics/BI system
```

Those can be separate future milestones.

---

# ✅ Definition of Done

TASK 20 is complete when:

* [ ] Complete tender workflow can be demonstrated
* [ ] Tender document processing works
* [ ] OCR works
* [ ] AI requirement extraction works
* [ ] Officer approval works
* [ ] Bidder document processing works
* [ ] Government demo verification works
* [ ] Evidence is generated
* [ ] Compliance evaluation works
* [ ] Officer review works
* [ ] Officer decision is persisted
* [ ] Tender dashboard reflects current state
* [ ] Audit trail contains the workflow history
* [ ] Failure states propagate correctly
* [ ] Historical evaluations remain unchanged
* [ ] No subsystem bypasses another subsystem's authority
* [ ] Full integration test passes
* [ ] Manual golden-path test passes
* [ ] Existing TASK 01–19 functionality remains intact

---

# 📋 COPY THIS DIRECTLY TO YOUR VIBE CODER

```text
TASK 20 — Complete End-to-End Procurement Workflow Integration.

Assume TASKS 01–19 are fully implemented and working.

OBJECTIVE:

Connect and verify the entire procurement compliance workflow.

This task is primarily integration and end-to-end validation.

DO NOT create duplicate business logic.

EXISTING SYSTEMS:

TASK 07 → Documents
TASK 08 → OCR
TASK 09 → AI Extraction
TASK 10 → Government Verification
TASK 11 → Compliance Engine
TASK 12 → Tender Requirements
TASK 13 → Compliance Orchestration
TASK 14 → Government Provider Registry
TASK 15 → Evidence + Audit
TASK 16 → Officer Review
TASK 17 → Tender Dashboard
TASK 18 → Requirement Approval
TASK 19 → Tender Document Processing

GOLDEN PATH:

Tender
↓
Tender Document Upload
↓
OCR
↓
AI Requirement Extraction
↓
AI_SUGGESTED Requirements
↓
Officer Approval
↓
Bidder
↓
Bidder Document Upload
↓
OCR
↓
AI Extraction
↓
Government Verification
↓
Evidence
↓
Compliance Evaluation
↓
Officer Review
↓
Officer Decision
↓
Tender Dashboard
↓
Audit Trail

CRITICAL:

AI must never:
- approve requirements
- approve bidders
- reject bidders
- award tender

Compliance Engine must never make officer decisions.

Government providers must only provide verification evidence.

Dashboard must not modify compliance results.

OFFICER DECISION MUST REMAIN HUMAN CONTROLLED.

CREATE/REUSE:

backend/tests/integration/
    test_tender_workflow.py
    test_bidder_workflow.py
    test_compliance_workflow.py

Only create:

frontend/src/pages/TenderWorkflowPage.jsx

if the current application does not already have an appropriate workflow page.

Do not duplicate existing pages.

WORKFLOW STATUS:

Expose a read-only high-level workflow status.

Stages:

tender_created
documents_uploaded
ocr
requirement_extraction
requirements_approved
bidder_documents
government_verification
compliance_evaluation
officer_review

Use existing database state.

Do NOT create a second worker/process engine.

WORKFLOW UI:

Create a simple workflow timeline:

Tender Created
↓
Documents Uploaded
↓
OCR Completed
↓
AI Requirements Extracted
↓
Requirements Approved
↓
Bidder Documents Processed
↓
Government Verification
↓
Compliance Evaluation
↓
Officer Review
↓
Review Completed

The page should link to existing:

Documents
Requirements
Evaluation Dashboard
Audit Trail

Do not duplicate those interfaces.

DEMO:

Use the existing demo tender and bidder data.

Tender:
Industrial Equipment Procurement

Bidder:
ABC Technologies Pvt Ltd

Use existing demo requirements/providers.

Do not create a second incompatible demo-data system.

VERIFY:

Tender document:
uploaded and stored

OCR:
completed

AI:
completed

Requirements:
initially AI_SUGGESTED

Officer:
approves requirement

Bidder documents:
processed

Government verification:
completed using existing providers

Compliance:
completed

Evidence:
created and traceable

Officer review:
completed

Officer decision:
persisted

Dashboard:
reflects result

Audit:
contains complete history

INTEGRATION TEST:

Test the entire sequence:

create tender
→ upload tender document
→ OCR
→ AI extraction
→ approve requirement
→ create/use bidder
→ upload bidder document
→ OCR
→ AI extraction
→ government verification
→ compliance evaluation
→ evidence
→ officer review
→ officer decision
→ dashboard
→ audit

ASSERT:

- OCR_COMPLETED
- AI_COMPLETED
- requirement transitions AI_SUGGESTED → APPROVED
- government verification exists
- compliance evaluation COMPLETED
- evidence exists
- officer review COMPLETED
- officer decision exists
- dashboard reflects current state
- audit events exist

FAILURE TEST:

Make one government provider return UNAVAILABLE.

Expected:

Government verification = SOURCE_ERROR

Compliance should not falsely report PASS.

Use NOT_VERIFIED or the existing appropriate compliance status.

HISTORICAL TEST:

Run evaluation A.

Change demo government data.

Run evaluation B.

Verify evaluation A retains its original evidence snapshot.

Verify evaluation B reflects the new evidence.

SECURITY/ARCHITECTURE TEST:

Confirm:
AI cannot approve requirements.
AI cannot approve bidders.
Compliance cannot make officer decisions.
Government provider cannot make bidder decisions.
Dashboard cannot modify compliance results.

STRICT SCOPE:

Do not rewrite:
AI
OCR
Government
Compliance
Evidence
Review
Dashboard
Document
Requirement

Reuse existing implementations.

Do not add:
authentication
RBAC
notifications
payments
bid ranking
financial scoring
award workflow
real government credentials
production deployment

Do not start TASK 21.

At the end report:

1. Files created
2. Files modified
3. Integration points connected
4. APIs reused
5. Database changes
6. Integration tests executed
7. Failure tests executed
8. Historical evaluation test
9. Manual golden-path result
10. Confirmation that no automatic bidder decision was introduced

STOP AFTER TASK 20.
```

## 🏁 What you've achieved by TASK 20

At this point, your architecture has reached a very strong **MVP/demo-complete backbone**:

```text
             ┌──────────────────┐
             │      TENDER      │
             └────────┬─────────┘
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
   TENDER DOCUMENTS            BIDDERS
          ↓                       ↓
         OCR                     DOCS
          ↓                       ↓
    AI REQUIREMENTS              OCR
          ↓                       ↓
  OFFICER APPROVAL          AI EXTRACTION
          ↓                       ↓
    APPROVED RULES       GOVT VERIFICATION
          └───────────┬───────────┘
                      ↓
              COMPLIANCE ENGINE
                      ↓
                 EVIDENCE
                      ↓
               OFFICER REVIEW
                      ↓
              OFFICER DECISION
                      ↓
             TENDER DASHBOARD
                      ↓
                AUDIT TRAIL
```

🔥 **TASK 20 is therefore your first major “system works as one product” milestone.** From TASK 21 onward, you can focus increasingly on hardening, security, performance, testing, real integrations where legitimately available, deployment, and the SIH demonstration rather than continuing to build disconnected foundations.
