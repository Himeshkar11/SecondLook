# 🚀 TASK 12 — Tender Requirement Management & Requirement Extraction

Assuming **TASK 11 passed**, we now need to solve a major missing piece.

Right now we have:

```text
Tender
   ↓
Manually created requirements
   ↓
Compliance Engine
   ↓
PASS / FAIL / NOT_VERIFIED
```

But in the real SIH workflow, a procurement officer starts with a **tender document**.

The system needs to turn that tender document into structured requirements.

So TASK 12 introduces:

```text
Tender Document
      ↓
OCR / Text
      ↓
Requirement Extraction
      ↓
Structured Tender Requirements
      ↓
Procurement Officer Review
      ↓
Compliance Engine
```

### ⚠️ Very important

Unlike bidder-document extraction, **AI must NOT automatically activate a requirement for compliance**.

AI can *suggest*:

> "This tender appears to require active GST registration."

But the procurement officer must be able to review/edit/approve it.

That gives us:

```text
AI suggestion
      ↓
Officer review
      ↓
Approved requirement
      ↓
Compliance Engine
```

This is much safer and much more defensible for a procurement system.

---

# 📋 EXACT VIBE-CODING PROMPT

```text
TASK 12 — TENDER REQUIREMENT MANAGEMENT AND EXTRACTION

TASK 11 has been completed successfully.

The application currently supports:

Tender
    ↓
Tender Requirements
    ↓
Evidence
    ↓
Compliance Engine
    ↓
PASS / FAIL / NOT_VERIFIED

However, tender requirements are currently primarily seeded/manual.

Now implement the TENDER REQUIREMENT MANAGEMENT AND EXTRACTION LAYER.

--------------------------------------------------
CORE PURPOSE
--------------------------------------------------

The system must allow a procurement officer to:

1. Open a tender.
2. View its requirements.
3. Add/edit/remove requirements where permitted.
4. Upload or associate a tender document.
5. Extract possible requirements from the tender document.
6. Review AI-suggested requirements.
7. Approve/reject/edit those suggestions.
8. Only APPROVED requirements should be evaluated by the Compliance Engine.

The architecture must therefore be:

Tender Document
      ↓
Text Extraction
      ↓
AI Requirement Extraction
      ↓
Suggested Requirements
      ↓
Procurement Officer Review
      ↓
Approved Requirements
      ↓
Compliance Engine

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

AI may suggest tender requirements.

AI must NOT silently create active compliance requirements.

AI must NOT automatically:

- reject a bidder
- approve a bidder
- mark a requirement mandatory
- determine final qualification
- determine final disqualification
- make procurement decisions

The procurement officer must explicitly approve requirements before they become active compliance rules.

--------------------------------------------------
DO NOT IMPLEMENT
--------------------------------------------------

Do NOT implement:

- automatic bidder approval
- automatic bidder rejection
- bid award
- final qualification
- final disqualification
- risk scoring
- government API integrations
- OCR redesign
- bidder document OCR
- bidder AI extraction
- GST provider
- PAN provider
- new government integrations
- final procurement decision

Reuse existing:

- OCR
- AI extraction
- Government Verification
- Compliance Engine
- Tender
- Bidder
- Document

--------------------------------------------------
STEP 1 — INSPECT EXISTING STRUCTURE
--------------------------------------------------

Before modifying anything inspect:

backend/app/
backend/app/ai/
backend/app/ocr/
backend/app/integrations/
backend/app/verification/
backend/app/models/
backend/app/schemas/
backend/app/services/
backend/app/api/
backend/app/workers/
backend/tests/
supabase/migrations/

Frontend:

frontend/src/pages/
frontend/src/components/
frontend/src/services/

Inspect existing:

- tender model
- tender detail page
- tender requirements
- document model
- document processing
- OCR processor
- AI extractor
- compliance engine
- API conventions
- database migrations
- demo data

Reuse existing architecture.

Do not create duplicate services.

--------------------------------------------------
STEP 2 — TENDER DOCUMENT
--------------------------------------------------

A tender may have one or more source documents.

Use the existing document architecture if possible.

A tender document should be associated with:

tender_id

rather than bidder_id.

Do not force tender documents into bidder document semantics.

If the existing document table supports ownership/entity relationships, reuse that architecture.

Otherwise add the minimum required structure.

--------------------------------------------------
STEP 3 — TENDER DOCUMENT TYPES
--------------------------------------------------

Support at least:

TENDER_DOCUMENT
TENDER_CORRIGENDUM
TENDER_ADDENDUM
TENDER_OTHER

Do not implement a complex document classification system.

--------------------------------------------------
STEP 4 — TENDER TEXT EXTRACTION
--------------------------------------------------

Tender documents need machine-readable text before AI extraction.

Reuse the existing OCR/text processing abstraction where possible.

Do NOT copy the OCR implementation into another module.

The flow should be:

Tender Document
      ↓
Existing OCR/Text Processor
      ↓
Tender Text
      ↓
AI Requirement Extraction

If the existing OCR architecture is bidder-document-specific, create a thin reusable interface rather than duplicating OCR logic.

--------------------------------------------------
STEP 5 — AI REQUIREMENT EXTRACTION
--------------------------------------------------

Create a dedicated AI requirement extractor.

Conceptually:

TenderRequirementExtractor

Input:

- tender document text
- optional tender metadata

Output:

structured candidate requirements.

Example:

{
  "requirements": [
    {
      "title": "Active GST Registration",
      "description": "Bidder must possess a valid and active GST registration.",
      "requirement_type": "GST",
      "rule_type": "STATUS_EQUALS",
      "parameters": {
        "field": "status",
        "operator": "EQUALS",
        "expected_value": "ACTIVE"
      },
      "mandatory": true,
      "source_text": "The bidder shall possess a valid and active GST registration."
    }
  ]
}

--------------------------------------------------
STEP 6 — SOURCE TEXT
--------------------------------------------------

Every AI-suggested requirement must preserve the source text from the tender document.

Example:

{
  "source_text":
  "The bidder shall possess a valid and active GST registration."
}

If page/section information is available, preserve it.

Possible:

source_page
source_section

This is important for auditability.

The officer must be able to understand where the AI suggestion came from.

--------------------------------------------------
STEP 7 — DO NOT INVENT REQUIREMENTS
--------------------------------------------------

The AI extractor must be instructed:

- only extract requirements explicitly supported by the tender text
- do not invent requirements
- do not infer unstated eligibility conditions
- do not create government verification requirements without textual evidence
- do not assume a requirement is mandatory unless the document supports that interpretation

If uncertain:

flag the requirement for officer review.

--------------------------------------------------
STEP 8 — REQUIREMENT CATEGORIES
--------------------------------------------------

Support structured requirement categories.

At minimum:

GST
PAN
UDYAM
MSME
FINANCIAL
EXPERIENCE
TECHNICAL
DOCUMENT
OEM
MAKE_IN_INDIA
EPFO
ESIC
STARTUP_INDIA
NSIC
BLACKLISTING
OTHER

Only GST and PAN need fully working Compliance Engine rules initially.

Other categories may be stored as requirements but marked as requiring manual configuration/future verification.

--------------------------------------------------
STEP 9 — REQUIREMENT STATUS
--------------------------------------------------

Create controlled requirement lifecycle states.

At minimum:

DRAFT
AI_SUGGESTED
UNDER_REVIEW
APPROVED
REJECTED
ARCHIVED

Meaning:

AI_SUGGESTED:
AI extracted a possible requirement.

UNDER_REVIEW:
Officer is reviewing it.

APPROVED:
Requirement is active and may be evaluated.

REJECTED:
Officer rejected the suggestion.

ARCHIVED:
Requirement was previously approved but is no longer active.

--------------------------------------------------
STEP 10 — APPROVAL RULE
--------------------------------------------------

Only:

APPROVED

requirements may be passed to the Compliance Engine.

The Compliance Engine must never evaluate:

AI_SUGGESTED

or:

DRAFT

requirements.

This must be enforced by the backend.

Do not rely only on frontend behavior.

--------------------------------------------------
STEP 11 — MANUAL REQUIREMENT CREATION
--------------------------------------------------

Allow the procurement officer to manually create a requirement.

Example:

Title:
Active GST Registration

Category:
GST

Rule:
STATUS_EQUALS

Field:
status

Expected:
ACTIVE

Mandatory:
true

Status:

APPROVED

if the officer explicitly saves it as approved according to the project's permission model.

--------------------------------------------------
STEP 12 — REQUIREMENT EDITING
--------------------------------------------------

Officer should be able to edit:

- title
- description
- category
- mandatory flag
- rule
- rule parameters
- source reference where appropriate

If an approved requirement is modified, consider returning it to:

UNDER_REVIEW

unless the existing project has an explicit approval workflow.

Do not silently modify an active compliance rule without preserving traceability.

--------------------------------------------------
STEP 13 — AI SUGGESTION REVIEW UI
--------------------------------------------------

Create a government-portal-style review interface.

Example:

Tender Requirements

----------------------------------------

AI Suggested Requirement

Active GST Registration

"The bidder shall possess a valid and active GST registration."

Category:
GST

Suggested Rule:
GST status = ACTIVE

Source:
Page 12

[ Approve ] [ Edit ] [ Reject ]

----------------------------------------

The UI must make it obvious that:

AI suggested this.

It is NOT active until approved.

--------------------------------------------------
STEP 14 — REQUIREMENT EDITOR
--------------------------------------------------

Create a simple requirement editor.

Fields:

Requirement title
Description
Category
Mandatory
Rule type
Rule parameters
Source text
Source page/section

Do not create a complicated visual rule builder.

A simple structured form is sufficient.

--------------------------------------------------
STEP 15 — RULE COMPATIBILITY
--------------------------------------------------

The requirement extraction system must use the rule types already created in TASK 11.

Do NOT create a second rule system.

Reuse:

STATUS_EQUALS
FIELD_EQUALS
FIELD_EXISTS
IDENTIFIER_MATCH

If the AI suggests an unsupported rule:

store it as a suggestion requiring manual configuration.

Do not automatically activate it.

--------------------------------------------------
STEP 16 — AI PROVIDER
--------------------------------------------------

Reuse the AI provider abstraction from TASK 09.

Do not create another AI client.

Use the existing:

AI provider
AI model configuration
API key configuration
structured output mechanism

Create only the new requirement-extraction prompt/schema.

--------------------------------------------------
STEP 17 — DEMO AI REQUIREMENT EXTRACTOR
--------------------------------------------------

Create a deterministic DemoTenderRequirementExtractor.

Input:

The following fictional tender text:

"Tenderer shall possess a valid and active GST registration.
The bidder shall submit a valid PAN.
The bidder must be registered in Tamil Nadu.
The bidder shall not be debarred by any government authority."

Expected suggestions should include at least:

1. Active GST Registration
2. Valid PAN
3. Tamil Nadu registration
4. Debarment/blacklisting requirement

However:

Only GST/PAN should have fully configured rule mappings initially.

For unsupported requirements:

mark them as requiring manual configuration.

Do not invent verification providers.

--------------------------------------------------
STEP 18 — DEMO SOURCE REFERENCES
--------------------------------------------------

The demo extractor should return source references.

Example:

{
  "title": "Active GST Registration",
  "source_text":
    "Tenderer shall possess a valid and active GST registration.",
  "source_page": 1
}

Use deterministic fictional page numbers if the demo document has known pages.

--------------------------------------------------
STEP 19 — DATABASE
--------------------------------------------------

Extend the database minimally.

A conceptual tender_requirements structure:

id
tender_id
code
title
description
requirement_type
rule_type
parameters
mandatory
status
source_document_id
source_text
source_page
source_section
created_by
approved_by
created_at
updated_at
approved_at

Use existing project naming conventions.

If the current table already contains most fields, ALTER/extend rather than creating a duplicate table.

--------------------------------------------------
STEP 20 — REQUIREMENT VERSIONING
--------------------------------------------------

If an approved requirement changes, preserve enough history to understand:

What was approved
Who approved it
When it was approved
What rule was active

Reuse the existing audit mechanism if available.

Do not build an unnecessarily complex versioning system.

At minimum preserve timestamps and approval information.

--------------------------------------------------
STEP 21 — API
--------------------------------------------------

Create APIs following existing conventions.

Conceptually:

GET /api/v1/tenders/{tender_id}/requirements

Returns all requirements.

POST /api/v1/tenders/{tender_id}/requirements

Creates a manual requirement.

GET /api/v1/tender-requirements/{requirement_id}

Returns one requirement.

PATCH /api/v1/tender-requirements/{requirement_id}

Updates a requirement.

POST /api/v1/tender-requirements/{requirement_id}/approve

Approves an AI-suggested requirement.

POST /api/v1/tender-requirements/{requirement_id}/reject

Rejects an AI-suggested requirement.

POST /api/v1/tenders/{tender_id}/requirements/extract

Starts AI requirement extraction from tender text/document.

Use existing API naming conventions if they differ.

--------------------------------------------------
STEP 22 — API SECURITY
--------------------------------------------------

Approval must be a backend operation.

The frontend must not be able to simply send:

status = APPROVED

and bypass the intended approval workflow.

The backend should validate:

- requirement exists
- tender exists
- requirement belongs to tender
- valid state transition
- required fields exist
- rule configuration is valid where applicable

--------------------------------------------------
STEP 23 — STATUS TRANSITIONS
--------------------------------------------------

Implement controlled transitions.

Valid examples:

AI_SUGGESTED
    ↓
UNDER_REVIEW
    ↓
APPROVED

or:

AI_SUGGESTED
    ↓
REJECTED

Approved:

APPROVED
    ↓
UNDER_REVIEW
    ↓
APPROVED

or:

APPROVED
    ↓
ARCHIVED

Do not allow arbitrary invalid transitions.

--------------------------------------------------
STEP 24 — COMPLIANCE ENGINE INTEGRATION
--------------------------------------------------

Update TASK 11 integration so only APPROVED requirements are evaluated.

Example:

Requirement status:

AI_SUGGESTED

Compliance Engine:

DO NOT EVALUATE

Requirement status:

APPROVED

Compliance Engine:

EVALUATE

Do not modify the core rule logic unnecessarily.

--------------------------------------------------
STEP 25 — TENDER DETAIL PAGE
--------------------------------------------------

Update TenderDetailPage with:

Requirements

Example:

Tender Requirements
--------------------------------

✓ Active GST Registration
  GST
  Mandatory
  APPROVED

✓ Valid PAN
  PAN
  Mandatory
  APPROVED

⏳ Debarment Requirement
  BLACKLISTING
  Requires manual configuration

--------------------------------

AI Suggestions:

2 pending review

[Review Requirements]

Keep the UI minimalist and consistent with the existing government portal style.

--------------------------------------------------
STEP 26 — REQUIREMENT REVIEW PAGE
--------------------------------------------------

Create a dedicated requirement review page/component if appropriate.

Show:

- AI suggestion
- source text
- source document
- page
- category
- suggested rule
- mandatory status
- current status

Actions:

Approve
Edit
Reject

Do not add excessive animations.

--------------------------------------------------
STEP 27 — REQUIREMENT EXTRACTION FAILURE
--------------------------------------------------

Handle:

- empty tender text
- invalid AI response
- malformed JSON
- unsupported requirement category
- unsupported rule
- AI provider failure

On failure:

Do not create APPROVED requirements.

Store a safe extraction failure state.

Allow retry where appropriate.

--------------------------------------------------
STEP 28 — HALLUCINATION TEST
--------------------------------------------------

Input tender text:

"All bidders must submit the required documents along with their bids."

The AI must NOT invent:

GST requirement
PAN requirement
Udyam requirement
MSME requirement

unless those are actually stated.

The system should produce either:

no specific requirement

or:

a generic DOCUMENT requirement requiring officer review.

--------------------------------------------------
STEP 29 — DEMO APPROVAL TEST
--------------------------------------------------

Use:

"The bidder shall possess a valid and active GST registration."

AI returns:

AI_SUGGESTED

Officer opens review.

Officer clicks:

APPROVE

Expected:

status:

APPROVED

The requirement becomes available to the Compliance Engine.

--------------------------------------------------
STEP 30 — DEMO REJECTION TEST
--------------------------------------------------

AI suggests:

"Bidder must be registered with XYZ organization."

Officer rejects it.

Expected:

REJECTED

It must never be evaluated by Compliance Engine.

--------------------------------------------------
STEP 31 — EDIT TEST
--------------------------------------------------

AI suggests:

GST status == ACTIVE

Officer edits requirement:

GST state == Tamil Nadu

Then approves.

Expected:

The approved rule becomes:

FIELD_EQUALS

field:

state

expected:

Tamil Nadu

Compliance Engine uses the edited rule.

--------------------------------------------------
STEP 32 — COMPLIANCE INTEGRATION TEST
--------------------------------------------------

Create:

Requirement:

Active GST Registration

Rule:

status == ACTIVE

Status:

AI_SUGGESTED

Attempt compliance evaluation.

Expected:

NOT EVALUATED

Then approve requirement.

Run evaluation again.

Expected:

Compliance Engine evaluates it.

If government data says:

status = ACTIVE

Expected:

PASS

--------------------------------------------------
STEP 33 — SOURCE TRACEABILITY
--------------------------------------------------

For every extracted requirement verify:

Requirement
    ↓
Source Document
    ↓
Source Text
    ↓
Source Page/Section
    ↓
AI Suggestion
    ↓
Officer Approval
    ↓
Compliance Evaluation

This must be traceable.

--------------------------------------------------
STEP 34 — TESTING
--------------------------------------------------

Create tests for:

1. Requirement creation.
2. Requirement retrieval.
3. Requirement update.
4. Requirement approval.
5. Requirement rejection.
6. Invalid status transition.
7. AI requirement extraction.
8. Demo extractor.
9. GST extraction.
10. PAN extraction.
11. Tamil Nadu requirement extraction.
12. Unsupported requirement.
13. Source text preservation.
14. Source page preservation.
15. Empty tender text.
16. Invalid AI JSON.
17. AI provider failure.
18. Requirement rule validation.
19. APPROVED requirement evaluation.
20. AI_SUGGESTED requirement not evaluated.
21. REJECTED requirement not evaluated.
22. Requirement audit data.
23. Multiple requirements.
24. Multiple bidders using same tender requirements.

External AI providers must be mocked.

--------------------------------------------------
STEP 35 — MANUAL END-TO-END TEST
--------------------------------------------------

Create/use a fictional tender document containing:

"Tenderer shall possess a valid and active GST registration.

The bidder shall submit a valid PAN.

The bidder must be registered in Tamil Nadu.

The bidder shall not be debarred by any government authority."

Upload/associate the document with a fictional tender.

Run:

Extract Requirements

Expected:

AI suggestions appear.

They should NOT immediately become approved.

Review them.

Approve:

Active GST Registration

Approve:

Valid PAN

Edit and approve:

Tamil Nadu Registration

Reject one irrelevant/incorrect suggestion if necessary.

Then open the tender.

Expected:

Approved requirements are visible.

Rejected requirements are not active.

AI suggestions remain clearly distinguished from approved requirements.

--------------------------------------------------
STEP 36 — COMPLIANCE TEST
--------------------------------------------------

Use the approved GST requirement:

GST status == ACTIVE

Government verification:

ACTIVE

Run compliance evaluation.

Expected:

PASS

Use:

GST state == Tamil Nadu

Government verification:

Tamil Nadu

Expected:

PASS

Change government demo state:

Karnataka

Run evaluation.

Expected:

FAIL

The requirement result changes.

The tender requirement itself remains approved.

--------------------------------------------------
STEP 37 — PRESERVE EXISTING FEATURES
--------------------------------------------------

Verify:

- tender list works
- tender details work
- bidder list works
- bidder details work
- document upload works
- OCR works
- AI extraction works
- GST verification works
- PAN verification works
- Compliance Engine works
- Supabase works

Do not break existing functionality.

--------------------------------------------------
FILES RESTRICTION
--------------------------------------------------

Allowed:

backend/app/models/**
backend/app/schemas/**
backend/app/services/**
backend/app/api/**
backend/app/verification/**
backend/app/ai/**
backend/app/workers/**

frontend/src/pages/**
frontend/src/components/**
frontend/src/services/**

supabase/migrations/**
backend/tests/**

Only modify files directly related to:

- tender requirements
- tender document processing
- requirement extraction
- requirement review
- compliance integration

Do NOT rewrite:

backend/app/ocr/**

Do NOT rewrite:

backend/app/integrations/**

Do NOT rewrite the existing GST/PAN providers.

Do NOT rewrite the existing AI provider abstraction.

Do NOT rewrite the existing ComplianceEngine.

Extend existing components.

--------------------------------------------------
DEFINITION OF DONE
--------------------------------------------------

[ ] Tender documents can be associated with tenders
[ ] Tender text can be obtained through existing text/OCR infrastructure
[ ] TenderRequirementExtractor exists
[ ] Existing AI provider abstraction is reused
[ ] Demo requirement extractor exists
[ ] GST requirement extraction works
[ ] PAN requirement extraction works
[ ] Other requirements can be represented
[ ] Source text is preserved
[ ] Source page/section is preserved where available
[ ] AI suggestions are distinct from approved requirements
[ ] Requirement statuses exist
[ ] Status transitions are controlled
[ ] Manual requirement creation works
[ ] Requirement editing works
[ ] Requirement approval works
[ ] Requirement rejection works
[ ] Backend enforces approval
[ ] Only APPROVED requirements reach Compliance Engine
[ ] AI_SUGGESTED requirements cannot be evaluated
[ ] REJECTED requirements cannot be evaluated
[ ] Unsupported rules do not silently activate
[ ] Requirement data is stored in Supabase
[ ] Approval metadata is stored
[ ] Requirement source is traceable
[ ] Requirement extraction failure is handled
[ ] AI hallucination test passes
[ ] GST approval test passes
[ ] PAN approval test passes
[ ] Requirement editing test passes
[ ] Compliance integration test passes
[ ] Automated tests pass
[ ] Manual end-to-end test passes
[ ] Existing document processing works
[ ] Existing AI extraction works
[ ] Existing government verification works
[ ] Existing compliance engine works
[ ] Existing tender pages work
[ ] Existing bidder pages work

--------------------------------------------------
CRITICAL PRINCIPLE
--------------------------------------------------

There are now FOUR distinct layers:

1. EXTRACTION

Document → Information

2. VERIFICATION

Information → Government Evidence

3. COMPLIANCE

Evidence → Tender Requirement Result

4. OFFICER DECISION

Requirement Results → Procurement Decision

TASK 12 must NOT automate layer 4.

AI can assist with layer 1 and suggest configuration for layer 3.

The procurement officer remains responsible for approving tender requirements and making the final procurement decision.

--------------------------------------------------
STOP AFTER TASK 12
--------------------------------------------------

Do NOT implement TASK 13 automatically.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

Report:

1. Files modified.
2. Database changes.
3. Tender document association.
4. Tender requirement structure.
5. Requirement status lifecycle.
6. AI requirement extractor.
7. Demo extractor.
8. AI provider reused.
9. Supported requirement categories.
10. Supported rule types.
11. Source text handling.
12. Source page/section handling.
13. Approval workflow.
14. API endpoints.
15. Frontend changes.
16. Compliance Engine integration.
17. Tests executed.
18. Test results.
19. Hallucination test result.
20. Approval test result.
21. Rejection test result.
22. Edit test result.
23. Compliance integration result.
24. Confirmation that AI suggestions cannot automatically become active requirements.
25. Confirmation that final procurement decisions remain with the officer.
26. Confirmation that existing OCR, AI extraction, government verification, and compliance functionality remains intact.

STOP.
```

---

# 🧪 What you should manually verify

After the agent finishes, do these **four tests**.

### Test 1 — AI suggestion ≠ approved

Upload your fictional tender:

```text
The bidder shall possess a valid and active GST registration.

The bidder shall submit a valid PAN.

The bidder must be registered in Tamil Nadu.
```

Run extraction.

You should see:

```text
AI Suggested
──────────────
Active GST Registration
Valid PAN
Tamil Nadu Registration
```

They **must not automatically become APPROVED**.

---

### Test 2 — Officer approval

Click:

```text
Approve
```

on GST.

It should become:

```text
APPROVED
```

Now—and only now—it can enter the Compliance Engine.

---

### Test 3 — Officer edits AI

AI suggests:

```text
GST Status = ACTIVE
```

Edit it to:

```text
GST State = Tamil Nadu
```

Approve.

The actual active rule should be:

```text
FIELD_EQUALS
field = state
expected = Tamil Nadu
```

This demonstrates that **AI assists rather than controls the procurement logic**.

---

### Test 4 — Compliance

Government result:

```text
GST status = ACTIVE
GST state = Tamil Nadu
```

Approved requirements:

```text
GST status = ACTIVE
GST state = Tamil Nadu
```

Expected:

```text
GST Registration      ✅ PASS
Tamil Nadu GST        ✅ PASS
```

Then change government demo data:

```text
GST state = Karnataka
```

Expected:

```text
GST Registration      ✅ PASS
Tamil Nadu GST        ❌ FAIL
```

---

# 🧠 Architecture after TASK 12

This is now becoming a genuinely strong architecture:

```text
                 ┌──────────────────┐
                 │  TENDER DOCUMENT │
                 └────────┬─────────┘
                          ↓
                        OCR
                          ↓
                   Tender Text
                          ↓
                 AI Requirement
                   Extraction
                          ↓
              ┌─────────────────────┐
              │ AI SUGGESTED RULES  │
              └──────────┬──────────┘
                         ↓
                 OFFICER REVIEW
                    ↙         ↘
              APPROVE         REJECT
                 ↓
          APPROVED REQUIREMENT
                 ↓
          ┌──────────────────┐
          │ COMPLIANCE ENGINE│
          └────────┬─────────┘
                   ↓
          ┌─────────────────┐
          │     EVIDENCE    │
          └────────┬────────┘
                   ↓
      ┌────────────┴────────────┐
      ↓                         ↓
AI Extracted Data       Govt Verification
      │                         │
      └────────────┬────────────┘
                   ↓
              PASS / FAIL /
             NOT VERIFIED
                   ↓
          PROCUREMENT OFFICER
                   ↓
            FINAL DECISION
```

🔥 **The really important addition in TASK 12 is the human approval gate.**

That gives you a much stronger story for the SIH judges:

> **AI doesn't decide what the tender requires. AI extracts and suggests. The procurement officer validates the requirement. The deterministic engine evaluates the approved requirement against independently verified evidence.**

That separation makes the system considerably more defensible for an actual government procurement workflow.
