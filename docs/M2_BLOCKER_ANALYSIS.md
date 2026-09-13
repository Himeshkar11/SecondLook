# M2 Blocker Analysis and Resolution

## Original Blocker and Human Decision

Three bidder records are associated with one application user. The intended M2 invariant is one bidder profile per application user, but the live database currently contains three independent bidder records for that user.

The human decision confirmed that ABC Technologies Pvt Ltd (`...021`), XYZ Infrastructure Ltd (`...022`), and DEF Engineering Services Ltd (`...023`) are three separate development/demo organizations. They must not be merged or deleted, and their independent tender/document/OCR/AI history must remain attached to the original bidder IDs.

Before mutation, the affected rows were captured in the local uncommitted `m2_reconciliation_snapshot.json` rollback/audit snapshot.

## User

`00000000-0000-0000-0000-000000000001`

Read-only live facts:

- role: `admin`
- active: `true`
- bidder profiles: `3`
- tender memberships through those profiles: `3`

## Bidder Records

| Bidder ID | Name | Created | Updated | Status | References | Likely Role |
|---|---|---|---|---|---|---|
| `00000000-0000-0000-0000-000000000021` | ABC Technologies Pvt Ltd | 2026-09-11 15:21:14 UTC | 2026-09-11 16:16:03 UTC | verified | 1 tender, 2 documents | Bidder profile; canonical status cannot be selected yet |
| `00000000-0000-0000-0000-000000000022` | XYZ Infrastructure Ltd | 2026-09-11 15:21:14 UTC | 2026-09-11 15:21:14 UTC | pending | 1 tender, 2 documents, 1 OCR-completed document | Bidder profile; canonical status cannot be selected yet |
| `00000000-0000-0000-0000-000000000023` | DEF Engineering Services Ltd | 2026-09-11 15:21:14 UTC | 2026-09-11 15:21:14 UTC | flagged | 1 tender | Bidder profile; canonical status cannot be selected yet |

The three records share the same creation timestamp and have distinct business names, statuses, tender memberships, and histories. That pattern is consistent with a batch/demo or prior-development data load, but the repository does not contain the insert source.

## Dependency Analysis

The live schema contains these direct foreign-key references to `bidders.id`:

- `tender_bidders.bidder_id`
- `documents.bidder_id`
- `verification_jobs.bidder_id`
- `government_verifications.bidder_id`
- `requirement_evaluations.bidder_id`
- `compliance_evaluations.bidder_id`

There is no live `bids` table. The live schema also does not contain `officer_reviews` or `requirement_reviews`; those migration/model definitions exist in the repository but are not present in the live database queried during this investigation.

### Bidder `00000000-0000-0000-0000-000000000021`

- bids: no `bids` table exists; 0 applicable records.
- tender relationships: 1, tender `GEM/2026/B/892104`, `CPCL Procurement Tender — UPDATED`.
- documents: 2.
  - `gst_certificate.pdf`, status `uploaded`, OCR `PENDING`, AI `AI_PENDING`.
  - `integration_test_84eeb5a7.pdf`, status `QUEUED`, OCR `QUEUED`, AI `AI_PENDING`.
- document processing: 0 OCR-completed, 0 AI-completed.
- verification jobs: 0.
- government verifications: 0.
- verification results: 0.
- requirement evaluations: 0.
- compliance evaluations: 0.
- evidence: 0 stored evidence-bearing requirement-evaluation rows.
- officer reviews: not queryable because the live table does not exist.
- requirement reviews: not queryable because the live table does not exist.
- audit: 0 audit rows whose `entity_id` is this bidder ID.

### Bidder `00000000-0000-0000-0000-000000000022`

- bids: no `bids` table exists; 0 applicable records.
- tender relationships: 1, tender `GEM/2026/B/891950`, `Equipment Supply Tender`.
- documents: 2.
  - `test_gst_sample.pdf`, status `OCR_COMPLETED`, OCR `OCR_COMPLETED`, AI `AI_PENDING`.
  - `test_fail_sample.pdf`, status `QUEUED`, OCR `QUEUED`, AI `AI_PENDING`.
- document processing: 1 OCR-completed, 0 AI-completed.
- verification jobs: 0.
- government verifications: 0.
- verification results: 0.
- requirement evaluations: 0.
- compliance evaluations: 0.
- evidence: 0 stored evidence-bearing requirement-evaluation rows.
- officer reviews: not queryable because the live table does not exist.
- requirement reviews: not queryable because the live table does not exist.
- audit: 0 audit rows whose `entity_id` is this bidder ID.

### Bidder `00000000-0000-0000-0000-000000000023`

- bids: no `bids` table exists; 0 applicable records.
- tender relationships: 1, tender `GEM/2026/B/889412`, `Maintenance Services Tender`.
- documents: 0.
- document processing: 0 OCR-completed, 0 AI-completed.
- verification jobs: 0.
- government verifications: 0.
- verification results: 0.
- requirement evaluations: 0.
- compliance evaluations: 0.
- evidence: 0 stored evidence-bearing requirement-evaluation rows.
- officer reviews: not queryable because the live table does not exist.
- requirement reviews: not queryable because the live table does not exist.
- audit: 0 audit rows whose `entity_id` is this bidder ID.

## Root Cause

The repository's current Supabase seed file only seeds `demo_government_records`; it does not insert users, bidders, tenders, or documents. The historical core migration creates those tables but contains no domain data inserts. The application currently exposes bidder list/detail reads and bidder document upload/list routes, but no bidder-creation endpoint or bidder-creation service was found. The tests create bidder rows only in isolated SQLite fixtures.

The exact live insert source is therefore not present in the repository. The deterministic IDs, shared creation timestamp, three distinct demo-style names, and separate tender/document histories strongly suggest prior development or an external demo-data load. This is evidence of origin, not proof; no source-level claim can identify the creator conclusively.

## Reconciliation Classification

**B. Three legitimate organizations incorrectly attached to one legacy user** is the best-supported classification from the available data.

Evidence:

- The three rows have different legal names, registration numbers, GST numbers, and PAN numbers.
- They belong to three different tenders with different references and statuses.
- They have different bidder statuses: `verified`, `pending`, and `flagged`.
- Two organizations have document histories, including one OCR-completed document.

This classification does not establish the correct future application user for each organization. The current user is `admin@gem.gov.in`, `CPCL / Ministry of Petroleum`, active, with legacy role `admin`. Those fields identify a legacy procurement/system user, not a verified owner for any of the three private bidder organizations.

## Canonical Record

**MANUAL RECONCILIATION REQUIRED**

No bidder can be safely selected as canonical:

- `...021` has a tender relationship and two documents.
- `...022` has a different tender relationship and two documents, including OCR-completed processing history.
- `...023` has a different tender relationship and a flagged status.

Selecting by oldest/newest, verified status, or bidder name would discard or orphan independent tender/document history and could change the meaning of existing compliance workflows. There are no compliance/evidence records to resolve, but the tender and document histories are meaningful and belong to distinct business names.

The safest target structure is one application user per organization, with the existing bidder UUIDs preserved. The repository does not provide approved identity-provider subjects or ownership details for those organizations, so target users cannot be created or selected safely by automation. The current `admin@gem.gov.in` user must not be reassigned merely because it currently owns all three rows.

## Reconciliation Table

| Bidder ID | Organization | Tender count | Document count | Processing history | Current user | Proposed user | Proposed action | Reason | Confidence |
|---|---|---:|---:|---|---|---|---|---|---|
| `...021` | ABC Technologies Pvt Ltd | 1 | 2 | Uploaded/queued GST documents; no completed OCR/AI | Legacy user `...001` | Unknown; requires approved owner identity | Preserve bidder ID; reassign only after approval | Independent organization and tender history | High for separate organization; insufficient for target owner |
| `...022` | XYZ Infrastructure Ltd | 1 | 2 | One OCR-completed document and one queued document | Legacy user `...001` | Unknown; requires approved owner identity | Preserve bidder ID; reassign only after approval | Independent organization and processing history | High for separate organization; insufficient for target owner |
| `...023` | DEF Engineering Services Ltd | 1 | 0 | No document processing history | Legacy user `...001` | Unknown; requires approved owner identity | Preserve bidder ID; reassign only after approval | Independent organization, tender, and flagged status | High for separate organization; insufficient for target owner |

The proposed action is deliberately preparatory, not an executed mutation. No target user IDs, emails, or identity-provider subjects are available to authorize reassignment.

## Data Preservation Requirements

Any later remediation must preserve:

- all three bidder IDs until a business owner approves a disposition;
- all three tender memberships and their tender IDs;
- all four document rows and their OCR/AI lifecycle fields;
- all timestamps, statuses, names, and registration data;
- any future verification, evaluation, evidence, review, or audit rows created before remediation;
- existing user, tender, document, and foreign-key IDs.

No automated merge, delete, reassignment, or status rewrite is approved by this investigation.

## Legacy Roles

Read-only role census:

| Role | User count | Users with bidder profiles |
|---|---:|---:|
| `admin` | 1 | 1 |

No live `procurement_officer` role appeared in the grouped role result. The affected user is active and has role `admin`.

The M2 compatibility constraint allows `admin` and `procurement_officer` temporarily, alongside canonical `BIDDER` and `OFFICER`. No role values were changed. The affected user's role cannot be safely mapped until the three bidder records are reconciled and the user's intended product role is confirmed.

There are currently zero live `procurement_officer` users. No automatic `ADMIN -> OFFICER` or `ADMIN -> BIDDER` conversion is approved.

## Migration Result

The file `supabase/migrations/20260913_add_user_role_profiles.sql` was applied in one PostgreSQL transaction after reconciliation.

Its behavior is:

- changes the default for new `users.role` values to `OFFICER`;
- adds a role check allowing canonical `BIDDER`/`OFFICER` plus explicit temporary legacy values `admin`/`procurement_officer`;
- checks for duplicate `bidders.user_id` values and raises an exception before uniqueness enforcement;
- creates `uq_bidders_user_id` only after the duplicate check passes;
- creates `officer_profiles` with a unique `user_id` and `ON DELETE CASCADE` to `users`;
- does not change the legacy `admin` role;
- does not delete or merge bidder rows;
- does not move any tender, document, OCR/AI, verification, compliance, evidence, or audit relationship.

The duplicate guard correctly prevented unsafe enforcement before reconciliation. After reconciliation, it passed and created `uq_bidders_user_id`, the role check, and `officer_profiles` with unique `user_id`.

Reconciliation result:

| Application user | Role | Bidder profile |
|---|---|---|
| `...001` `admin@gem.gov.in` | unchanged `admin` | none |
| `...031` `demo.bidder.abc@secondlook.local` | `BIDDER` | `...021` ABC Technologies Pvt Ltd |
| `...032` `demo.bidder.xyz@secondlook.local` | `BIDDER` | `...022` XYZ Infrastructure Ltd |
| `...033` `demo.bidder.def@secondlook.local` | `BIDDER` | `...023` DEF Engineering Services Ltd |

Users inserted: 3. Bidder ownership updates: 3. Rows deleted: 0.

## Test Environment

- `backend/pytest.ini` exists and configures `pythonpath = .` and `testpaths = tests`.
- No `backend/.venv` directory exists; the repository root `.venv` is present and usable.
- No `pyproject.toml`, `requirements-dev.txt`, `setup.cfg`, `tox.ini`, `Pipfile`, or `poetry.lock` was found.
- `backend/requirements.txt` does not include pytest.
- The root `.venv` provides `pytest 9.1.1`.
- Focused M2 tests ran from `backend` with the root environment: `6 passed`.
- The read-only database queries were run through the installed `psycopg` driver by adapting the configured SQLAlchemy URL from `postgresql://` to `postgresql+psycopg://`.
- Full backend regression suite: `354 passed, 1 warning`.
- Four existing isolation tests were updated to use separate test users for separate bidder profiles; no tests were weakened or removed.

## Executed Resolution and Verification

1. Confirmed three separate demo organizations; no canonical bidder was selected.
2. Inserted three deterministic application users with role `BIDDER`; no passwords or Supabase Auth accounts were created.
3. Updated only `bidders.user_id` for `...021`, `...022`, and `...023`.
4. Left legacy user `...001` and role `admin` unchanged.
5. Verified all six direct bidder foreign-key tables. Counts remain: 3 tender memberships, 4 documents, 0 verification jobs, 0 government verifications, 0 requirement evaluations, 0 compliance evaluations, and 0 audit references.
6. Verified all three bidder IDs and all four document IDs remain present; document OCR/AI states are unchanged.
7. Verified duplicate bidder-user groups = 0, legacy admin bidder profiles = 0, and each affected bidder has exactly one owner.
8. Applied and verified the M2 migration, then ran focused and full regression tests.

## What MUST NOT Be Done

- Do not delete any of the three bidder rows.
- Do not merge the records automatically.
- Do not choose the oldest, newest, verified, pending, or flagged row as canonical without business approval.
- Do not reassign tender memberships or documents automatically.
- Do not update the live role from `admin` automatically.
- Do not merge or delete the three confirmed demo organizations.
- Do not delete or move their historical tender/document/OCR/AI/verification/compliance/evidence/audit data.
- Do not convert the legacy `admin` user into a bidder.
- Do not create passwords, Supabase Auth accounts, authentication, or authorization in M2.

## Investigation Commands and Safety

The preflight SQL was read-only. The approved reconciliation used one guarded transaction with strict preconditions and no delete statements. The migration used a separate transaction. No commit or push was created in Git.

M2 does not implement authentication, signup, frontend RBAC, route guards, dashboards, password handling, JWT handling, Supabase Auth, or authorization. M3 begins from the completed database identity/profile foundation.

**MILESTONE 02 COMPLETE — RBAC DATABASE FOUNDATION READY FOR MILESTONE 03**
