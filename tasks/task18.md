# 🚀 TASK 18 — Tender Document & Requirement Review Workspace

Assuming **TASK 17 — Tender Evaluation Dashboard** is completed successfully, TASK 18 should now build the **Tender Document + Requirement Management workspace**.

This is an important stage because the officer needs to go from:

**“I see a compliance problem” → “What exactly did the tender require?” → “Where did that requirement come from?”**

The workspace will connect the work from **TASK 12 (requirement extraction)** with the officer workflow from **TASK 16–17**.

---

# 🎯 Objective

Build a dynamic workspace where a procurement officer can:

1. View tender documents.
2. Upload/manage tender documents if that functionality already exists.
3. View OCR-extracted tender text.
4. View AI-suggested requirements.
5. Review individual requirements.
6. Approve/reject/edit AI suggestions.
7. See the source text/page/section for each requirement.
8. Understand which requirements are currently active.
9. See which requirements are used by compliance evaluation.

The key workflow becomes:

```text
Tender Document
      ↓
OCR
      ↓
AI Requirement Extraction
      ↓
AI Suggested Requirements
      ↓
Officer Review
      ↓
APPROVED Requirement
      ↓
Compliance Evaluation
```

---

# 🚨 Critical rule

AI-generated requirements are **suggestions only**.

AI must never directly activate a requirement.

Only:

```text
Procurement Officer
        ↓
Approve
        ↓
Requirement becomes APPROVED
        ↓
Compliance Engine may use it
```

This rule must be enforced **on the backend**, not just hidden in the frontend.

---

# 📁 Files to create

First inspect TASK 12's implementation.

Create only if equivalent files don't already exist:

```text
backend/
└── app/
    └── tender_requirements/
        ├── __init__.py
        ├── schemas.py
        ├── service.py
        ├── repository.py
        └── router.py

frontend/
└── src/
    ├── services/
    │   └── tenderRequirementService.js
    │
    └── components/
        └── requirements/
            ├── TenderRequirements.jsx
            ├── RequirementCard.jsx
            ├── RequirementReviewPanel.jsx
            ├── RequirementSource.jsx
            └── RequirementStatusBadge.jsx
```

If TASK 12 already has these capabilities:

> **Extend the existing implementation. Do not create duplicate requirement systems.**

---

# 🔐 Allowed modifications

The developer may modify:

```text
backend/app/main.py
```

to register routes.

Existing tender-detail routing may be modified to add navigation.

Existing requirement components/services from TASK 12 may be extended.

Existing document components may be reused.

---

# ❌ Do NOT modify

Do not modify:

```text
backend/app/ai/
backend/app/ocr/
backend/app/government/
backend/app/compliance/
backend/app/review/
backend/app/dashboard/
```

Do not change:

* compliance evaluation logic
* government providers
* OCR processing
* AI provider implementation
* bidder verification
* officer review from TASK 16

TASK 18 is primarily a **tender requirement management and review UI/API layer**.

---

# 🧠 STEP 1 — Tender Requirement Lifecycle

Use the lifecycle established in TASK 12:

```text
DRAFT
AI_SUGGESTED
UNDER_REVIEW
APPROVED
REJECTED
ARCHIVED
```

Recommended workflow:

```text
AI_SUGGESTED
      ↓
UNDER_REVIEW
      ↓
   ┌──┴──┐
 APPROVED REJECTED
```

An officer can edit an AI suggestion before approving it.

---

# 📋 STEP 2 — Requirement List

Create a tender-level page:

```text
Tender Requirements

Tender:
Industrial Equipment Procurement

Requirements: 8
Approved: 5
Under Review: 2
Rejected: 1
```

Then:

```text
┌──────────────────────────────────────────────┐
│ GST Registration                       APPROVED │
│                                              │
│ Bidder must possess a valid and active GST   │
│ registration.                                │
│                                              │
│ Rule: STATUS_EQUALS ACTIVE                   │
│ Source: Tender Document, Section 4.2         │
│                                              │
│ [View Source] [View Rule]                    │
└──────────────────────────────────────────────┘
```

---

# 🤖 STEP 3 — AI Suggested Requirement

Example:

```text
┌──────────────────────────────────────────────┐
│ ⚠ AI Suggested Requirement                   │
│                                              │
│ Bidder must be registered in Tamil Nadu.     │
│                                              │
│ Category: OTHER                              │
│ Status: AI_SUGGESTED                         │
│                                              │
│ Source: Page 3                               │
│ Confidence: 91%                              │
│                                              │
│ [Review] [Reject]                            │
└──────────────────────────────────────────────┘
```

Be careful with the word:

> **Confidence**

If TASK 12 does not actually provide a calibrated confidence score, **do not invent one**.

Instead display:

```text
AI Suggested
```

and provide source traceability.

---

# 🔎 STEP 4 — Requirement Source

Every AI-suggested requirement should expose where it came from.

Example:

```text
Requirement Source

Document:
Tender_2026.pdf

Page:
3

Section:
Eligibility Requirements

Source text:
"The bidder must be registered in Tamil Nadu."

────────────────────────────

AI Interpretation:

Requirement:
Tamil Nadu registration

Category:
OTHER

────────────────────────────

[Open Document]
```

The source text must come from the actual extracted tender text.

Do not fabricate source quotations.

---

# ✏️ STEP 5 — Requirement Editing

An officer should be able to edit:

```text
Title
Description
Category
Rule Type
Rule Parameters
Mandatory
Display Order
```

Example:

```text
Requirement

Title:
Valid GST Registration

Description:
Bidder must possess a valid and active GST registration.

Category:
GST

Rule:
STATUS_EQUALS

Expected:
ACTIVE

Mandatory:
Yes
```

---

# 🧩 STEP 6 — Rule Configuration

Use the rule types established in TASK 11.

For example:

```text
IDENTIFIER_MATCH
STATUS_EQUALS
FIELD_EQUALS
FIELD_EXISTS
FIELD_NOT_EMPTY
FIELD_GREATER_THAN_OR_EQUAL
```

For GST:

```json
{
  "source": "GST",
  "field": "status",
  "operator": "EQUALS",
  "expected_value": "ACTIVE"
}
```

For Make in India:

```json
{
  "source": "MAKE_IN_INDIA",
  "field": "local_content_percentage",
  "operator": "GREATER_THAN_OR_EQUAL",
  "expected_value": 50
}
```

The UI should provide structured controls where practical.

Do **not** expose a raw JSON editor as the primary interface unless the existing architecture already requires it.

---

# 🔐 STEP 7 — Approval Enforcement

This is one of the most important parts of TASK 18.

Backend must prevent:

```text
AI_SUGGESTED
```

from being consumed by the compliance engine.

Only:

```text
APPROVED
```

requirements can become active compliance requirements.

For example:

```text
POST /requirements/{id}/approve
```

should:

1. Verify requirement exists.
2. Verify it belongs to the tender.
3. Validate rule configuration.
4. Change status to `APPROVED`.
5. Create an audit event.
6. Make it available to compliance evaluation.

---

# ❌ STEP 8 — Reject Requirement

Implement:

```http
POST /api/v1/requirements/{requirement_id}/reject
```

Example:

```json
{
  "reason": "AI interpretation does not represent a mandatory eligibility condition."
}
```

Result:

```text
AI_SUGGESTED
       ↓
REJECTED
```

Persist the reason.

---

# ✏️ STEP 9 — Edit + Re-review

If an already approved requirement is substantially edited, don't silently change the active requirement.

Use:

```text
APPROVED
   ↓
UNDER_REVIEW
   ↓
APPROVED
```

This is important for auditability.

The previous approved version should remain traceable.

If the existing schema supports versioning, use it.

If not, implement the smallest safe history mechanism rather than rewriting the entire requirement architecture.

---

# 🔌 STEP 10 — APIs

Expose APIs similar to:

### List requirements

```http
GET /api/v1/tenders/{tender_id}/requirements
```

---

### Get requirement

```http
GET /api/v1/requirements/{requirement_id}
```

---

### Create requirement

```http
POST /api/v1/tenders/{tender_id}/requirements
```

---

### Update requirement

```http
PATCH /api/v1/requirements/{requirement_id}
```

---

### Approve

```http
POST /api/v1/requirements/{requirement_id}/approve
```

---

### Reject

```http
POST /api/v1/requirements/{requirement_id}/reject
```

---

### Change status/review

```http
POST /api/v1/requirements/{requirement_id}/review
```

Use the existing TASK 12 API if already implemented instead of creating duplicates.

---

# 📜 STEP 11 — Audit Trail

Reuse TASK 15 audit infrastructure.

Record events such as:

```text
REQUIREMENT_CREATED
REQUIREMENT_AI_SUGGESTED
REQUIREMENT_REVIEW_STARTED
REQUIREMENT_EDITED
REQUIREMENT_APPROVED
REQUIREMENT_REJECTED
REQUIREMENT_ARCHIVED
```

Example:

```json
{
  "event": "REQUIREMENT_APPROVED",
  "requirement_id": "req-001",
  "actor": "officer-demo",
  "details": {
    "previous_status": "UNDER_REVIEW",
    "new_status": "APPROVED"
  }
}
```

---

# 🔗 STEP 12 — Connect Requirements to Compliance

The page should clearly show:

```text
GST Registration
Status: APPROVED

Used in:
3 compliance evaluations
```

If this information is available from existing data.

For an unapproved requirement:

```text
Tamil Nadu Registration
Status: AI_SUGGESTED

Compliance:
Not active

Reason:
Requirement requires officer approval.
```

This makes the AI → officer → compliance relationship obvious.

---

# 🖥️ STEP 13 — Tender Detail Navigation

Add:

```text
Tender Details

[Requirements]
[Documents]
[Evaluation Dashboard]
```

Click:

```text
Requirements
```

opens:

```text
/tenders/{tender_id}/requirements
```

The page should contain filters:

```text
All
AI Suggested
Under Review
Approved
Rejected
```

---

# 🧪 STEP 14 — Tests

### Test 1 — List requirements

Create a tender with:

```text
3 APPROVED
2 AI_SUGGESTED
1 REJECTED
```

Verify correct counts.

---

### Test 2 — Approve requirement

```text
AI_SUGGESTED
      ↓
APPROVED
```

Verify persistence.

---

### Test 3 — Reject requirement

```text
AI_SUGGESTED
      ↓
REJECTED
```

Verify rejection reason.

---

### Test 4 — Invalid rule

Attempt:

```text
STATUS_EQUALS
```

without required configuration.

Expected:

```text
400 validation error
```

---

### Test 5 — Compliance protection

Create:

```text
AI_SUGGESTED requirement
```

Attempt to run compliance evaluation.

Expected:

```text
Requirement is ignored/not eligible for evaluation
```

Only:

```text
APPROVED
```

requirements should be evaluated.

---

### Test 6 — Edit approved requirement

Edit an approved requirement.

Expected:

```text
UNDER_REVIEW
```

or the existing version-controlled equivalent.

It must not silently alter the previously approved state.

---

### Test 7 — Source traceability

Requirement should expose:

```text
document
page
section
source text
```

where available.

---

### Test 8 — Audit

Verify:

```text
created
edited
approved
rejected
```

events are recorded.

---

# 🧪 Manual Test

Use the existing demo tender.

Open:

```text
Tender
 ↓
Requirements
```

You should see something like:

```text
GST Registration          APPROVED
PAN                       APPROVED
Tamil Nadu Registration   AI_SUGGESTED
Debarment                 AI_SUGGESTED
```

Open:

```text
Tamil Nadu Registration
```

Verify:

```text
Source Document
Page
Section
Extracted Source Text
AI Suggested Requirement
```

Click:

```text
Review
```

Edit the requirement if necessary.

Then:

```text
Approve
```

Expected:

```text
Status: APPROVED
```

Refresh the page.

Expected:

```text
Status remains APPROVED
```

Now verify the requirement can be consumed by the compliance pipeline.

---

# 🚨 Negative Test

This one is **mandatory**.

Create:

```text
AI_SUGGESTED
```

requirement.

Do **not** approve it.

Run compliance evaluation.

Expected:

```text
AI_SUGGESTED requirement
        ↓
NOT USED
```

Then approve it:

```text
AI_SUGGESTED
        ↓
APPROVED
        ↓
New compliance evaluation
        ↓
Requirement included
```

This proves that your platform has a proper **human-in-the-loop control**.

---

# 🏗️ Architecture After TASK 18

Your architecture now becomes:

```text
                 TENDER
                   │
          ┌────────┴────────┐
          │                 │
     Documents         Requirements
          │                 │
         OCR          AI Extraction
          │                 │
          │          AI Suggestions
          │                 │
          │          Officer Review
          │                 │
          │              APPROVED
          │                 │
          └────────┬────────┘
                   ↓
           Compliance Engine
                   ↓
             Evaluation
                   ↓
             Evidence
                   ↓
            Officer Review
                   ↓
          Tender Dashboard
```

🔥 This is a very strong architecture for the SIH demo because it clearly demonstrates **AI assistance + deterministic rules + government evidence + human approval + auditability**.

---

# ✅ Definition of Done

TASK 18 is complete when:

* [ ] Tender Requirements workspace exists
* [ ] Requirements load dynamically
* [ ] AI-suggested requirements are visible
* [ ] Requirement source is visible
* [ ] Source document/page/section is traceable where available
* [ ] Officer can review requirements
* [ ] Officer can edit requirements
* [ ] Officer can approve requirements
* [ ] Officer can reject requirements
* [ ] Rejection reason persists
* [ ] Rule configuration is validated
* [ ] Only APPROVED requirements are active for compliance
* [ ] Approved requirement edits are auditable
* [ ] Audit events are generated
* [ ] Existing TASK 12 functionality is reused
* [ ] Existing compliance engine remains unchanged
* [ ] Loading state works
* [ ] Empty state works
* [ ] Error state works
* [ ] Backend tests pass
* [ ] Manual test passes
* [ ] AI-suggested negative test passes
* [ ] Existing TASK 01–17 functionality remains intact

---

# 📋 COPY THIS DIRECTLY TO YOUR VIBE CODER

```text
TASK 18 — Build the Tender Document & Requirement Review Workspace.

Assume TASKS 01–17 are fully implemented and working.

OBJECTIVE:

Build the procurement officer workspace for reviewing tender documents and AI-extracted tender requirements.

The workflow must be:

Tender Document
↓
OCR
↓
AI Requirement Extraction
↓
AI Suggested Requirement
↓
Officer Review
↓
APPROVED Requirement
↓
Compliance Engine

CRITICAL HUMAN-IN-THE-LOOP RULE:

AI-generated requirements are suggestions only.

AI must NEVER automatically activate a requirement.

Only an explicitly APPROVED requirement may be consumed by the compliance engine.

Reuse TASK 12 functionality if already implemented.

Do not create duplicate requirement systems.

REQUIREMENT STATUSES:

DRAFT
AI_SUGGESTED
UNDER_REVIEW
APPROVED
REJECTED
ARCHIVED

BACKEND:

Create/reuse:

backend/app/tender_requirements/
    __init__.py
    schemas.py
    service.py
    repository.py
    router.py

APIs:

GET
/api/v1/tenders/{tender_id}/requirements

GET
/api/v1/requirements/{requirement_id}

POST
/api/v1/tenders/{tender_id}/requirements

PATCH
/api/v1/requirements/{requirement_id}

POST
/api/v1/requirements/{requirement_id}/approve

POST
/api/v1/requirements/{requirement_id}/reject

POST
/api/v1/requirements/{requirement_id}/review

Use existing TASK 12 APIs if already available.

REQUIREMENT FIELDS:

title
description
category
type
rule_type
parameters
mandatory
display_order
status
source_document_id
source_page
source_section
source_text
created_at
updated_at

Do not invent source information.

Only show source fields when actual source information exists.

RULE TYPES:

IDENTIFIER_MATCH
STATUS_EQUALS
FIELD_EQUALS
FIELD_EXISTS
FIELD_NOT_EMPTY
FIELD_GREATER_THAN_OR_EQUAL

Validate rule parameters server-side.

Example:

{
  "source": "GST",
  "field": "status",
  "operator": "EQUALS",
  "expected_value": "ACTIVE"
}

APPROVAL:

When approving:

1. Verify requirement exists.
2. Verify requirement belongs to the tender.
3. Validate rule configuration.
4. Change status to APPROVED.
5. Record audit event.
6. Make requirement eligible for compliance evaluation.

REJECTION:

Allow officer to reject AI suggestions.

Persist rejection reason.

EDITING:

If an APPROVED requirement is materially edited, it must return to UNDER_REVIEW or use the existing versioning mechanism.

Do not silently modify an approved requirement.

AUDIT:

Reuse TASK 15 audit infrastructure.

Record:

REQUIREMENT_CREATED
REQUIREMENT_AI_SUGGESTED
REQUIREMENT_REVIEW_STARTED
REQUIREMENT_EDITED
REQUIREMENT_APPROVED
REQUIREMENT_REJECTED
REQUIREMENT_ARCHIVED

FRONTEND:

Create/reuse:

frontend/src/services/tenderRequirementService.js

frontend/src/components/requirements/
    TenderRequirements.jsx
    RequirementCard.jsx
    RequirementReviewPanel.jsx
    RequirementSource.jsx
    RequirementStatusBadge.jsx

Add tender navigation:

Tender Details
→ Requirements
→ Evaluation Dashboard
→ Documents

Requirements page should show:

- Total requirements
- Approved
- AI Suggested
- Under Review
- Rejected

Provide filters:

All
AI Suggested
Under Review
Approved
Rejected

Requirement cards should show:

Title
Description
Category
Rule
Mandatory status
Requirement status
Source document
Source page
Source section
Source text

Actions:

Review
Edit
Approve
Reject
View Source

Do not add automatic approval/rejection.

UI STYLE:

Use the existing minimalist government portal design.

PASS/APPROVED = green
AI Suggested/Under Review = orange
Rejected/Failed = red
Information/source = blue

Avoid flashy gradients, excessive animations, glassmorphism, or marketing-style UI.

COMPLIANCE PROTECTION:

MANDATORY NEGATIVE TEST:

Create an AI_SUGGESTED requirement.

Run compliance evaluation.

The requirement MUST NOT be evaluated.

Approve the requirement.

Run a new compliance evaluation.

The requirement MUST now be eligible for evaluation.

This protection must exist on the backend, not only the frontend.

TESTS:

1. Requirement listing
2. Requirement counts
3. Approve requirement
4. Reject requirement
5. Rejection reason persistence
6. Invalid rule validation
7. AI_SUGGESTED excluded from compliance
8. APPROVED included in compliance
9. Approved requirement editing requires re-review/versioning
10. Source traceability
11. Audit events
12. 404 handling
13. Persistence after refresh

MANUAL TEST:

Open:

Tender
→ Requirements

Verify AI-suggested requirements appear.

Open one.

Verify source document/page/section/source text.

Review it.

Edit if necessary.

Approve it.

Refresh.

Verify APPROVED persists.

Run compliance evaluation.

Verify the approved requirement participates.

Create another AI_SUGGESTED requirement.

Do not approve it.

Run a new evaluation.

Verify it does NOT participate.

STRICT SCOPE:

Do NOT modify:

backend/app/ai/
backend/app/ocr/
backend/app/government/
backend/app/compliance/
backend/app/review/
backend/app/dashboard/

Reuse their existing functionality.

Do not create duplicate audit, OCR, AI, evidence, or compliance systems.

Do not introduce automatic bidder qualification/rejection.

Do not start TASK 19.

At the end report:

1. Files created
2. Files modified
3. APIs added
4. Database changes
5. Tests executed
6. Manual test results
7. Confirmation that unapproved requirements cannot enter compliance evaluation

STOP AFTER TASK 18.
```

### 🧱 Position in your architecture

After this milestone, you have a particularly important control point:

**AI extracts → Officer approves → Rules evaluate.**

That makes the system much easier to defend in an SIH presentation because you can explicitly demonstrate that **AI does not get unchecked authority over procurement decisions**.
