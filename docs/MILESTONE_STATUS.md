# SecondLook Milestone Status

Current Milestone: 02  
Status: BLOCKED

## What Was Inspected

- Repository structure, README files, Docker/configuration files, frontend package manifest, backend requirements, and test configuration.
- FastAPI entry point, API dependencies, routers, services, repositories, workers, storage integration, OCR, AI, government integrations, verification, evidence, compliance, review, dashboard, and audit modules.
- SQLAlchemy models and all inspected Supabase migrations under `supabase/migrations/`.
- React entry point, `App.jsx`, BrowserRouter route tree, layouts, navigation, pages, API client, frontend services, and current local/session storage usage.
- Backend and integration tests covering Tasks 01-20 behavior.
- Milestone 02 role/profile models, migration conventions, seed data, and existing test role values.

## Architecture Findings

- Authentication does not currently exist.
- Supabase Auth is not used. Supabase is currently used for PostgreSQL and private Storage integration.
- FastAPI routes have no authentication or role dependencies. The request context dependency explicitly reports `authenticated: false` as a contract placeholder.
- A local `users` table/model exists with a free-form `role` field defaulting to legacy `admin`; tests use `procurement_officer`.
- `bidders.user_id` links bidder records to `users.id`, but is not unique.
- No officer profile table or bid submission table exists. `tender_bidders` is the current tender/bidder association.
- Frontend routes are inside one unguarded layout. `/login` is a placeholder; the header uses a hard-coded officer display. `localStorage` is used only for theme preference.
- Documents, evidence, evaluations, reviews, audit events, and processing endpoints are currently addressable by resource IDs without caller ownership checks.
- Existing OCR, AI, government verification, evidence, compliance, review, audit, worker, Storage, and Task 17/19/20 systems are established protected systems.

## Files Created

- `backend/app/models/officer_profile.py`
- `backend/tests/test_user_role_foundation.py`
- `supabase/migrations/20260913_add_user_role_profiles.sql`

## Files Modified

- `backend/app/models/user.py`
- `backend/app/models/bidder.py`
- `backend/app/models/__init__.py`
- `docs/RBAC_ARCHITECTURE.md`
- `docs/MILESTONE_STATUS.md`
- `docs/HANDOFF.md`

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
- `python -m pytest -q tests/test_user_role_foundation.py`: unavailable because pytest is not installed.
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

- Existing role data is not constrained and includes values outside the target role model.
- Existing `bidders.user_id` cardinality is not one-to-one by database constraint.
- No current mapping exists between Supabase Auth identities and local `users` rows.
- Officer access scope is not modeled beyond tender creator references.
- Broad unauthenticated routes currently expose bidder, document, evidence, evaluation, review, and audit data.
- Some routes accept actor IDs in request bodies or optional parameters; these must eventually be derived from authenticated identity.
- Legacy/demo endpoints coexist with database-backed endpoints and need a staged authorization/retirement plan.
- No RLS policies were found in the inspected migrations.

## Blockers

The live PostgreSQL preflight succeeded through the installed `psycopg` driver and found one `user_id` with three bidder profiles. The M02 migration intentionally raises before creating `uq_bidders_user_id`, so it cannot apply until those existing records are manually classified and resolved without deleting historical data. The focused pytest suite was unavailable because pytest is not installed in the active interpreter.

Evidence: `SELECT user_id, COUNT(*) FROM bidders GROUP BY user_id HAVING COUNT(*) > 1` returned one group: `00000000-0000-0000-0000-000000000001`, count `3`.

The live role preflight also found one `admin` user. The compatibility check allows that legacy value temporarily; it must be explicitly classified before a later migration removes legacy roles.

The following later decisions remain open:

1. Canonical authentication identity: Supabase Auth mapping or backend-owned identity/session.
2. Single-role versus multi-role account semantics.
3. Mapping of existing `admin` and `procurement_officer` records.
4. Officer-to-tender authorization model.
5. Bid submission data model and its relationship to `tender_bidders`.

These are later design decisions and do not require changing protected systems in M02.

## M2 Blocker Investigation

Read-only investigation is complete. See [docs/M2_BLOCKER_ANALYSIS.md](M2_BLOCKER_ANALYSIS.md).

- Bidder `...021`: 1 tender, 2 documents.
- Bidder `...022`: 1 different tender, 2 documents, 1 OCR-completed document.
- Bidder `...023`: 1 different tender, no documents, flagged status.
- No live bids table exists.
- No live verification, compliance, evidence, or direct audit-entity references were found for these bidders.
- The live `officer_reviews` and `requirement_reviews` tables are absent even though their migration/model definitions exist in the repository.
- Multiple rows contain independent history, so no canonical record was selected.
- Manual business/data reconciliation is required before applying the M2 migration.

## Next Milestone

Milestone 03 — Role-Based Signup

## STRICT DO NOT

- implement authentication
- implement signup
- implement login
- implement RBAC
- create role middleware
- create dashboards
- modify compliance
- modify OCR
- modify AI
- modify government verification
- modify evidence
- modify officer review
- modify workers
- modify historical migrations
- implement authentication
- implement RBAC middleware
- apply the M02 migration before the duplicate bidder-user data is resolved
