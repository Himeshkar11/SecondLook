# M2 Blocker Analysis

## Blocker

Three bidder records are associated with one application user. The intended M2 invariant is one bidder profile per application user, but the live database currently contains three independent bidder records for that user.

This investigation was read-only. No `DELETE`, `UPDATE`, `TRUNCATE`, `DROP`, `ALTER TABLE`, `MERGE`, or migration application was performed.

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

## Canonical Record

**MANUAL RECONCILIATION REQUIRED**

No bidder can be safely selected as canonical:

- `...021` has a tender relationship and two documents.
- `...022` has a different tender relationship and two documents, including OCR-completed processing history.
- `...023` has a different tender relationship and a flagged status.

Selecting by oldest/newest, verified status, or bidder name would discard or orphan independent tender/document history and could change the meaning of existing compliance workflows. There are no compliance/evidence records to resolve, but the tender and document histories are meaningful and belong to distinct business names.

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

## Migration Safety

The file `supabase/migrations/20260913_add_user_role_profiles.sql` was inspected and not applied.

Its behavior is:

- changes the default for new `users.role` values to `OFFICER`;
- adds a role check allowing canonical `BIDDER`/`OFFICER` plus explicit temporary legacy values `admin`/`procurement_officer`;
- checks for duplicate `bidders.user_id` values and raises an exception before uniqueness enforcement;
- creates `uq_bidders_user_id` only after the duplicate check passes;
- creates `officer_profiles` with a unique `user_id` and `ON DELETE CASCADE` to `users`;
- does not change existing role values;
- does not delete, merge, or reassign bidder rows.

The duplicate guard is safe and correctly prevents an unsafe migration. The migration cannot apply successfully to the current live data until manual reconciliation is completed.

## Test Environment

- `backend/pytest.ini` exists and configures `pythonpath = .` and `testpaths = tests`.
- No `backend/.venv` directory exists.
- No `pyproject.toml`, `requirements-dev.txt`, `setup.cfg`, `tox.ini`, `Pipfile`, or `poetry.lock` was found.
- `backend/requirements.txt` does not include pytest.
- `pytest` is not available as a command and `python -m pytest` reports that the module is not installed.
- The read-only database queries were run through the installed `psycopg` driver by adapting the configured SQLAlchemy URL from `postgresql://` to `postgresql+psycopg://`.
- No packages were installed during this investigation.

## Recommended Resolution

1. Have the product/data owner identify whether the three names are intentionally separate businesses incorrectly attached to one application user, or whether the records are test/demo artifacts.
2. Freeze changes to this user and these bidder rows while reconciliation is pending.
3. For each row, capture an approved disposition: retain as the user-owned bidder, transfer to a separate application user, or mark as an explicitly deprecated demo record. Do not delete history.
4. If multiple records remain valid, create separate application users or revise the one-profile invariant through an approved architecture decision; do not force a one-to-one constraint.
5. Recheck all foreign-key and transitive references after the approved disposition.
6. Classify the user's legacy `admin` role explicitly as `BIDDER` or `OFFICER` only after the profile decision; do not infer it from status or name.
7. Apply the M2 migration only after the duplicate query returns zero rows and the role mapping has been reviewed.
8. Re-run focused database tests and the existing regression suite in an environment with the repository's test dependencies installed.

## What MUST NOT Be Done

- Do not delete any of the three bidder rows.
- Do not merge the records automatically.
- Do not choose the oldest, newest, verified, pending, or flagged row as canonical without business approval.
- Do not reassign tender memberships or documents automatically.
- Do not update the live role from `admin` automatically.
- Do not apply `20260913_add_user_role_profiles.sql` yet.
- Do not start Milestone 03.
- Do not modify backend code, frontend code, migrations, or live data during this blocker phase.

## Investigation Commands and Safety

All live SQL used for this report was read-only `SELECT` against `information_schema` and domain tables. No write statement was executed. The repository checks performed were source reads, searches, and environment inspection only.

**MILESTONE 02 REMAINS BLOCKED — AWAITING DATA RESOLUTION**
