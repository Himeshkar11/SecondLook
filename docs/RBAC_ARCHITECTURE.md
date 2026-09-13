# SecondLook RBAC Architecture Audit

## Scope and Evidence

This document records the Milestone 01 audit of the existing repository. It is a design and handoff document only. No authentication, authorization, schema, migration, dashboard, landing page, or protected-system implementation was added during this milestone.

The audit used the current backend models, routers, services, workers, frontend route tree, frontend services, Supabase migrations, tests, README files, and configuration.

## Current Architecture Audit

### Repository structure

- Backend entry point: `backend/app/main.py`.
- FastAPI API router: `backend/app/api/router.py`, mounted at `/api/v1`.
- Dashboard router: `backend/app/dashboard/router.py`.
- Officer review router: `backend/app/review/router.py`.
- Database session dependency: `backend/app/api/deps.py` delegates to `backend/app/database/repository.py`.
- SQLAlchemy models: `backend/app/models/`.
- Services: `backend/app/services/`.
- Repositories: `backend/app/database/`, `backend/app/dashboard/repository.py`, and `backend/app/review/repository.py`.
- Workers and in-process queues: `backend/app/workers/`.
- OCR abstractions: `backend/app/ocr/`.
- AI extraction abstractions and providers: `backend/app/ai/`.
- Government integrations: `backend/app/integrations/`.
- Verification, evidence, rules, scoring, risk, and explanation code: `backend/app/verification/`.
- Frontend entry point: `frontend/src/main.jsx`.
- Frontend route tree: `frontend/src/App.jsx` using React Router `BrowserRouter`.
- Frontend HTTP client: `frontend/src/api/client.js`.
- Database platform: Supabase PostgreSQL through SQLAlchemy; Supabase Storage is used by the document service.
- No Alembic directory or `pyproject.toml` was found. SQL migrations live under `supabase/migrations/`.

The intended layering is Router -> Service -> Repository/Database/Integration. The implementation is partly real database-backed and partly retained contract/demo behavior, so the future authorization layer must account for both paths.

## Authentication Findings

| Question | Finding | Evidence |
|---|---|---|
| Login | M3A provides a minimal Supabase Auth email/password flow at `/login`. | `frontend/src/App.jsx`, `frontend/src/pages/LoginPage.jsx` |
| Signup | Not present. | No signup page, service, or route found. |
| Supabase Auth | Used for password verification and session lifecycle; no service-role key is exposed to the browser. | `frontend/src/auth/supabaseClient.js`, `backend/app/auth/service.py` |
| FastAPI authentication | M3A validates bearer credentials through Supabase Auth and M4 resolves roles and ownership through centralized dependencies. | `backend/app/auth/dependencies.py`, `backend/app/authz/dependencies.py`, `backend/app/api/router.py` |
| JWT | No JWT library, token parser, or bearer dependency found. | `backend/requirements.txt`, backend auth search |
| Session authentication | No application session or cookie authentication found. | Backend and frontend auth search |
| Frontend current user | Supabase Auth state is exposed through `AuthProvider`; the header displays the authenticated email and logout control. | `frontend/src/auth/AuthContext.jsx`, `frontend/src/components/layout/Header.jsx` |
| Identity storage | Supabase client manages persisted session state; application identity mapping is stored in nullable `users.auth_user_id`. | `frontend/src/auth/supabaseClient.js`, `supabase/migrations/20260913_add_auth_identity_mapping.sql` |
| Protected backend APIs | M4 protects all sensitive bidder, tender, document, compliance, evidence, verification, requirement, review, audit, and dashboard boundaries. | `backend/app/api/router.py`, `backend/app/dashboard/router.py`, `backend/app/review/router.py` |
| Application user table | Yes, local `users` table and SQLAlchemy `User` model exist. | `backend/app/models/user.py`, `supabase/migrations/20260911_create_core_domain_schema.sql` |
| Role field | Yes, `users.role`, defaulting to legacy `admin`. Tests use `procurement_officer`. No controlled enum/check constraint exists. | `User.role`, migration, backend tests |
| Auth migrations | M3A adds nullable unique `users.auth_user_id`; historical application user UUIDs remain unchanged. | `supabase/migrations/20260913_add_auth_identity_mapping.sql` |
| Auth frontend components/tests | No real auth components or auth tests. Existing tests verify unauthenticated demo/API behavior. | `frontend/src`, `backend/tests` |

**Conclusion:** Authentication and identity resolution are implemented in M3A/M3. Backend authorization and ownership enforcement are implemented in M4. Frontend role-based routing remains unimplemented and will be added in Milestone 05.

## Current Database Architecture

### Existing identity and profiles

```text
users
  |-- bidders.user_id -> users.id
  |-- tenders.created_by -> users.id
  |-- tender_requirements.created_by -> users.id
  |-- tender_requirements.approved_by -> users.id
  |-- officer_reviews.reviewer_id -> users.id
  |-- requirement_reviews.reviewed_by -> users.id
  `-- audit_logs.user_id -> users.id
```

`User` currently has `id`, unique `email`, required `full_name`, free-form `role`, `is_active`, and timestamps. It has relationships to tenders, a bidder profile, and audit logs. There is no `officer_profiles` table and no separate `bid_profiles` or `bids` table.

`Bidder` currently has its own profile-like record with `id`, required `user_id`, legal and registration fields, status, and timestamps. The `user_id` column is not unique, so the database currently permits multiple bidder rows per user. This is a migration decision, not an assumption that it is safe to change immediately.

There is no `Bid` ORM model or `bids` migration/table. Bidder participation is currently represented by the `tender_bidders` many-to-many table. A future bid submission workflow will need a deliberate model rather than treating `tender_bidders` as a bid.

### Existing domain tables

- `users`: application identity-like records with an uncontrolled role string.
- `tenders`: tender records with `created_by`; many-to-many bidder association through `tender_bidders`.
- `bidders`: bidder business profile linked to `users` by `user_id`.
- `documents`: bidder or tender documents; `bidder_id` became nullable when `tender_id` was added.
- `verification_jobs` and `verification_results`: legacy verification lifecycle.
- `government_verifications`: immutable-style government verification history linked to bidder/document.
- `tender_requirements`: requirement lifecycle, AI source traceability, creator/approver references.
- `requirement_evaluations` and `compliance_evaluations`: factual evaluation history linked to tender and bidder.
- `officer_reviews` and `requirement_reviews`: review lifecycle and decision records linked to users.
- `audit_logs`: append-only service API with nullable `user_id`.
- `demo_government_records`: demo provider source data.

### Safe future identity/profile model

The minimum-change design is to preserve existing `users.id` as the application-facing foreign-key target while introducing a verified identity mapping only after the identity provider decision is made:

```text
Canonical Auth Identity (provider subject)
              |
              v
Application User (`users.id`, one row per identity)
       |                      |
       v                      v
Bidder profile            Officer profile
(existing `bidders`)      (future `officer_profiles`, only if officer-specific data is needed)
```

Recommended constraints for future design, subject to data migration validation:

- Keep `users.id` as the primary key referenced by historical records.
- Add an immutable identity-provider subject mapping or make `users.id` equal to the provider UUID; do not silently replace existing IDs.
- Normalize roles to exactly `BIDDER` and `OFFICER` for new authorization code. Preserve a staged mapping for existing `admin` and `procurement_officer` values before enforcing a constraint.
- Decide whether one user may have multiple roles. The product requirement says two account types, but the current schema has one role string; do not introduce a multi-role table without a product decision.
- Add a unique bidder-to-user relationship only after checking for duplicates. Existing data and tests do not prove one-to-one cardinality.
- Create `officer_profiles` only if officer-specific attributes cannot remain on `users`; it should use `user_id` as a unique foreign key to `users.id`.
- Do not delete users or profiles when historical tenders, evaluations, reviews, or audits depend on them. Prefer deactivation and `ON DELETE RESTRICT`/`SET NULL` according to each historical relationship.
- Preserve existing bidder, tender, document, evaluation, evidence, review, and audit IDs.
- No row-level security policies were found in the inspected migrations. Future RLS must complement backend authorization, not replace it, and must not be enabled without a tested service-role/migration strategy.

### Migration strategy

1. Inventory and classify all existing `users.role` values and duplicate `bidders.user_id` values.
2. Decide canonical authentication identity: Supabase Auth subject mapped to `users`, or a backend-owned identity system.
3. Add the identity mapping/application-user fields without changing historical primary keys.
4. Backfill and verify user mappings, including existing bidder and officer/procurement records.
5. Introduce controlled role values with an explicit compatibility mapping for `admin` and `procurement_officer`.
6. Add profile constraints only after duplicate and orphan checks pass.
7. Add backend authentication in observe-only or narrowly scoped routes first.
8. Add bidder ownership checks and officer tender authorization checks.
9. Add frontend guards as UX only, then progressively protect APIs.
10. Validate historical document, verification, evaluation, review, evidence, and audit access before enforcing the full role boundary.

## M02 Implemented Foundation

Milestone 02 adds the following database foundation without implementing authentication:

- `ApplicationRole` exposes only canonical `BIDDER` and `OFFICER` values.
- `users.role` defaults to `OFFICER` and has a database check constraint.
- `admin` and `procurement_officer` remain explicitly allowed as temporary legacy compatibility values; no automatic production classification was performed.
- `bidders.user_id` is unique, preserving existing bidder IDs and preventing a second bidder profile for one user.
- `officer_profiles` is a minimal one-to-one table with a cascading foreign key to `users`.
- The migration aborts if duplicate bidder profiles are found rather than deleting or merging records.
- The confirmed demo organizations were kept as three separate records: ABC `...021`, XYZ `...022`, and DEF `...023`.
- Deterministic demo application users `...031`, `...032`, and `...033` were created with canonical role `BIDDER`; no passwords or Supabase Auth identities were created.
- The legacy `admin@gem.gov.in` user `...001` remains unchanged and owns no bidder profile.
- The M2 migration was applied transactionally after reconciliation. Live verification confirms the unique bidder index, officer profile table and uniqueness, role check, zero duplicate ownership groups, and preserved history.

The local uncommitted rollback snapshot is `m2_reconciliation_snapshot.json`. The reconciliation performed zero deletes and changed only three bidder ownership foreign keys plus the three newly inserted demo users. No bidder, tender, document, OCR/AI, verification, compliance, evidence, or audit row was deleted or moved.

Cross-table role/profile consistency is not enforced by a database trigger in M02. Profile creation and role checks must be validated by the application/profile service in a later milestone; M02 deliberately does not implement RBAC or authentication.

## M3A — Authentication Foundation

M3A establishes authentication only. Supabase Auth is the provider for password verification and session/token lifecycle. The application database remains the identity/profile layer and does not store passwords or password hashes.

The additive `users.auth_user_id` column maps a Supabase Auth UUID to the existing application `users.id` without replacing historical primary keys. `uq_users_auth_user_id` is unique for non-null mappings. Existing M2 users and the three confirmed demo organizations remain unchanged.

The frontend Supabase client uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`, persists sessions through the official client, restores the initial session, subscribes to auth state changes, and provides logout. `/login` is now a minimal email/password login page; successful login navigates to the existing `/dashboard` page. No signup flow, role selection, route guard, or role-based navigation exists yet.

The backend validates the bearer credential through Supabase Auth's `/auth/v1/user` endpoint, resolves the returned Auth UUID through `users.auth_user_id`, and exposes `/api/v1/auth/me` for identity retrieval. An Auth identity must already be explicitly mapped to an active application user; the endpoint does not provision users or authorize roles. `role` in the response is informational only.

AUTHENTICATION IS IMPLEMENTED.

RBAC AUTHORIZATION IS NOT IMPLEMENTED.

M3 implements role-based signup and role/profile creation. M4 implements backend role enforcement and protected endpoints.

## M3 — Role-Based Signup

M3 reuses the M3A Supabase Auth foundation. The frontend requires an explicit account type and calls Supabase Auth signup first. When Supabase returns an authenticated session, the frontend sends the role/profile payload with the bearer token to `/api/v1/auth/provision`.

The backend accepts only the canonical `BIDDER` and `OFFICER` roles using strict request validation. It obtains the Auth UUID and email from the validated Supabase token, never from request JSON. It rejects duplicate Auth mappings and duplicate application emails, then creates the application User and exactly one matching profile inside one database transaction.

For `BIDDER`, the existing `Bidder` model is reused with required `legal_name` and optional `registration_number`, `gst_number`, and `pan_number`. For `OFFICER`, the existing `OfficerProfile` is reused; its current schema contains only `user_id` and timestamps, so no invented department or designation fields were added. The opposite profile is not created.

The signup form has no default role. Switching to OFFICER clears bidder-only fields. Signup failure after Auth creation signs the client out; because Supabase Auth and PostgreSQL cannot share one transaction through the public client, an Auth account may require provider-side cleanup if provisioning fails. The application database transaction itself rolls back completely.

Authentication is implemented. Role-based signup is implemented. M4 implements backend role enforcement and protected ownership boundaries; frontend selection and the informational role returned by `/api/v1/auth/me` are not security boundaries.

## M4 — Backend Role Enforcement

M4 keeps `get_authenticated_identity` as the only authentication-to-application-User resolution path. Centralized `require_role(ApplicationRole.BIDDER)` and `require_role(ApplicationRole.OFFICER)` dependencies compare only the trusted application `User.role`; they do not inspect request bodies, query parameters, URLs, custom headers, or frontend state. Legacy `admin` and `procurement_officer` values are not promoted to canonical roles.

The bidder ownership dependency resolves the requested bidder through `Bidder.user_id == authenticated_user.id`. The document access dependency resolves the document's bidder relationship and permits the owning BIDDER or an OFFICER. A bidder changing `user_id`, `bidder_id`, `document_id`, `role`, `X-Role`, or query parameters cannot change the authenticated identity or cross the ownership boundary.

M4 protects the following existing API boundaries:

- Officer-only tender-bidder inspection and dashboard endpoints.
- Bidder-owned bidder detail and bidder document upload/list endpoints.
- Owning-bidder or officer document metadata, signed access, OCR, AI, retry, and government-verification endpoints.

All sensitive legacy list, contract, compliance, review, verification, requirement, evidence, and audit surfaces now require authentication and appropriate role/ownership dependencies. Health and authentication operations are the only intentionally public/authentication-scoped exceptions.

BACKEND RBAC IS IMPLEMENTED.

FRONTEND ROLE-BASED ROUTING IS IMPLEMENTED.

## Role Model

The target first-version application roles are exactly:

- `BIDDER`
- `OFFICER`

The legacy values `admin` and `procurement_officer` are existing data values, not approved new product roles. They require an explicit migration mapping and should not be interpreted implicitly by future route code.

### BIDDER permissions

Eventually, a bidder may browse available tenders, view requirements, create and manage own bid submissions, upload and process own documents, view own compliance scores/failures/evidence explanations, and manage the bidder profile.

A bidder must not approve or reject requirements, review other bidders, use officer routes, make officer decisions, modify evaluations or government results, or access another bidder's private resources.

### OFFICER permissions

Eventually, an officer may manage authorized tenders, process tender documents, review and approve/reject requirements, inspect assigned tender bidder submissions, inspect compliance/evidence, perform officer review, make explicit decisions, and access permitted audit information.

An officer must not impersonate bidders, alter historical evaluations, bypass audit recording, or turn AI suggestions into decisions without an explicit review action.

## Data Ownership Model

The future authorization chain should be evaluated server-side for every request:

```text
Authenticated identity
  -> application user
  -> bidder profile
  -> bid submission (future table)
  -> bidder/tender document
  -> evidence and verification
  -> compliance evaluation
```

A bidder request must resolve the bidder profile from the authenticated user, then verify every requested document, bid, evidence item, and evaluation against that profile and the relevant tender. A caller-supplied `bidder_id`, `document_id`, `evaluation_id`, or `user_id` is never sufficient proof of ownership.

For officer access, the current schema only proves tender creation through `tenders.created_by`; it does not provide an officer assignment table. The future design must choose one of:

- creator-based authorization for an initial narrow release;
- an explicit officer-to-tender assignment table; or
- an organization/department authorization model.

Until that decision exists, officer access should be treated as `OFFICER` plus explicit tender authorization, not as global access to every tender.

Cross-resource checks must include:

- document -> bidder/tender relationship;
- verification -> document/bidder relationship;
- requirement -> tender relationship;
- evaluation -> tender and bidder relationship;
- review -> evaluation and authorized tender relationship;
- audit query -> allowed scope, not arbitrary `user_id` or `entity_id` filters.

## Backend Authorization Design

Do not implement this in Milestone 01. The intended FastAPI shape is:

```text
get_authenticated_identity()
  -> get_application_user()
  -> require_role(BIDDER | OFFICER)
  -> require_owned_or_authorized_resource(...)
  -> route/service operation
```

Recommended semantics:

- `401 Unauthorized`: no credential, invalid credential, expired credential, or identity cannot be established.
- `403 Forbidden`: authenticated identity has the wrong role or lacks tender/resource authorization.
- `404 Not Found`: use where hiding resource existence is required, especially for cross-bidder access; document the policy consistently.
- `422`: malformed request data after authentication/authorization dependencies have run.

Protect direct routes and background-triggering routes, including document upload, OCR/AI retry, tender document processing, verification, requirement approval/rejection, compliance evaluation triggers, officer review, decisions, and audit access. Background workers must receive a trusted job context and must not infer authorization from untrusted request payloads.

Every state-changing operation must audit the authenticated actor. Existing service APIs accept optional caller-provided IDs such as `officer_id`, `reviewer_id`, and `user_id`; future authorization must derive these from the authenticated identity rather than trusting request bodies.

The frontend guard is only a navigation and user-experience feature. The backend dependency and resource checks remain the security boundary.

## API Inventory and Future Role Intent

Current protection status for the routes below reflects M4 backend enforcement. Frontend route protection remains future work.

| Method and route | Current implementation | Future role | Ownership/authorization requirement | Risk |
|---|---|---|---|---|
| GET `/api/v1/tenders` | `TenderService.list_tenders` | Shared/BIDDER/OFFICER | Public availability rules for bidders; officer scope for managed tenders | M4 protected (authenticated user required) |
| GET `/api/v1/tenders/{id}` | `TenderService.get_tender` | Authenticated users | Authentication dependency; no frontend route guard | M4 protected |
| GET `/api/v1/tenders/{id}/bidders` | Tender service relationship lookup | OFFICER | Authorized tender only | M4 protected (OFFICER only) |
| POST `/api/v1/tenders/{tender_id}/documents` | Document upload plus OCR/AI background task | OFFICER | Authenticated officer; tender relationship retained by service | M4 protected |
| POST `/api/v1/tenders/{tender_id}/documents/{document_id}/process` | Existing OCR/AI worker trigger | OFFICER | Authenticated officer; tender/document relationship retained | M4 protected |
| GET `/api/v1/tenders/{tender_id}/documents/{document_id}/processing` | Processing status | OFFICER | Authenticated officer; tender/document relationship retained | M4 protected |
| GET `/api/v1/tenders/{tender_id}/documents` | Tender document listing | OFFICER | Authenticated officer | M4 protected |
| GET `/api/v1/bidders` | `BidderService.list_bidders` | OFFICER | Officer scope; no bidder-wide listing for BIDDER | M4 protected (OFFICER only) |
| GET `/api/v1/bidders/{id}` | `BidderService.get_bidder` | BIDDER own / OFFICER | User-to-bidder ownership or officer tender scope | M4 protected (owning BIDDER only) |
| POST `/api/v1/bidders/{bidder_id}/documents` | Upload plus OCR/AI background task | BIDDER own / OFFICER support | Authenticated owner or authorized officer; bidder relationship | M4 protected (owning BIDDER only) |
| GET `/api/v1/bidders/{bidder_id}/documents` | Bidder document listing | BIDDER own / OFFICER | Ownership/scope check | M4 protected (owning BIDDER only) |
| GET `/api/v1/documents` | Global/filterable document listing | OFFICER | Authenticated officer; filters remain service inputs | M4 protected |
| GET `/api/v1/documents/{id}` | Metadata lookup | BIDDER own / OFFICER | Central document ownership dependency | M4 protected |
| GET `/api/v1/documents/{id}/access` | Signed Storage URL plus audit event | BIDDER own / OFFICER | Ownership/scope before signed URL | M4 protected (owner or OFFICER) |
| GET/POST `/api/v1/documents/{id}/ocr`, `/ocr/retry` | OCR status/retry | BIDDER own / OFFICER | Central document ownership dependency | M4 protected |
| GET/POST `/api/v1/documents/{id}/ai`, `/ai/retry` | AI status/retry | BIDDER own / OFFICER | Central document ownership dependency | M4 protected |
| POST/GET `/api/v1/documents/{id}/verify`, `/verification` | Government verification | BIDDER own / OFFICER | Central document ownership dependency | M4 protected |
| POST/GET `/api/v1/verification/start`, `/verification/{id}` | Legacy contract verification | OFFICER | Authenticated officer; legacy IDs no longer public | M4 protected |
| GET `/api/v1/tenders/{tender_id}/requirements` | Requirement listing | OFFICER | Authenticated officer | M4 protected |
| POST `/api/v1/tenders/{tender_id}/requirements` | Requirement creation | OFFICER | Authenticated officer | M4 protected |
| POST `/api/v1/tenders/{tender_id}/requirements/extract` | AI requirement extraction | OFFICER | Authenticated officer | M4 protected |
| GET/PATCH `/api/v1/tender-requirements/{id}` | Requirement lookup/update | OFFICER | Authenticated officer | M4 protected |
| POST `/api/v1/tender-requirements/{id}/approve` | Explicit approval and audit | OFFICER | Authenticated officer identity replaces body officer ID | M4 protected |
| POST `/api/v1/tender-requirements/{id}/reject` | Requirement rejection | OFFICER | Authenticated officer | M4 protected |
| GET/POST `/api/v1/bidders/{id}/compliance` and `/evaluate` | Compliance read/evaluation | BIDDER own read; OFFICER execute | Tender-bidder ownership dependency | M4 protected |
| POST/GET `/api/v1/tenders/{tender_id}/bidders/{bidder_id}/compliance/evaluate` and history | Evaluation orchestration/history | OFFICER execute; BIDDER own history read | Tender-bidder association and role | M4 protected (OFFICER execute / owning BIDDER history) |
| GET `/api/v1/compliance/evaluations/{id}` | Full evaluation and evidence | BIDDER own / OFFICER | Central evaluation ownership dependency | M4 protected |
| GET `/api/v1/compliance/evaluations/{id}/evidence` and `/audit` | Trace/audit for evaluation | BIDDER own evidence; OFFICER audit | Evaluation ownership or officer role | M4 protected |
| GET `/api/v1/requirements/{id}/evidence`, `/tender-requirements/{id}/evidence`, `/evidence/{id}` | Evidence trace/item access | OFFICER | Authenticated officer | M4 protected |
| GET `/api/v1/audit/events` and `/audit/{id}` | Audit listing/placeholder | OFFICER only | Central officer dependency | M4 protected |
| GET `/api/v1/tenders/{id}/dashboard` and `/dashboard/requirements` | Task 17 aggregation | OFFICER | Authorized tender | M4 protected (OFFICER only) |
| GET `/api/v1/dashboard/summary` | Legacy placeholder | OFFICER | Central officer dependency | M4 protected |
| GET `/api/v1/health`, `/health/database` | Health | Public/operations policy | No business data | Database health may reveal availability |

## Frontend Route Inventory

Milestone 05 introduces centralized `ProtectedRoute` guards with canonical `BIDDER` and `OFFICER` namespaces, role-aware navigation, and safe fallback handling. Frontend route protection exists for UX/navigation; backend RBAC remains the authoritative security boundary.

| Route | M5 Protection / Guard | Allowed Roles | Behavior |
|---|---|---|---|
| `/` | Public Root Resolver | Public | Redirects to role workspace (`/bidder` or `/officer`) or `/login` |
| `/login` | Public | Public | Authenticates via Supabase Auth; navigates to role workspace |
| `/signup` | Public | Public | Registers account + role profile; navigates to role workspace |
| `/bidder/*` | `ProtectedRoute` | `BIDDER` only | Minimal shell for M5; wrong-role redirected to `/officer` |
| `/officer/*` | `ProtectedRoute` | `OFFICER` only | Reuses Task 17/16 components; wrong-role redirected to `/bidder` |
| `/dashboard`, `/tenders`, `/bidders`, `/documents`, `/verification`, `/audit` | `ProtectedRoute` | `OFFICER` only | Preserved legacy paths protected against unauthorized / bidder access |
| `/settings` | `ProtectedRoute` | Authenticated (`BIDDER`, `OFFICER`) | Shared account settings |

The future route shape should preserve current deep links where practical while adding `/bidder/*` and `/officer/*` layouts. Recommended structure:

```text
/
/login
/signup/bidder
/signup/officer

/bidder
/bidder/tenders
/bidder/bids
/bidder/bids/:id
/bidder/documents
/bidder/compliance
/bidder/profile

/officer
/officer/dashboard
/officer/tenders
/officer/tenders/:id
/officer/bidders
/officer/bidders/:id
/officer/requirements
/officer/evaluations
/officer/reviews
/officer/audit
```

`frontend/src/api/client.js` currently sends no authorization header. Future auth state should be centralized and should not rely on arbitrary local storage values as proof of identity.

## Future Dashboard and Landing Design

### Bidder dashboard

Create a bidder-specific layout that consumes existing read-oriented compliance, evidence, document, and tender APIs. It should show available tenders, own bids, document processing state, compliance score/status, failures, explanations, and profile information. It must not calculate a second compliance result in the browser or expose other bidders.

### Officer dashboard

Refactor the existing Task 17 tender aggregation into an officer-scoped experience. It should show active authorized tenders, bidder counts, evaluation states, requirement issues, pending reviews, evidence links, decisions, and audit access. The existing dashboard service and `TenderEvaluationDashboard` are the reuse points; do not create a second evaluation engine.

### Landing page

A future public landing page should contain the product explanation, evidence/verification story, explainable compliance, human review, bidder/officer role selection, and a lightweight 3D procurement/evidence visual. Isolate the 3D work under `frontend/src/components/landing/`. Do not install a 3D library or modify the current UI in Milestone 01.

## Protected Systems

The following systems are protected and must be wrapped by the future product/RBAC layer rather than rewritten or duplicated:

- OCR interfaces and workers: `backend/app/ocr/`, `backend/app/workers/`.
- AI extraction interfaces/providers: `backend/app/ai/`.
- Government provider framework and providers: `backend/app/integrations/`.
- Government verification service and history: `GovernmentVerificationService`, `government_verifications`.
- Evidence Resolver and evidence trace models: `backend/app/verification/evidence_resolver.py`, `evidence_models.py`.
- Compliance Rule Engine and ComplianceService.
- Immutable compliance evaluation/evidence snapshots.
- Explanation Engine.
- Officer Review and Officer Decision lifecycle.
- Append-only AuditService and `audit_logs`.
- Background workers and job queues.
- Supabase Storage and signed URL behavior.
- Task 17 dashboard aggregation.
- Task 19 tender document processing.
- Task 20 workflow integration.

## Architecture Decisions for Future Milestones

1. No auth exists today; do not pretend the current `users` table authenticates anyone.
2. Preserve current UUIDs and foreign-key history.
3. Normalize new product roles to exactly `BIDDER` and `OFFICER`; map legacy values explicitly.
4. Treat backend authorization as the security boundary.
5. Derive actor IDs from authenticated identity, never from request body fields.
6. Add ownership checks before exposing documents, evidence, evaluations, or review records.
7. Introduce a real bid-submission model before implementing bid uploads; `tender_bidders` is not a bid.
8. Reuse compliance, evidence, review, audit, and dashboard services.
9. Keep public landing/auth pages separate from authenticated layouts.
10. Resolve the identity provider and officer tender-assignment model before creating migrations.

## File Change Plan

| File/Directory | Current purpose | Future change | Milestone | Risk | Protected? |
|---|---|---|---|---|---|
| `backend/app/models/user.py` | User-like application record | MODIFY: identity mapping and controlled role strategy after decision | M02 | High: historical FKs and legacy roles | Yes |
| `backend/app/models/bidder.py` | Bidder profile | MODIFY: ownership/cardinality constraints after data audit | M02/M03 | High: duplicate user links possible | Yes |
| `backend/app/models/officer_profile.py` | Does not exist | CREATE only if officer-specific data requires it | M02 | Medium | No, new boundary |
| `backend/app/models/bid.py` | Does not exist | CREATE: explicit bid submission and ownership model | Later bid milestone | High | No, new boundary |
| `backend/app/api/deps.py` | DB and placeholder context dependencies | MODIFY: authenticated user, role, resource dependencies | M03/M04 | High | No, auth boundary |
| `backend/app/api/router.py` | Domain routes and processing triggers | MODIFY: attach auth/ownership dependencies incrementally | M04+ | High | Domain behavior protected |
| `backend/app/dashboard/` | Task 17 aggregation | MODIFY only for scoping/reuse | Officer dashboard milestone | Medium | Yes |
| `backend/app/review/` | Officer review lifecycle | MODIFY only to derive actor and tender authorization | M04+ | High | Yes |
| `backend/app/services/audit_service.py` | Append-only audit service | MODIFY only for trusted actor context if required | M03/M04 | High | Yes |
| `backend/app/ocr/`, `app/ai/`, `app/integrations/`, `app/verification/`, `app/workers/` | Protected processing systems | DO NOT TOUCH for RBAC design; add callers around them only | All | High | Yes |
| `frontend/src/App.jsx` | Current unguarded route tree | MODIFY: public/authenticated layouts and role guards | Frontend auth milestone | Medium | No |
| `frontend/src/api/client.js` | Fetch wrapper | MODIFY: attach credential and normalize 401/403 | Frontend auth milestone | High | No |
| `frontend/src/components/layout/` | Current single officer-style shell | MODIFY: public, bidder, and officer layouts | Dashboard milestone | Medium | No |
| `frontend/src/components/landing/` | Does not exist | CREATE: isolated landing/3D components | Landing milestone | Medium | No |
| `supabase/migrations/` | Schema history | CREATE new reviewed migrations only; do not edit history | M02+ | High | Schema boundary |
| `supabase/seed.sql` | Demo data | MODIFY only with reviewed identity/profile seed strategy | M02+ | Medium | No |
| `docs/RBAC_ARCHITECTURE.md` | This audit | CREATE in M01 | M01 | Low | No |
| `docs/MILESTONE_STATUS.md` | This status | CREATE in M01 | M01 | Low | No |
| `docs/HANDOFF.md` | Agent handoff | CREATE in M01 | M01 | Low | No |

## Unresolved Questions

- Is Supabase Auth required, or will the backend own credentials and sessions?
- Should a user have exactly one role, or can one identity hold both `BIDDER` and `OFFICER` roles?
- How should existing `admin` and `procurement_officer` rows map to the two-role product model?
- Are there duplicate bidder rows for a single user in live data?
- Is `tender_bidders` an invitation/participation list, or should it be replaced/augmented by a real bid submission table?
- Which officers may access which tenders: creator, department, organization, explicit assignment, or all officers?
- Which evidence fields may a bidder see, especially government payloads and raw OCR text?
- What RLS/service-role boundary will be used with backend-mediated access?
- Which legacy/demo endpoints can be retired after the role-specific APIs exist?

## Milestone 01 Boundary

No source, migration, dependency, or runtime behavior was changed. The next implementation milestone is:

**Milestone 02 — Database User/Role Foundation**
