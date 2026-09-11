# 🚀 TASK 17 — Tender Evaluation Dashboard & Procurement Officer Workspace

Assuming **TASK 16 — Officer Review Layer** is completed successfully, TASK 17 should now build the **main procurement officer workspace**.

The goal is to move from individual compliance-review screens to a **complete tender-level dashboard** where an officer can quickly understand what is happening across all bidders.

> **Important:** This is a visualization and workflow layer. It must not change the underlying compliance engine or automatically decide bidder eligibility.

---

# 🎯 Objective

Build a dynamic:

## **Tender Evaluation Dashboard**

The officer should be able to open a tender and see:

```text
Tender
  ↓
Requirements
  ↓
All Bidders
  ↓
Compliance Evaluations
  ↓
Officer Reviews
  ↓
Evidence / Issues
```

The dashboard should answer:

* How many bidders submitted?
* How many have been evaluated?
* How many are still processing?
* How many have passed all requirements?
* How many have failures?
* Which bidders require officer attention?
* Which requirements are causing the most failures?
* Which reviews are incomplete?
* What actions should the officer take next?

---

# 🖥️ Target UI

The page should look roughly like:

```text
← Tenders

Tender Evaluation
────────────────────────────────────────

Industrial Equipment Procurement

Tender ID: TND-2026-001
Status: Evaluation

────────────────────────────────────────

Overview

┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ 12         │ │ 10         │ │ 7          │ │ 2          │
│ Bidders    │ │ Evaluated  │ │ Completed  │ │ Attention  │
└────────────┘ └────────────┘ └────────────┘ └────────────┘

────────────────────────────────────────

Bidder Evaluation

Bidder                     Compliance     Review       Action
─────────────────────────────────────────────────────────────
ABC Technologies            92%           Completed    View
XYZ Industries              81%           Pending      Review
DEF Engineering              67%           Attention    Review
PQR Systems                  —             Not Started  Evaluate

────────────────────────────────────────

Requirement Issues

GST Registration             10/12 PASS
PAN                          11/12 PASS
UDYAM                         8/12 PASS
Local Content                 7/12 PASS
OEM Authorization             6/12 PASS

────────────────────────────────────────
```

Keep it **minimal, professional and government-portal-like**.

---

# 📁 Files to create

First inspect the existing frontend/backend structure.

Create only if equivalent functionality does not already exist:

```text
backend/
└── app/
    └── dashboard/
        ├── __init__.py
        ├── schemas.py
        ├── service.py
        ├── repository.py
        └── router.py

frontend/
└── src/
    ├── services/
    │   └── dashboardService.js
    │
    └── components/
        └── dashboard/
            ├── TenderEvaluationDashboard.jsx
            ├── EvaluationStats.jsx
            ├── BidderEvaluationTable.jsx
            ├── RequirementIssueSummary.jsx
            └── EvaluationStatusBadge.jsx
```

If an equivalent dashboard structure already exists:

> **Extend it. Do not create duplicate dashboard architecture.**

---

# 🔐 Allowed modifications

The vibe coder may modify:

```text
backend/app/main.py
```

to register the dashboard router.

Existing frontend routing/navigation files may be modified **only to expose the dashboard page**.

Existing shared UI components may be reused or minimally extended.

---

# ❌ DO NOT MODIFY

Do not modify:

```text
backend/app/ai/
backend/app/ocr/
backend/app/government/
backend/app/compliance/
backend/app/review/
backend/app/documents/
```

The dashboard must consume their existing APIs/services.

Do not alter:

* compliance rules
* government verification
* AI extraction
* OCR
* officer-review logic

---

# 🧠 STEP 1 — Dashboard Data Model

Do **not** create a duplicate database representation of compliance.

The dashboard should aggregate existing data.

Conceptually:

```text
Tender
 ├── Requirements
 ├── Bidders
 │    └── Compliance Evaluations
 │         └── Officer Reviews
 │              └── Requirement Results
```

The dashboard service should aggregate these existing records.

---

# 📊 STEP 2 — Tender Statistics

Create a summary object such as:

```json
{
  "tender_id": "tender-001",
  "total_bidders": 12,
  "evaluated": 10,
  "not_started": 2,
  "processing": 0,
  "completed": 7,
  "attention_required": 2,
  "reviews_completed": 6,
  "reviews_pending": 4
}
```

These numbers must come from real database data.

Do **not** hard-code them in React.

---

# 👥 STEP 3 — Bidder Evaluation Summary

Each bidder should have a summarized evaluation.

Example:

```json
{
  "bidder_id": "bidder-001",
  "bidder_name": "ABC Technologies Pvt Ltd",
  "evaluation_status": "COMPLETED",
  "total_requirements": 10,
  "passed": 8,
  "failed": 1,
  "partial": 1,
  "not_verified": 0,
  "compliance_percentage": 80,
  "review_status": "COMPLETED",
  "officer_decision": "REQUIRES_CLARIFICATION"
}
```

### Important

`compliance_percentage` is a **summary metric only**.

Do not display:

> "80% = Qualified"

Instead display:

> **Compliance assessment: 80%**

and separately:

> **Officer decision: Requires Clarification**

---

# 📐 STEP 4 — Compliance Percentage

Calculate:

```text
passed / applicable requirements × 100
```

Do not count:

```text
NOT_APPLICABLE
```

in the denominator.

Example:

```text
10 total
1 NOT_APPLICABLE
8 PASS

8 / 9 × 100
= 88.9%
```

Round to an appropriate display value such as:

```text
89%
```

### Critical

Do not use percentage to automatically determine:

```text
QUALIFIED
NOT_QUALIFIED
```

Officer decision remains independent.

---

# 🚦 STEP 5 — Attention Required

Create deterministic rules for identifying bidders requiring attention.

For example:

```text
FAILED requirement
OR
PARTIAL requirement
OR
NOT_VERIFIED mandatory requirement
OR
review not completed
```

Return something like:

```json
{
  "attention_required": true,
  "attention_reasons": [
    "Mandatory requirement not verified",
    "Officer review incomplete"
  ]
}
```

This is an **attention indicator**, not an eligibility decision.

---

# 📋 STEP 6 — Bidder Table

Create a dynamic table:

| Bidder           | Evaluation | Passed | Failed | Not Verified | Review    | Action |
| ---------------- | ---------- | -----: | -----: | -----------: | --------- | ------ |
| ABC Technologies | 89%        |      8 |      1 |            0 | Completed | View   |
| XYZ Industries   | 72%        |      6 |      2 |            1 | Pending   | Review |
| DEF Engineering  | Processing |      — |      — |            — | —         | View   |

Actions:

```text
View Evaluation
Review
View Evidence
```

Do not add:

```text
Approve Bidder
Reject Bidder
Award Bid
```

to this dashboard.

---

# 🔎 STEP 7 — Requirement Issue Summary

The dashboard should also aggregate requirement-level failures.

Example:

```text
Requirement Issues

GST Registration
✓ 10 PASS
✕ 1 FAIL
! 1 NOT VERIFIED

PAN
✓ 11 PASS
✕ 1 FAIL

UDYAM
✓ 8 PASS
! 4 NOT VERIFIED

OEM Authorization
✓ 6 PASS
✕ 2 FAIL
! 4 NOT VERIFIED
```

This helps the officer identify recurring problems.

---

# 🧮 STEP 8 — Requirement Statistics API

Expose something similar to:

```http
GET /api/v1/tenders/{tender_id}/dashboard/requirements
```

Example response:

```json
[
  {
    "requirement_id": "req-001",
    "title": "GST Registration",
    "total": 12,
    "passed": 10,
    "failed": 1,
    "partial": 0,
    "not_verified": 1
  }
]
```

---

# 🔌 STEP 9 — Main Dashboard API

Expose:

```http
GET /api/v1/tenders/{tender_id}/dashboard
```

Response:

```json
{
  "tender": {},
  "summary": {},
  "bidders": [],
  "requirement_issues": []
}
```

This endpoint should provide everything necessary for the primary dashboard.

Avoid making the frontend perform a large number of individual requests.

---

# ⚡ STEP 10 — Performance

Because this is a tender-level dashboard, potentially containing many bidders, avoid:

```text
1 tender
↓
12 bidders
↓
12 separate evaluation requests
↓
120 requirement requests
```

That creates an N+1 request problem.

Prefer backend aggregation:

```text
React
 ↓
GET /dashboard
 ↓
DashboardService
 ↓
Database queries
 ↓
Aggregated response
```

Use efficient database queries and indexes where necessary.

Do not prematurely introduce Redis, Elasticsearch, Kafka, etc.

---

# 🖱️ STEP 11 — Dashboard Navigation

From the tender detail page:

```text
Tender Details
       ↓
[Open Evaluation Dashboard]
       ↓
Tender Evaluation Dashboard
```

From the dashboard:

```text
Bidder
 ↓
View Evaluation
 ↓
Compliance Evaluation
 ↓
Officer Review
```

Existing routes should be reused.

---

# 🔄 STEP 12 — Dynamic Updates

When an officer completes a review and returns to the dashboard:

```text
Review Completed
       ↓
Dashboard refresh
       ↓
Statistics updated
```

For example:

Before:

```text
Reviews Completed: 5
Reviews Pending: 5
```

After:

```text
Reviews Completed: 6
Reviews Pending: 4
```

Do not implement WebSockets in this task.

A normal refresh/refetch is sufficient.

---

# 🧪 STEP 13 — Backend Tests

Create tests for:

### Test 1

Tender with no bidders:

```text
total_bidders = 0
```

Dashboard should load successfully.

---

### Test 2

Tender with bidders but no evaluations:

```text
12 bidders
12 not started
```

---

### Test 3

Mixed evaluation states:

```text
3 completed
2 processing
1 failed
4 not started
```

Verify aggregation.

---

### Test 4

Compliance statistics

Given:

```text
10 requirements
7 PASS
1 FAIL
1 PARTIAL
1 NOT_VERIFIED
```

Verify:

```text
passed = 7
failed = 1
partial = 1
not_verified = 1
```

---

### Test 5

Percentage

Given:

```text
10 requirements
1 NOT_APPLICABLE
8 PASS
1 FAIL
```

Expected:

```text
88.9%
```

or appropriate rounded representation.

---

### Test 6

Attention detection

Given:

```text
mandatory requirement = NOT_VERIFIED
```

Expected:

```text
attention_required = true
```

---

### Test 7

Officer decision independence

A bidder with:

```text
90% compliance
```

must **not** automatically receive:

```text
QUALIFIED
```

---

### Test 8

Requirement issue aggregation

Verify each requirement's:

```text
PASS
FAIL
PARTIAL
NOT_VERIFIED
```

counts.

---

### Test 9

404

Request:

```text
GET /api/v1/tenders/nonexistent/dashboard
```

Expected:

```text
404
```

---

# 🧪 Manual Test

Use the existing demo tender.

Create/use several bidders with different evaluation states.

For example:

```text
ABC
8 PASS
1 FAIL
1 NOT_VERIFIED
Review completed

XYZ
7 PASS
2 FAIL
1 PARTIAL
Review pending

DEF
Evaluation processing

PQR
No evaluation
```

Open:

```text
Tender
 ↓
Evaluation Dashboard
```

Verify the dashboard displays the real values.

Then open:

```text
ABC
 ↓
View Evaluation
 ↓
Officer Review
```

Change the officer review.

Return to dashboard.

Expected:

```text
Dashboard statistics update
```

without hardcoded values.

---

# 🎨 UI Rules

Keep the existing government style.

### Colors

```text
PASS              → green
FAIL              → red
PARTIAL           → orange
NOT_VERIFIED      → orange
PROCESSING        → blue
INFORMATION       → blue
```

Avoid:

```text
large gradients
glassmorphism
excessive animation
neon colors
huge hero sections
```

The dashboard should feel like:

> **A serious government procurement application, not a SaaS marketing website.**

---

# 🚨 VERY IMPORTANT ARCHITECTURAL RULE

TASK 17 is **read/aggregation focused**.

The dashboard should consume:

```text
TASK 03 → Tender data
TASK 04 → Bidder data
TASK 05 → Tender details
TASK 06 → Bidder details
TASK 11 → Compliance
TASK 13 → Evaluation
TASK 15 → Evidence
TASK 16 → Officer Review
```

It should **not recreate their logic**.

Architecture:

```text
                    ┌── Tender Service
                    │
                    ├── Bidder Service
                    │
Dashboard Service ──┼── Compliance Service
                    │
                    ├── Evaluation Service
                    │
                    └── Review Service
```

Then:

```text
Dashboard API
     ↓
React Dashboard
```

---

# ✅ Definition of Done

TASK 17 is complete when:

* [ ] Tender evaluation dashboard exists
* [ ] Dashboard uses dynamic database data
* [ ] Bidder statistics are dynamic
* [ ] Evaluation statistics are dynamic
* [ ] Review statistics are dynamic
* [ ] Compliance summary is displayed
* [ ] Requirement issue summary is displayed
* [ ] Attention indicators work
* [ ] Compliance percentage is calculated correctly
* [ ] NOT_APPLICABLE is excluded from percentage denominator
* [ ] Dashboard does not make automatic qualification decisions
* [ ] Existing evidence/review/evaluation pages are linked
* [ ] No N+1 frontend request pattern
* [ ] Loading state works
* [ ] Empty state works
* [ ] Error state works
* [ ] 404 handling works
* [ ] Backend tests pass
* [ ] Manual test passes
* [ ] Existing TASK 01–16 functionality remains intact

---

# 📋 COPY THIS TO YOUR VIBE CODER

```text
TASK 17 — Build the Tender Evaluation Dashboard & Procurement Officer Workspace.

Assume TASK 16 is fully implemented and working.

OBJECTIVE:

Build a dynamic tender-level evaluation dashboard that allows a procurement officer to see the status of all bidders, compliance evaluations, officer reviews, and requirement-level issues.

The dashboard is an aggregation/read layer.

CRITICAL RULE:

Do NOT automatically qualify, disqualify, reject, approve, or award any bidder.

Compliance percentage is only a summary metric.

Officer decision remains independent and comes from TASK 16.

ARCHITECTURE:

Tender
 ↓
Bidders
 ↓
Compliance Evaluations
 ↓
Officer Reviews
 ↓
Tender Evaluation Dashboard

BACKEND:

Create/reuse:

backend/app/dashboard/
    __init__.py
    schemas.py
    service.py
    repository.py
    router.py

Create:

GET
/api/v1/tenders/{tender_id}/dashboard

GET
/api/v1/tenders/{tender_id}/dashboard/requirements

Dashboard response should contain:

{
  tender,
  summary,
  bidders,
  requirement_issues
}

Summary should include:

total_bidders
evaluated
not_started
processing
completed
attention_required
reviews_completed
reviews_pending

Bidder summary should include:

bidder_id
bidder_name
evaluation_status
total_requirements
passed
failed
partial
not_verified
not_applicable
compliance_percentage
review_status
officer_decision
attention_required
attention_reasons

Compliance percentage:

passed / applicable requirements * 100

Exclude NOT_APPLICABLE from the denominator.

Do NOT use compliance percentage to automatically determine qualification.

Attention required should be deterministic.

Examples:

FAILED requirement
OR
PARTIAL requirement
OR
mandatory NOT_VERIFIED requirement
OR
incomplete officer review

Requirement issue statistics should contain:

requirement_id
title
total
passed
failed
partial
not_verified
not_applicable

PERFORMANCE:

Avoid N+1 frontend requests.

Prefer:

React
 ↓
GET /dashboard
 ↓
DashboardService
 ↓
efficient DB aggregation
 ↓
single aggregated response

Do not introduce unnecessary Redis/Kafka/etc.

FRONTEND:

Create/reuse:

frontend/src/services/dashboardService.js

frontend/src/components/dashboard/
    TenderEvaluationDashboard.jsx
    EvaluationStats.jsx
    BidderEvaluationTable.jsx
    RequirementIssueSummary.jsx
    EvaluationStatusBadge.jsx

Dashboard should show:

- Tender information
- Total bidders
- Evaluated bidders
- Completed evaluations
- Pending evaluations
- Attention required
- Review completion statistics
- Bidder evaluation table
- Requirement issue summary

Bidder table should contain:

Bidder
Evaluation
Passed
Failed
Not Verified
Review
Action

Actions may include:

View Evaluation
Review
View Evidence

DO NOT add:

Approve Bidder
Reject Bidder
Award Bid

NAVIGATION:

Tender Detail
 ↓
Open Evaluation Dashboard
 ↓
Tender Evaluation Dashboard
 ↓
Bidder Evaluation
 ↓
Officer Review

Reuse existing routes where possible.

UI:

Use the existing minimalist government portal style.

Colors:

PASS = green
FAIL = red
PARTIAL = orange
NOT_VERIFIED = orange
PROCESSING = blue
INFO = blue

Do not use excessive gradients, animations, glassmorphism, or marketing-style UI.

TESTS:

1. Tender with no bidders
2. Bidders with no evaluations
3. Mixed evaluation states
4. Compliance aggregation
5. Correct percentage calculation
6. NOT_APPLICABLE exclusion
7. Attention detection
8. Officer decision remains independent
9. Requirement issue aggregation
10. Tender 404
11. Dashboard persistence after refresh

MANUAL TEST:

Use several demo bidders:

ABC:
8 PASS
1 FAIL
1 NOT_VERIFIED
Review completed

XYZ:
7 PASS
2 FAIL
1 PARTIAL
Review pending

DEF:
Processing

PQR:
No evaluation

Open the tender evaluation dashboard.

Verify all values are dynamically loaded.

Open ABC evaluation.

Open officer review.

Change the review.

Return to dashboard.

Verify dashboard statistics update after refresh.

STRICT SCOPE:

Do NOT modify:

backend/app/ai/
backend/app/ocr/
backend/app/government/
backend/app/compliance/
backend/app/review/
backend/app/documents/

Do not duplicate existing compliance, evidence, evaluation, or review logic.

Do not introduce automatic bidder decisions.

Do not implement WebSockets.

Do not start TASK 18.

At the end report:

1. Files created
2. Files modified
3. APIs added
4. Database changes
5. Tests executed
6. Manual test result

STOP AFTER TASK 17.
```

🔥 **TASK 17 gives you the actual tender-level command center.** After this, the project has a strong chain from **document → OCR → AI extraction → government verification → compliance → evidence → officer review → tender dashboard**, while keeping each layer isolated for your team to work on safely.
