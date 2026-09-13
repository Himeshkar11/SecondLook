# SecondLook Milestone 09 Handoff

## Exact Stopping Point

Milestones 01 through 09 are complete. The authenticated bidder workspace, proposal creation, private document upload, asynchronous OCR and structured AI extraction pipeline, statutory government verification integration, transparent processing tracking, formal bid submission workflows, and bidder compliance score visibility layer with failure explanations are implemented and verified.

The handoff state is:
- Bidder compliance visibility is implemented.
- Deterministic compliance scoring formula is implemented (`applicable = total - not_applicable`, `score = (passed / applicable) * 100.0`).
- Factual failure/partial/unverified explanations and actionable remediation guidance are implemented.
- Secure evidence traceability with signed document access is implemented.
- Evaluation run history audit trail is implemented.
- Prominent statutory disclaimers are enforced across UI and backend API responses.
- Backend RBAC and bidder ownership are authoritative (`HTTP 403` on mismatch).
- No duplicate compliance engine, evidence resolver, or evaluation models created.
- No officer review logic mutated; no automatic qualification, disqualification, ranking, or award.
- All changes are UNCOMMITTED in the working tree (`NOT COMMITTED`).

Next milestone: Milestone 10 — Officer Review & Disqualification Workflow.


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

Supabase Auth is the authentication provider. The frontend uses the official Supabase client for email/password login, persisted sessions, refresh, auth-state changes, and logout. The backend validates bearer credentials through Supabase Auth `/auth/v1/user` and resolves the Auth UUID through `users.auth_user_id`. `/api/v1/auth/me` returns the linked active application identity.

Role-based signup now uses Supabase Auth followed by authenticated `/api/v1/auth/provision`. M4 adds centralized `require_role`, bidder ownership, and document access dependencies. No frontend route guard exists. An authenticated Supabase identity that has no explicit application-user mapping receives a safe error from `/auth/me`; it is not auto-provisioned outside the signup provisioning flow.

The local `users` table and SQLAlchemy `User` model are application records with historical `id`, nullable `auth_user_id`, email, full name, free-form role, active flag, and timestamps. The role default is legacy `admin`; tests create `procurement_officer`. The frontend `/login` route uses Supabase Auth, and the header displays the authenticated email with logout. Theme preference is separate from Supabase session persistence.

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

`bidders` contains legal and registration data and points to `users` through a unique `user_id`. `officer_profiles` exists as a one-to-one foundation. `users.auth_user_id` is a nullable unique mapping to Supabase Auth. There is no `bids` table or Bid model; `tender_bidders` is a many-to-many association between tenders and bidders. Documents can belong to a bidder or tender. Evaluations, government verifications, evidence, reviews, and audit rows retain tender/bidder/user references for historical traceability.

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

All sensitive domain routes are protected by centralized authentication and role/ownership authorization. Key boundaries enforced in M4 include:

- bidder list/detail and bidder document list/upload;
- global document list, metadata, signed access, OCR, AI, and verification routes;
- compliance evaluation/history/detail/evidence routes;
- requirement creation, update, approval, rejection, and extraction routes;
- officer review and decision routes;
- audit list/detail routes;
- tender dashboard and bidder aggregation routes;
- worker-triggering upload/process/retry routes.

All sensitive endpoints enforce centralized `require_role`, `require_owned_bidder`, `require_document_access`, or `require_tender_bidder_access`. Actor identity is strictly derived from authenticated identity, never from request body `officer_id` or caller-supplied parameters. Only `/api/v1/health/database` remains intentionally public, and `/api/v1/auth/provision` requires a validated Supabase bearer token.

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

The frontend routes remain without route guards by design. Their backend API calls now enforce M4 authentication, role, and ownership boundaries. M5 may add frontend route protection as UX; it must not replace backend authorization.

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
- `backend/app/auth/__init__.py`
- `backend/app/auth/service.py`
- `backend/app/auth/dependencies.py`
- `backend/app/authz/__init__.py`
- `backend/app/authz/dependencies.py`
- `backend/app/schemas/auth.py`
- `backend/tests/test_authentication_foundation.py`
- `frontend/src/auth/supabaseClient.js`
- `frontend/src/auth/AuthContext.jsx`
- `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/SignupPage.jsx`
- `backend/app/services/signup_service.py`
- `backend/tests/test_signup_foundation.py`
- `backend/tests/test_authorization_boundaries.py`
- `backend/tests/conftest.py`
- `supabase/migrations/20260913_add_auth_identity_mapping.sql`
- `frontend/package.json`
- `frontend/package-lock.json`
- `.env.example`
- `docker-compose.yml`
- `backend/tests/test_compliance_orchestration.py`
- `backend/tests/test_evidence_traceability.py`
- `backend/tests/test_tender_requirement_management.py`
- `backend/app/api/router.py`
- `backend/app/dashboard/router.py`
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

## M3 Role-Based Signup

- `/signup` requires an explicit BIDDER/OFFICER selection.
- BIDDER creates the existing `Bidder` profile from the real model fields.
- OFFICER creates the existing `OfficerProfile`, which currently has no additional business fields.
- Backend role validation is authoritative and rejects legacy or arbitrary roles.
- Existing login remains unchanged and can authenticate Supabase accounts created by the signup flow when Supabase returns a session.
- If email confirmation is enabled, Supabase may return no session; profile provisioning waits for a confirmed authenticated session rather than creating an orphaned application User.

Focused M3 tests: `14 passed`. Full backend regression: `368 passed, 1 warning`. Frontend build passed.

## M4 Backend Authorization

The backend is authoritative for the selected M4 boundaries. Officer-only routes require canonical `OFFICER`; bidder profile/document routes resolve ownership through the authenticated application User; document-by-ID routes permit the owner or an officer. Invalid or legacy roles receive `403`, missing/invalid credentials receive `401`, and cross-owner resources receive `403` or `404` without leaking data.

M4 protects officer tender-bidder inspection and dashboard endpoints, bidder-owned bidder detail and bidder-document endpoints, owner/officer document metadata, signed access, OCR, AI, retry, verification, tender-document, compliance, evidence, requirement-management, audit, and review endpoints.

M4 focused security tests: `22 passed`. Full backend regression: `390 passed, 1 warning`. No migration was required and no frontend source was changed.

All sensitive legacy surfaces are now protected. Health and authentication operations are the only intentionally public/authentication-scoped exceptions.

## M5 Frontend Role-Based Routing

The frontend understands the canonical `BIDDER` and `OFFICER` roles resolved from `/api/v1/auth/me`. Centralized `ProtectedRoute` guards protect namespaced routes:
- `/bidder/*`: restricted to canonical `BIDDER` role; officers redirected to `/officer`.
- `/officer/*` and legacy preserved routes: restricted to canonical `OFFICER` role; bidders redirected to `/bidder`.
- Unauthenticated users attempting to reach protected routes are redirected to `/login`.
- Unresolved or invalid roles trigger a safe role-unavailable notice (never default to any role).
- Navigation in Sidebar and Header dynamically reflects role context without cross-role link exposure.
- Initial auth loading displays a stable loading indicator to eliminate redirect flicker.

Frontend build: `npm run build` passed.
Full backend regression: `390 passed, 1 warning`.

FRONTEND ROUTE PROTECTION IS IMPLEMENTED FOR UX/NAVIGATION.

BACKEND RBAC REMAINS THE AUTHORITATIVE SECURITY BOUNDARY.

## M6 SecondLook Landing Page + 3D Experience

The public product experience on `/` is implemented:
- `LandingPage.jsx`: Public product narrative explaining the 5-step deterministic evaluation process (Upload → Extract → Verify → Evaluate → Review), evidence chain architecture, and AI+human control principle.
- `Hero3D.jsx`: Interactive Three.js "Evidence & Compliance Inspection Constellation" featuring a rotating faceted gateway core, orbital document cards, and statutory verification nodes. Code-split via `React.lazy` with automatic `IntersectionObserver` pause and SVG/CSS fallback.
- `PublicNavbar.jsx`: Dedicated public navigation with brand tricolor accent, semantic anchor links, light/dark theme toggle, and direct role signup CTAs.
- Direct Role CTAs: `Sign up as Bidder` (`/signup?role=bidder`) and `Sign up as Officer` (`/signup?role=officer`) connecting to the existing signup flow with preselected account type cards.
- Layout: `MainLayout.jsx` automatically renders a full-width experience without internal enterprise sidebar for unauthenticated visitors on `/`.
- Dynamic Root: Authenticated users visiting `/` continue redirecting to their canonical role workspace (`/bidder` or `/officer`) via `RootRoute`.

Authentication and Security Boundary:
- Authentication/RBAC architecture was not redesigned.
- Backend RBAC enforcement was not changed.
- `AuthContext` and `ProtectedRoute` were not changed.
- `SignupPage.jsx` was modified only to support landing-page role preselection via `?role=bidder` / `?role=officer`.
- The signup query parameter remains UI-only.
- Backend `/api/v1/auth/provision` remains authoritative for role validation.

Frontend build: `npm run build` passed.
Full backend regression: `390 passed, 1 warning`.

LANDING PAGE IMPLEMENTED.

AUTHENTICATION/RBAC NOT REDESIGNED.

BACKEND RBAC REMAINS THE AUTHORITATIVE SECURITY BOUNDARY.

## M7 Bidder Profile + Bidder Workspace Foundation

The authenticated bidder experience is implemented:
- `GET /api/v1/bidders/me`: Secure backend profile and metric endpoint enforcing canonical `BIDDER` role and resolving identity strictly from the authenticated application user (`current_user.id == Bidder.user_id`).
- Profile & Ownership Security: Cross-bidder access denied via `require_owned_bidder_by_id` (403 Forbidden). Officer access to bidder profile endpoints denied (403 Forbidden). Bidder access to officer endpoints denied (403 Forbidden).
- Read-Only Statutory Profile: Legal Name, GSTIN, PAN, and CIN are established upon registration and verified against government authorities. Self-service mutation is restricted to preserve compliance audit integrity.
- Bidder Workspace (`/bidder`): Welcome company greeting, account summary with masked statutory identifiers (`29******Z5`, `AA*****1A`), real metric counts (`active_tenders_count`, `documents_count`, `submitted_bids_count = 0`), and module navigation.
- Bidder Profile Page (`/bidder/profile`): Displays verified corporate attributes with reveal/mask toggle and statutory integrity notice.
- Bidder Tender Discovery (`/bidder/tenders`): Read-only discovery of published procurement tenders using existing `GET /api/v1/tenders` and `GET /api/v1/tenders/{id}`, with detailed inspection modal and M8 bid submission notices.
- Honest Placeholder States:
  - My Bids (`/bidder/bids`): Clear milestone notice that bid submission opens in Milestone 08.
## M8 Bid Submission + Bidder Document Workflow
- Asynchronous document pipeline tracking (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`) with on-demand manual retry.
- Government statutory registry verification triggered on document extraction.
- Formal bid submission enforcing at least one document and rendering submitted bids immutable.
- Focused M8 tests: `10 passed`.

## M9 Bidder Compliance Score + Failure Explanation
- Read-only bidder compliance visibility layer exposed at `GET /api/v1/bidder/bids/{bid_id}/compliance` and `GET /api/v1/bidder/bids/{bid_id}/compliance/history`.
- Strictly informational legal disclaimer banner on UI and embedded in all backend compliance API payloads.
- Clear honest empty state (`status="NOT_EVALUATED"`, `score=None`, `score_formatted="—"`) when evaluation has not run yet.
- Deterministic compliance score: `applicable = total_requirements - not_applicable_count`. When `applicable > 0`: `score = round((pass_count / applicable) * 100.0, 1)`. When `applicable == 0`: `score = None` (`"—"`). `FAIL`, `PARTIAL`, and `NOT_VERIFIED` are never counted as passed.
- Requirement breakdowns with code, title, mandatory badge, outcome badge, factual rationale from `ExplanationEngine`, actionable remediation guidance, and evidence links.
- Evaluation run history table tracking immutable audit trail of past runs.
- Cross-bidder access denied with HTTP 403; officer access to bidder compliance endpoints denied with HTTP 403; unauthenticated access denied with HTTP 401.
- Focused M9 tests: `11 passed`.
- Full backend regression: `422 passed, 1 warning`.
- Frontend build: `npm run build` passed cleanly.

BIDDER COMPLIANCE SCORE AND FAILURE EXPLANATION IS IMPLEMENTED.

OFFICER REVIEW AND DISQUALIFICATION WORKFLOW IS NOT IMPLEMENTED.

NOT COMMITTED (WORKING TREE CHANGES ONLY).

MILESTONE 10 NOT STARTED.

## Next Milestone Instructions

Milestone 10 is **Officer Review & Disqualification Workflow**.

AUTHENTICATION IS IMPLEMENTED.

ROLE-BASED SIGNUP IS IMPLEMENTED.

BACKEND RBAC IS IMPLEMENTED.

FRONTEND ROLE-BASED ROUTING IS IMPLEMENTED.

LANDING PAGE + 3D EXPERIENCE IS IMPLEMENTED.

BIDDER WORKSPACE FOUNDATION IS IMPLEMENTED.

BID SUBMISSION + DOCUMENT PIPELINE IS IMPLEMENTED.

BIDDER COMPLIANCE SCORE + EXPLANATIONS ARE IMPLEMENTED.

Do NOT start Milestone 10 before review.
Do NOT commit working tree changes.
Do NOT modify officer review logic during M9 handoff.
Do NOT auto-disqualify or rank bidders.
