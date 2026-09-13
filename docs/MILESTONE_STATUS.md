# SecondLook Milestone Status

Current Milestone: 07 — Bidder Profile + Bidder Workspace
Status: COMPLETED


## What Was Inspected

- Repository structure, README files, Docker/configuration files, frontend package manifest, backend requirements, and test configuration.
- FastAPI entry point, API dependencies, routers, services, repositories, workers, storage integration, OCR, AI, government integrations, verification, evidence, compliance, review, dashboard, and audit modules.
- SQLAlchemy models and all inspected Supabase migrations under `supabase/migrations/`.
- React entry point, `App.jsx`, BrowserRouter route tree, layouts, navigation, pages, API client, frontend services, and current local/session storage usage.
- Backend and integration tests covering Tasks 01-20 behavior.
- Milestone 02 role/profile models, migration conventions, seed data, and existing test role values.

## Architecture Findings

- Supabase Auth provides authentication for login and signup flows. Supabase is also used for PostgreSQL and private Storage integration.
- FastAPI domain routes enforce centralized authentication and role/ownership authorization dependencies implemented in M4.
- A local `users` table/model exists with constrained canonical `BIDDER` and `OFFICER` roles alongside temporary legacy compatibility values.
- `bidders.user_id` links bidder records to `users.id` and is unique; `users.auth_user_id` is a nullable unique Supabase identity mapping.
- `officer_profiles` is the existing one-to-one officer profile foundation. No bid submission table exists; `tender_bidders` is the current tender/bidder association.
- Frontend routes enforce centralized ProtectedRoute guards with canonical BIDDER and OFFICER namespaces and role-aware navigation implemented in M5.
- Documents, evidence, evaluations, reviews, audit events, and processing endpoints are protected by centralized ownership and role dependencies.
- Existing OCR, AI, government verification, evidence, compliance, review, audit, worker, Storage, and Task 17/19/20 systems are established protected systems.

## Files Created

- `backend/app/models/officer_profile.py`
- `backend/tests/test_user_role_foundation.py`
- `supabase/migrations/20260913_add_user_role_profiles.sql`
- `supabase/migrations/20260913_add_auth_identity_mapping.sql`
- `docs/M2_BLOCKER_ANALYSIS.md`
- `m2_reconciliation_snapshot.json`
- `backend/app/auth/__init__.py`
- `backend/app/auth/service.py`
- `backend/app/auth/dependencies.py`
- `backend/app/schemas/auth.py`
- `backend/tests/test_authentication_foundation.py`
- `frontend/src/auth/supabaseClient.js`
- `frontend/src/auth/AuthContext.jsx`
- `frontend/src/pages/LoginPage.jsx`
- `backend/app/services/signup_service.py`
- `backend/tests/test_signup_foundation.py`
- `backend/app/authz/__init__.py`
- `backend/app/authz/dependencies.py`
- `backend/tests/test_authorization_boundaries.py`
- `backend/tests/conftest.py`
- `frontend/src/auth/ProtectedRoute.jsx`
- `frontend/src/pages/bidder/BidderWorkspacePage.jsx`
- `frontend/src/components/landing/Hero3D.jsx`
- `frontend/src/components/landing/PublicNavbar.jsx`
- `frontend/src/pages/LandingPage.jsx`
- `backend/tests/test_bidder_workspace_foundation.py`
- `frontend/src/pages/bidder/BidderProfilePage.jsx`
- `frontend/src/pages/bidder/BidderTendersPage.jsx`
- `frontend/src/pages/bidder/BidderPlaceholderPage.jsx`

## Files Modified

- `backend/app/models/user.py`
- `backend/app/models/bidder.py`
- `backend/app/models/__init__.py`
- `backend/app/api/router.py`
- `backend/app/dashboard/router.py`
- `backend/app/schemas/__init__.py`
- `frontend/src/auth/AuthContext.jsx`
- `frontend/src/main.jsx`
- `frontend/src/App.jsx`
- `frontend/src/components/layout/Header.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/pages/LoginPage.jsx`
- `frontend/src/pages/SignupPage.jsx`
- `frontend/package.json`
- `frontend/package-lock.json`
- `.env.example`
- `docker-compose.yml`
- `backend/tests/test_compliance_orchestration.py`
- `backend/tests/test_evidence_traceability.py`
- `backend/tests/test_tender_requirement_management.py`
- `docs/RBAC_ARCHITECTURE.md`
- `docs/MILESTONE_STATUS.md`
- `docs/HANDOFF.md`
- `docs/M2_BLOCKER_ANALYSIS.md`
- `backend/app/schemas/bidder.py`
- `backend/app/services/bidder_service.py`
- `frontend/src/api/client.js`
- `frontend/src/services/bidderService.js`
- `frontend/src/pages/bidder/BidderWorkspacePage.jsx`


## Tests / Checks

The following checks were run after the M02 implementation:

- `git status --short`
- `git diff --check`
- `git diff --stat`
- `git diff --name-only`

Results:

- `git diff --check`: passed with no output.
- `git diff --stat`: reported only the pre-existing tracked deletions under `tasks/task*.md`.
- `git diff --name-only`: reported only those pre-existing tracked task files.
- `git status --short`: showed the three new docs, the pre-existing `tasks/m*.md` files, and the pre-existing `tasks/task*.md` deletions.
- Direct file check: all three documentation files exist and are non-empty.
- `python -m compileall -q app tests/test_user_role_foundation.py`: passed.
- SQLite runtime probe: duplicate bidder profile rejected.
- `python -m pytest -q tests/test_user_role_foundation.py` using the root `.venv`: 6 passed in 2.82s.
- Read-only live preflight through `psycopg`: found one legacy `admin` user and one duplicate bidder-user group containing three bidder profiles.

Pre-existing task-file and M01 documentation changes were present before the M02 implementation and remain untouched outside the listed M02 files.

## Architecture Decisions

- Preserve existing `users.id` and all historical foreign-key identifiers.
- Resolve the canonical identity provider before implementing migrations.
- Normalize new product authorization to exactly `BIDDER` and `OFFICER`; explicitly map legacy role values.
- Use backend authentication, role dependencies, and resource ownership checks as the security boundary.
- Preserve and wrap existing OCR, AI, government verification, evidence, compliance, review, audit, worker, Storage, and dashboard systems.
- Add a real bid submission model before implementing bidder bid uploads.
- Require an explicit decision for officer-to-tender authorization before protecting officer workflows.
- Use an explicit compatibility allowlist for legacy `admin` and `procurement_officer` values until a later reviewed backfill removes them.
- Preserve existing bidder records and fail the migration if duplicate `bidders.user_id` values require manual resolution.
- Do not add Supabase Auth, RLS, authentication, or RBAC in M02.

## Known Risks

- Officer access scope is based on the canonical OFFICER role; fine-grained tender assignment beyond tender creation remains an open model decision.
- Legacy/demo endpoints coexist with database-backed endpoints and need a staged retirement plan once full frontend workflows are complete.
- No database RLS policies exist; authorization is enforced centrally at the backend API layer.
- Frontend role-based routing is not yet implemented (scheduled for Milestone 05).

## Reconciliation Result

The human decision confirmed ABC Technologies Pvt Ltd, XYZ Infrastructure Ltd, and DEF Engineering Services Ltd are three separate development/demo bidder organizations. They were not merged or deleted. A local rollback snapshot was captured in `m2_reconciliation_snapshot.json` before mutation.

The exact transactional reconciliation was:

| User | Role | Bidder |
|---|---|---|
| `...001` `admin@gem.gov.in` | unchanged legacy `admin` | none |
| `...031` `demo.bidder.abc@secondlook.local` | `BIDDER` | `...021` ABC Technologies Pvt Ltd |
| `...032` `demo.bidder.xyz@secondlook.local` | `BIDDER` | `...022` XYZ Infrastructure Ltd |
| `...033` `demo.bidder.def@secondlook.local` | `BIDDER` | `...023` DEF Engineering Services Ltd |

Users inserted: 3. Bidder ownership updates: 3. Rows deleted: 0. Bidder/tender/document/OCR/AI/verification/compliance/evidence/audit deletions: 0.

The migration `20260913_add_user_role_profiles.sql` was then applied in one PostgreSQL transaction. It created the unique bidder ownership index, canonical role check with legacy compatibility, and the one-to-one `officer_profiles` foundation.

The following later decisions remain open:

1. Canonical authentication identity: Supabase Auth mapping or backend-owned identity/session.
2. Single-role versus multi-role account semantics.
3. Mapping of existing `admin` and `procurement_officer` records.
4. Officer-to-tender authorization model.
5. Bid submission data model and its relationship to `tender_bidders`.

These are later design decisions and do not require changing protected systems in M02.

## M2 Verification

The completed investigation and reconciliation are recorded in [docs/M2_BLOCKER_ANALYSIS.md](M2_BLOCKER_ANALYSIS.md).

- Bidder `...021`: 1 tender, 2 documents.
- Bidder `...022`: 1 different tender, 2 documents, 1 OCR-completed document.
- Bidder `...023`: 1 different tender, no documents, flagged status.
- No live bids table exists.
- No live verification, compliance, evidence, or direct audit-entity references were found for these bidders.
- The live `officer_reviews` and `requirement_reviews` tables are absent even though their migration/model definitions exist in the repository.
- All three bidder UUIDs remain present and each has exactly one owner.
- All 3 `tender_bidders` rows and all 4 documents remain present with unchanged OCR/AI states.
- Duplicate bidder-user groups: 0. Legacy admin bidder profiles: 0.
- No live verification, compliance, evidence, or direct audit-entity references existed for these bidders; all counts remain unchanged at zero.

## M3A — Authentication Foundation

M3A establishes Supabase Auth as the authentication provider without implementing role-based signup or authorization.

- Frontend uses `@supabase/supabase-js` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`.
- `AuthProvider` restores sessions, subscribes to Supabase auth state changes, exposes the current Auth user, and supports logout.
- `/login` performs Supabase email/password sign-in and navigates to the existing `/dashboard` destination. No signup UI was added.
- `users.auth_user_id` is a nullable additive mapping to the Supabase Auth UUID with a partial unique index.
- Backend validates bearer credentials by calling Supabase Auth `/auth/v1/user`; it never creates or signs JWTs.
- `/api/v1/auth/me` resolves the validated Auth UUID to an active application User. Identity lookup is not role authorization.
- Unmapped Auth identities are rejected with a safe error rather than being assigned a role or privileged profile.
- No passwords, password hashes, tokens, service-role credentials, route guards, dashboards, or protected business routes were added.

Focused M3A tests: `6 passed`.
Frontend build: `npm run build` passed.
Database verification: `uq_users_auth_user_id` exists; M2 demo bidder, tender, and document counts remain unchanged.

## M3 — Role-Based Signup

M3 reuses M3A Supabase Auth and adds explicit role/profile provisioning only.

- `/signup` requires an explicit account type; no role is selected by default.
- Only `BIDDER` and `OFFICER` can pass backend validation.
- BIDDER signup collects `full_name`, required `legal_name`, and the existing optional bidder fields: registration number, GST number, and PAN number.
- OFFICER signup collects only the required application `full_name`; `OfficerProfile` contributes only its existing `user_id` and timestamps.
- After Supabase Auth returns an authenticated session, the frontend calls `/api/v1/auth/provision` with the bearer token.
- The backend creates `users.auth_user_id`, `users.role`, and exactly one role-specific profile in one database transaction.
- BIDDER creates `Bidder`; OFFICER creates `OfficerProfile`; the opposite profile is never requested or created.
- Duplicate Auth mappings, duplicate emails, duplicate profiles, invalid roles, and missing bidder company names are rejected safely.
- Existing M2 demo organizations and all historical records remain unchanged.

Focused M3 tests: `14 passed` including authentication compatibility tests.
Full backend regression: `368 passed, 1 warning`.
Frontend build: `npm run build` passed.

When Supabase email confirmation is enabled, signup may return without a session. In that case no application profile is created until a confirmed authenticated session is available; the UI reports this limitation without creating an orphaned application record.

## M4 — Authentication + Backend Role Enforcement

M4 makes the backend the authorization boundary while reusing M3A authentication. `get_authenticated_identity` remains the single Supabase bearer-token and application-User resolution path. `require_role(ApplicationRole.BIDDER/OFFICER)` is centralized in `backend/app/authz/dependencies.py`; legacy `admin` and `procurement_officer` values are not silently treated as canonical roles.

Protected boundaries:

- Officer-only: `GET /api/v1/tenders/{id}/bidders`, `GET /api/v1/dashboard/summary`, `GET /api/v1/tenders/{tender_id}/dashboard`, and `GET /api/v1/tenders/{tender_id}/dashboard/requirements`.
- Bidder-owned: `GET /api/v1/bidders/{id}`, `POST/GET /api/v1/bidders/{bidder_id}/documents`.
- Document ownership: document metadata, signed access, OCR, AI, retry, and government-verification routes allow the owning BIDDER or an OFFICER.

Ownership is resolved from the authenticated application User to `Bidder.user_id`; path, query, body, and `X-Role` values are never used as identity or role authority. Existing legacy contract tests use a test-only dependency override in `backend/tests/conftest.py`; production routes retain the real dependencies.

Focused M4 security tests: `22 passed`.
Full backend regression: `390 passed, 1 warning`.
No migration was required. No frontend source was changed for M4.

All sensitive bidder, tender, document, compliance, evidence, verification, requirement, review, audit, and dashboard routes now require centralized authentication and role/ownership authorization. Only health and authentication operations remain intentionally public or authentication-scoped.

## M5 — Frontend Role-Based Routing + Navigation

M5 establishes frontend role-aware routing, centralized route protection, and navigation using the canonical `BIDDER` and `OFFICER` roles established by M02–M04:

- `AuthContext` resolves canonical `role` via `/api/v1/auth/me` with `isRoleLoading` and `isAuthResolving` tracking to eliminate redirect flicker.
- Reusable centralized `ProtectedRoute` guard handles:
  1. Active authentication/role resolution -> non-flickering loading indicator.
  2. Unauthenticated state -> redirect to `/login` with return location.
  3. Unknown/invalid role -> safe role-unavailable notice (never defaults to BIDDER or OFFICER, never renders privileged content).
  4. Role mismatch -> redirects BIDDER attempting officer access to `/bidder`, and OFFICER attempting bidder access to `/officer`.
  5. Authorized state -> renders destination workspace.
- Namespaced public routes: `/`, `/login`, `/signup`.
- Namespaced BIDDER routes: `/bidder`, `/bidder/tenders`, `/bidder/bids`, `/bidder/compliance`, `/bidder/documents`, `/bidder/profile`.
- Namespaced OFFICER routes: `/officer`, `/officer/dashboard`, `/officer/tenders`, `/officer/tenders/:id`, `/officer/bidders`, `/officer/evaluations`, `/officer/reviews`, `/officer/audit`, `/officer/documents`.
- Preserved existing domain routes wrapped under Officer role protection.
- Role-aware sidebar navigation: dedicated items for BIDDER vs. OFFICER; no cross-role link exposure.
- Role-aware header: displays canonical role badge (`BIDDER` or `OFFICER`), role-based logo navigation, and clean logout.

Frontend build: `npm run build` passed.
Full backend regression: `390 passed, 1 warning`.

FRONTEND ROUTE PROTECTION IS IMPLEMENTED FOR UX/NAVIGATION.

BACKEND RBAC REMAINS THE AUTHORITATIVE SECURITY BOUNDARY.

## M6 — SecondLook Landing Page + 3D Experience

M6 establishes the public product narrative and lightweight 3D visual hero on the frontend root route (`/`) without modifying backend authentication, backend RBAC, or procurement business logic:

- `LandingPage.jsx`: Public product narrative explaining SecondLook's 5-step deterministic procurement evaluation pipeline (Upload → Extract → Verify → Evaluate → Review).
- `Hero3D.jsx`: Interactive Three.js "Evidence & Compliance Inspection Constellation" featuring a rotating faceted gateway core, orbital document cards, and statutory verification nodes.
  - Lifecycle: `IntersectionObserver` halts the render loop when off-screen; full disposal on unmount.
  - Accessibility: Respects `prefers-reduced-motion` media queries.
  - Reliability: Graceful SVG/CSS fallback if WebGL is unavailable or fails.
  - Performance: Code-split via `React.lazy` into an isolated chunk to maintain fast initial page load times.
- `PublicNavbar.jsx`: Dedicated public navigation with brand tricolor accent, semantic anchor links, light/dark theme toggle, and direct role signup CTAs.
- Direct Role CTAs (`Sign up as Bidder` / `Sign up as Officer`) connecting to `/signup?role=bidder` and `/signup?role=officer` with preselected account type cards.
- Layout Integration: `MainLayout.jsx` automatically presents a full-width experience without internal enterprise sidebar for unauthenticated visitors on `/`.
- Dynamic Root Preservation: Authenticated users visiting `/` continue redirecting to their canonical role workspace (`/bidder` or `/officer`) via `RootRoute`.

Authentication and Security Boundary:
- Authentication/RBAC architecture was not redesigned.
- Backend RBAC enforcement was not changed.
- `AuthContext` and `ProtectedRoute` were not changed.
- `SignupPage.jsx` was modified only to support landing-page role preselection via `?role=bidder` / `?role=officer`.
- The signup query parameter remains UI-only.
- Backend `/api/v1/auth/provision` remains authoritative for role validation.

Frontend build: `npm run build` passed (with code-split 3D bundle).
Full backend regression: `390 passed, 1 warning`.

LANDING PAGE IMPLEMENTED.

AUTHENTICATION/RBAC NOT REDESIGNED.

BACKEND RBAC REMAINS THE AUTHORITATIVE SECURITY BOUNDARY.

## M7 — Bidder Profile + Bidder Workspace Foundation

Milestone 07 implements the authenticated BIDDER product foundation:

- `GET /api/v1/bidders/me`: Secure backend profile endpoint protected by `require_bidder`. Resolves profile strictly from the authenticated application user (`current_user.id == Bidder.user_id`).
- Profile & Ownership Security: Cross-bidder access denied via `require_owned_bidder_by_id` (403 Forbidden). Officer access to bidder profile endpoints denied (403 Forbidden). Bidder access to officer endpoints denied (403 Forbidden).
- Read-Only Statutory Profile: Statutory company attributes (Legal Name, GSTIN, PAN, CIN) are established at registration and verified against government authorities. Self-service modification is restricted to preserve compliance audit integrity.
- Bidder Workspace (`/bidder`): Welcome company greeting, account summary with masked statutory identifiers (`29******Z5`, `AA*****1A`), real metric counts (`active_tenders_count`, `documents_count`, `submitted_bids_count = 0`), and module navigation.
- Bidder Profile Page (`/bidder/profile`): Displays verified corporate attributes with reveal/mask toggle and statutory integrity notice.
- Bidder Tender Discovery (`/bidder/tenders`): Read-only discovery of published procurement tenders using existing `GET /api/v1/tenders` and `GET /api/v1/tenders/{id}`, with detailed inspection modal and M8 bid submission notices.
- Honest Placeholder States:
  - My Bids (`/bidder/bids`): Clear milestone notice that bid submission opens in Milestone 08.
  - Bidder Documents (`/bidder/documents`): Clear milestone notice that document upload opens in Milestone 08.
  - Compliance (`/bidder/compliance`): Clear milestone notice that compliance evaluation opens in Milestone 09.
- Frontend API Client: Transparently attaches `Bearer ${token}` from Supabase Auth session for authenticated API calls.

Focused M7 tests: `7 passed`.
Full backend regression: `397 passed, 1 warning`.
Frontend build: `npm run build` passed.

BIDDER WORKSPACE FOUNDATION IS IMPLEMENTED.

ACTUAL BID SUBMISSION IS NOT IMPLEMENTED.

BIDDER DOCUMENT UPLOAD/PROCESSING IS NOT IMPLEMENTED.

BIDDER COMPLIANCE SCORING IS NOT IMPLEMENTED.

OFFICER DASHBOARD IS NOT IMPLEMENTED.

MILESTONE 08 NOT STARTED.

## Next Milestone

Milestone 08 — Bid Submission + Bidder Document Workflow

## STRICT DO NOT

- implement actual bid upload
- implement bid submission
- implement bidder document processing workflow
- implement bidder OCR workflow
- implement bidder AI extraction
- implement bidder compliance scoring
- implement officer dashboard
- start Milestone 08 before review
