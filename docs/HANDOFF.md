# SecondLook Milestone 01 Handoff

## Exact Stopping Point

Milestone 02 is complete. Authentication, RBAC, role middleware, signup, dashboards, landing redesign, and bid submission were not implemented. The duplicate bidder-user records were reconciled without deleting or merging any organization or history, and the additive migration applied successfully.

The investigation and executed resolution are documented in [docs/M2_BLOCKER_ANALYSIS.md](M2_BLOCKER_ANALYSIS.md). The local rollback snapshot is `m2_reconciliation_snapshot.json` and is intentionally uncommitted.

## Repository Structure Discovered

```text
backend/app/main.py                 FastAPI application entry point
backend/app/api/router.py           Versioned domain API router
backend/app/api/deps.py             DB and placeholder request context dependencies
backend/app/models/                 SQLAlchemy domain models
backend/app/services/               Domain services
backend/app/database/               SQLAlchemy connection and repositories
backend/app/workers/                In-process job records, queues, and workers
backend/app/ocr/                    OCR abstractions and processors
backend/app/ai/                     AI extraction abstractions/providers
backend/app/integrations/           Government integration/provider adapters
backend/app/verification/           Rules, scoring, evidence, explanation, pipeline
backend/app/dashboard/              Task 17 dashboard aggregation
backend/app/review/                 Task 16 officer review lifecycle
backend/tests/                     Unit/integration tests for existing behavior
frontend/src/main.jsx               React/Vite entry point and BrowserRouter
frontend/src/App.jsx                Current route tree
frontend/src/api/client.js          Fetch-based API client
frontend/src/services/              API service wrappers
frontend/src/components/layout/     MainLayout, Header, Sidebar
frontend/src/pages/                 Current dashboard/domain pages
supabase/migrations/                PostgreSQL schema history
supabase/seed.sql                   Demo seed data
```

No Alembic directory or `pyproject.toml` was found. Database schema changes are represented by Supabase SQL migrations.

## Important Files Inspected

- `backend/app/main.py`
- `backend/app/api/deps.py`
- `backend/app/api/router.py`
- `backend/app/dashboard/router.py` and `service.py`
- `backend/app/review/router.py` and `service.py`
- `backend/app/models/user.py`, `bidder.py`, `tender.py`, `document.py`, `tender_requirement.py`, `government_verification.py`, `audit_log.py`
- `backend/app/services/document_service.py`, `compliance_service.py`, `government_verification_service.py`, `audit_service.py`, `tender_service.py`, `bidder_service.py`
- `backend/app/workers/worker.py`
- `frontend/src/main.jsx`, `App.jsx`, `api/client.js`
- `frontend/src/components/layout/Header.jsx`, `Sidebar.jsx`, `MainLayout.jsx`
- `frontend/src/pages/DashboardPage.jsx`, `TendersPage.jsx`, `TenderDetailPage.jsx`, `BiddersPage.jsx`, `BidderDetailPage.jsx`, `DocumentsPage.jsx`, `VerificationPage.jsx`, `AuditPage.jsx`, `TenderWorkflowPage.jsx`
- `frontend/src/components/dashboard/TenderEvaluationDashboard.jsx`
- `frontend/src/components/compliance/` review/evidence components
- All inspected SQL files under `supabase/migrations/`
- Backend tests for database config, bidders, bidder details, documents, OCR, AI, government verification, evidence, compliance, officer review, and tender workflow.

## Current Authentication State

There is no implemented login, signup, JWT, session cookie, bearer-token parsing, Supabase Auth client, auth state store, protected route, or backend auth dependency.

The local `users` table and SQLAlchemy `User` model are application records with `id`, email, full name, free-form role, active flag, and timestamps. The role default is legacy `admin`; tests create `procurement_officer`. The frontend `/login` route is a placeholder and the header displays a hard-coded `Auditor Officer`. Theme preference is the only current `localStorage` usage.

## Current Database State

The existing identity-like graph is:

```text
users
  -> bidders.user_id
  -> tenders.created_by
  -> tender_requirements.created_by / approved_by
  -> officer_reviews.reviewer_id
  -> requirement_reviews.reviewed_by
  -> audit_logs.user_id
```

`bidders` contains legal and registration data and points to `users`, but `user_id` is not unique. There is no `officer_profiles` table. There is no `bids` table or Bid model; `tender_bidders` is a many-to-many association between tenders and bidders. Documents can belong to a bidder or tender. Evaluations, government verifications, evidence, reviews, and audit rows retain tender/bidder/user references for historical traceability.

No row-level security policies were found in the inspected migrations. Do not add RLS or alter the existing schema until the identity provider and backend/service-role boundary are decided.

## M02 Database Foundation Implemented

- `ApplicationRole` defines canonical `BIDDER` and `OFFICER` values.
- `users.role` defaults to `OFFICER` and is constrained to canonical values plus the explicitly temporary legacy values `admin` and `procurement_officer`.
- `Bidder.user_id` has a unique constraint/index; the ORM exposes `User.bidder_profile` as a one-to-one relationship.
- `OfficerProfile` and `officer_profiles` provide a minimal one-to-one officer profile linked to `users.id` with `ON DELETE CASCADE`.
- Existing IDs and foreign-key targets are unchanged.
- The migration checks for duplicate bidder-user links and raises before creating the unique index; it never deletes or merges records.
- Human review confirmed three separate demo organizations and approved deterministic demo application identities.
- User `...031` owns bidder `...021` ABC, user `...032` owns bidder `...022` XYZ, and user `...033` owns bidder `...023` DEF.
- Legacy user `...001` remains `admin@gem.gov.in`, role `admin`, unchanged, with no bidder profile.
- The migration was applied transactionally after the duplicate group was resolved. Live verification found zero duplicate groups and all three bidder owners exactly once.

The affected bidder rows are:

- `00000000-0000-0000-0000-000000000021`: ABC Technologies Pvt Ltd; 1 tender and 2 documents.
- `00000000-0000-0000-0000-000000000022`: XYZ Infrastructure Ltd; 1 different tender and 2 documents, including 1 OCR-completed document.
- `00000000-0000-0000-0000-000000000023`: DEF Engineering Services Ltd; 1 different tender and no documents.

Because more than one row contains independent tender/document history, no canonical bidder was selected. Manual business reconciliation is required.

The user is `admin@gem.gov.in`, `CPCL / Ministry of Petroleum`, active, role `admin`. The three demo identities are application users only: no passwords, Supabase Auth accounts, or production identity claims were created.
- Cross-table role/profile consistency is intentionally not enforced with triggers in M02. A later profile/application service must reject a BIDDER with an officer profile and an OFFICER with a bidder profile.

## Current Domain Architecture

- Tender management: `Tender` model, `TenderService`, routes under `/api/v1/tenders`, frontend tender pages.
- Bidder management: `Bidder` model, `BidderService`, routes under `/api/v1/bidders`, frontend bidder pages.
- Tender and bidder documents: `Document` model and `DocumentService`; bidder/tender upload and listing routes.
- Storage: private Supabase Storage bucket configured through `storage_bucket`; signed access URLs are generated by `DocumentService`.
- OCR: `backend/app/ocr/`, `DocumentOCRWorker`, queued status transitions, persisted OCR text/status.
- AI extraction: `backend/app/ai/`, `DocumentAIWorker`, persisted structured extraction/status.
- Government verification: provider registry under `backend/app/integrations/`, orchestration in `GovernmentVerificationService`, persisted history in `government_verifications`.
- Evidence and explanation: `EvidenceResolver`, evidence trace models, `ExplanationEngine`, evidence endpoints.
- Compliance: `ComplianceEngine` and `ComplianceService`, approved requirement gate, historical `ComplianceEvaluation` and `RequirementEvaluation` snapshots.
- Requirement review: `TenderRequirement` lifecycle, AI suggestions, explicit approve/reject routes, audit events.
- Officer review/decision: `backend/app/review/`, `officer_reviews`, `requirement_reviews`, explicit decision state machine, audit events.
- Audit: append-only `AuditService` and `audit_logs`; current list/detail routes have no authorization.
- Dashboard/workflow: Task 17 aggregation in `backend/app/dashboard/`, frontend `TenderEvaluationDashboard`, `TenderWorkflowPage`, and current demo `DashboardPage`.
- Workers: in-process background tasks and queues in `backend/app/workers/`; API routes can trigger OCR, AI, extraction, and retry work without an auth boundary today.

## Current API Security State

All current domain routes are unauthenticated. High-risk broad routes include:

- bidder list/detail and bidder document list/upload;
- global document list, metadata, signed access, OCR, AI, and verification routes;
- compliance evaluation/history/detail/evidence routes;
- requirement creation, update, approval, rejection, and extraction routes;
- officer review and decision routes;
- audit list/detail routes;
- tender dashboard and bidder aggregation routes;
- worker-triggering upload/process/retry routes.

Some routes check that a resource exists or that a tender document belongs to a tender. These are relationship checks, not caller authorization. Request bodies can currently provide `officer_id`, `reviewer_id`, or similar actor IDs; future code must derive actor identity from an authenticated dependency.

## Proposed RBAC Architecture

Use exactly two new product roles: `BIDDER` and `OFFICER`. Treat `admin` and `procurement_officer` as legacy values requiring an explicit migration mapping.

Preferred future dependency chain:

```text
credential
  -> authenticated identity
  -> application user (`users`)
  -> role check (`BIDDER` or `OFFICER`)
  -> resource ownership/tender authorization
  -> existing service or protected workflow
```

Use `401` for missing/invalid identity, `403` for a valid identity without role/scope, and a documented `404` strategy when hiding resource existence is appropriate. Keep frontend guards as UX only.

## Proposed Ownership Rules

A bidder must reach resources through the authenticated user and own bidder profile:

```text
user -> bidder profile -> future bid -> document -> evidence/verification -> evaluation
```

Never authorize from a caller-supplied ID alone. Resolve and validate every tender, bidder, document, evidence, evaluation, and review relationship. Officer access requires both `OFFICER` role and authorization for the tender. The current schema has no officer assignment model; creator-only, explicit assignment, or organization scope must be selected before implementation.

## Proposed Frontend Routing

Keep public pages separate from authenticated layouts. Recommended future paths:

```text
/                         public landing
/login                    public login
/signup/bidder            public bidder signup
/signup/officer           public officer signup
/bidder/*                 bidder layout and own resources
/officer/*                officer layout and authorized tender workflows
```

The current `/dashboard`, `/tenders`, `/bidders`, `/documents`, `/verification`, `/audit`, and `/settings` routes are unprotected legacy/demo routes. Migrate them deliberately rather than assuming their current navigation implies authorization. Add credential handling to `frontend/src/api/client.js` only after the backend identity contract is approved.

## Protected Systems

Do not rewrite or duplicate:

- OCR pipeline and workers.
- AI extraction and providers.
- GovernmentProvider/integration framework and verification history.
- Evidence Resolver, evidence snapshots, and Explanation Engine.
- Compliance Rule Engine and ComplianceService.
- Officer Review and Officer Decision lifecycle.
- Append-only AuditService.
- Background workers and Supabase Storage.
- Task 17 dashboard aggregation.
- Task 19 tender document processing.
- Task 20 workflow integration.

RBAC should wrap these systems at the API/service boundary and preserve their existing contracts and historical data.

## Migration Strategy

1. Decide canonical identity provider and whether roles are single-valued or multi-valued.
2. Inventory all existing users, role values, duplicate bidder links, orphan references, and demo records.
3. Add identity mapping while preserving current UUIDs and historical foreign keys.
4. Map legacy roles explicitly to `BIDDER` or `OFFICER`, with exceptions documented before enforcement.
5. Add profile/cardinality constraints only after data validation.
6. Decide and model officer-to-tender authorization.
7. Add backend auth and ownership dependencies incrementally, starting with read and high-risk state-changing routes.
8. Derive audit actor IDs from trusted identity and preserve append-only history.
9. Add frontend role layouts/guards after API behavior is protected.
10. Validate all existing OCR, AI, verification, evidence, compliance, review, audit, dashboard, and workflow tests/data before enabling enforcement broadly.

## Known Problems and Unresolved Questions

- No canonical auth identity mapping exists.
- Legacy role values do not match the required two-role model.
- Bidder cardinality is not constrained.
- Bid submission is not modeled separately from tender-bidder association.
- Officer tender assignment is not modeled.
- RLS strategy is absent.
- Existing endpoints expose too much data and accept caller-provided actor IDs.
- Demo/contract routes coexist with live database routes.
- The team must decide which raw OCR, government payload, evidence, and compliance details are visible to bidders.

## Exact Files Changed in M02

Created:

- `backend/app/models/officer_profile.py`
- `backend/tests/test_user_role_foundation.py`
- `supabase/migrations/20260913_add_user_role_profiles.sql`
- `m2_reconciliation_snapshot.json`

Modified:

- `backend/app/models/user.py`
- `backend/app/models/bidder.py`
- `backend/app/models/__init__.py`
- `backend/tests/test_compliance_orchestration.py`
- `backend/tests/test_evidence_traceability.py`
- `backend/tests/test_tender_requirement_management.py`
- `docs/RBAC_ARCHITECTURE.md`
- `docs/MILESTONE_STATUS.md`
- `docs/HANDOFF.md`

Created during blocker investigation:

- `docs/M2_BLOCKER_ANALYSIS.md`

## Checks Performed

Checks run:

```text
git status --short
git diff --check
git diff --stat
git diff --name-only
python -m compileall -q app tests/test_user_role_foundation.py
python -m pytest -q tests/test_user_role_foundation.py
```

`git diff --check` passed. Python compilation passed. The focused M2 suite passed: `6 passed`. The full backend regression suite passed: `354 passed, 1 warning`. The live PostgreSQL reconciliation committed `3` user inserts and `3` bidder ownership updates with `0` deletes. The migration applied successfully in one transaction and all live M2 constraints passed verification. Pre-existing task-file and unrelated documentation changes were not reverted or modified.

The blocker investigation also verified the live bidder rows and dependency graph using read-only queries. No live `bids` table exists; there are six direct bidder foreign-key tables. No live verification, compliance, evidence, or direct audit-entity references exist for the three rows. The live officer-review tables are absent even though their repository models/migrations exist.

The root `.venv` was used for validation. `pytest 9.1.1` is available there. Four existing isolation tests were updated to create separate test users for separate bidder profiles; no tests were weakened or removed.

Observed results: `git diff --check` passed with no output. Because the three M01 files are untracked until a later review/staging step, `git diff --stat` and `git diff --name-only` listed only the pre-existing tracked `tasks/task*.md` deletions; `git status --short` showed the three docs alongside the pre-existing task changes. A direct file check confirmed all three docs exist and are non-empty.

## Next Milestone Instructions

Milestone 03 is **Role-Based Signup**. It may begin from the completed M2 database identity/profile foundation, with the explicit product decision that the three existing organizations remain separate. M2 does not implement authentication, signup, frontend RBAC, route guards, password handling, JWT handling, Supabase Auth, or authorization.
