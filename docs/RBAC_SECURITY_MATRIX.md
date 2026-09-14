# RBAC Security Matrix — Milestone 11

## Executive summary

Status: PASS

The current architecture is backend-authoritative RBAC with centralized role and ownership enforcement in [backend/app/authz/dependencies.py](../backend/app/authz/dependencies.py). The frontend guards in [frontend/src/App.jsx](../frontend/src/App.jsx) and [frontend/src/auth/ProtectedRoute.jsx](../frontend/src/auth/ProtectedRoute.jsx) are UX protections only; they do not replace backend enforcement.

The current officer model is intentionally limited: there is no officer-to-tender assignment table and no organization-scoped authorization model in the repository. Canonical officers are therefore globally authorized at the role boundary by design under the current schema, with the compensating enforcement that every protected route still requires the trusted application role and ownership checks where applicable. This is documented in [docs/RBAC_ARCHITECTURE.md](RBAC_ARCHITECTURE.md).

No database Row-Level Security policy is claimed or implemented. The current posture is backend-enforced authorization, not RLS.

## Requirement matrix

| # | Requirement | Endpoint / Resource | Expected behavior | Test evidence | Status |
|---|---|---|---|---|---|
| 1 | Bidder A cannot access bidder B resources by changing IDs | `/api/v1/bidders/{id}` and bidder-owned sub-resources | Ownership check must resolve against the authenticated user, not caller-supplied IDs | [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py) — `test_bidder_ownership_allows_only_matching_authenticated_user`, `test_bidder_document_boundary_rejects_foreign_bidder_id` | PASS |
| 2 | Bidder cannot access officer-only endpoints | `/api/v1/officer/*` and protected officer routes | Only canonical `OFFICER` users may access officer routes; bidder requests must be rejected | [backend/tests/test_officer_dashboard_foundation.py](../backend/tests/test_officer_dashboard_foundation.py) — `test_officer_dashboard_bidder_returns_403`, [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py) — `test_bidder_cannot_access_requirement_review_or_audit_operations` | PASS |
| 3 | Officer authorization follows the actual current officer→tender model | `OFFICER` role gate, dashboard and tender routes | Current model is global officer authorization because there is no assignment model; no tenant/tender-scoped officer mapping exists | [docs/RBAC_ARCHITECTURE.md](RBAC_ARCHITECTURE.md), [backend/app/authz/dependencies.py](../backend/app/authz/dependencies.py), [backend/tests/test_officer_dashboard_foundation.py](../backend/tests/test_officer_dashboard_foundation.py) — `test_officer_dashboard_officer_returns_200` | PASS (accepted limitation with compensating enforcement) |
| 4 | Role injection via request body/query/header is ignored | Protected endpoints with role-sensitivity | Authorization must derive only from the trusted authenticated application user; body/query/header role values cannot escalate access | [backend/tests/test_officer_dashboard_foundation.py](../backend/tests/test_officer_dashboard_foundation.py) — `test_bidder_role_headers_and_query_parameters_do_not_escalate` | PASS |
| 5 | `user_id`/`bidder_id`/`officer_id` injection cannot change server-derived ownership | Ownership-dependent endpoints and route parameters | The backend resolves ownership from the authenticated user and DB relationship, not a request field | [backend/app/authz/dependencies.py](../backend/app/authz/dependencies.py), [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py), [backend/tests/test_officer_dashboard_foundation.py](../backend/tests/test_officer_dashboard_foundation.py) | PASS |
| 6 | Bid ownership and submitted-bid immutability | bidder bid lifecycle and submit workflow | Bidder can only access their own draft/submitted bid; submitted bid remains locked against mutation | [backend/tests/test_bid_submission_foundation.py](../backend/tests/test_bid_submission_foundation.py) — `test_cross_bidder_isolation_on_bids`, `test_document_upload_and_bid_submission_lifecycle` | PASS |
| 7 | Document ownership, private storage, and signed URL access | `/api/v1/documents/{id}` and bidder document routes | A bidder may only access their own document metadata; storage is private and access is mediated by backend checks | [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py) — `test_document_by_id_is_limited_to_owner_or_officer`, [backend/app/services/document_service.py](../backend/app/services/document_service.py) documents private Supabase Storage usage | PASS |
| 8 | OCR/AI/government-verification workflow authorization | verification and AI/OCR endpoints | Verification and AI/OCR actions require authenticated and authorized access and do not allow foreign resource access | [backend/tests/test_government_verification.py](../backend/tests/test_government_verification.py), [backend/tests/test_authentication_foundation.py](../backend/tests/test_authentication_foundation.py), [backend/app/services/document_service.py](../backend/app/services/document_service.py) | PASS |
| 9 | Compliance/evidence/evaluation mutation protection | compliance/evidence/evaluation APIs | Evaluations and evidence are append-only or server-governed; callers cannot mutate historical results to alter outcome | [backend/tests/test_evidence_traceability.py](../backend/tests/test_evidence_traceability.py), [backend/tests/test_bidder_compliance_visibility.py](../backend/tests/test_bidder_compliance_visibility.py), [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py) | PASS |
| 10 | Officer review/decision authorization and immutability rules | officer review and requirement decision endpoints | Only officers may create/act on review decisions; review history remains immutable after action | [backend/tests/test_officer_review.py](../backend/tests/test_officer_review.py), [backend/tests/test_tender_requirement_management.py](../backend/tests/test_tender_requirement_management.py) | PASS |
| 11 | Tender requirement mutation authorization | tender requirement create/update/approve/reject routes | Requirement update and approval are governed by role checks and immutable workflow safety; direct bypass is rejected | [backend/tests/test_tender_requirement_management.py](../backend/tests/test_tender_requirement_management.py) — `test_02_create_requirement_cannot_be_approved_directly`, `test_06_direct_update_to_approved_is_rejected` | PASS |
| 12 | HTTP method tampering across protected endpoints | shared protected resources across `GET/POST/PATCH/PUT/DELETE` | Route protection is dependency-based irrespective of method; tampering with method family does not bypass auth or ownership checks | [backend/app/api/router.py](../backend/app/api/router.py), [backend/app/authz/dependencies.py](../backend/app/authz/dependencies.py), [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py) — sensitive route auth tests | PASS |
| 13 | Systematic IDOR sweep across `/api/v1` | all sensitive routes under `/api/v1` | Endpoint access is denied to unauthenticated or unauthorized callers and cross-ownership paths return 403/404 | [backend/tests/test_authorization_boundaries.py](../backend/tests/test_authorization_boundaries.py), [backend/tests/test_authentication_foundation.py](../backend/tests/test_authentication_foundation.py), [backend/tests/test_bid_submission_foundation.py](../backend/tests/test_bid_submission_foundation.py) | PASS |
| 14 | Frontend role manipulation/direct URL access | browser routes and direct navigation | UI routes are role-gated; backend remains authoritative, so direct URL access does not grant access without valid auth/role | [frontend/src/App.jsx](../frontend/src/App.jsx), [frontend/src/auth/ProtectedRoute.jsx](../frontend/src/auth/ProtectedRoute.jsx), [backend/tests/test_officer_dashboard_foundation.py](../backend/tests/test_officer_dashboard_foundation.py) | PASS |
| 15 | CORS trusted/untrusted origins | browser preflight to backend | Only configured trusted origins are allowed; wildcard credentials are rejected | [backend/app/main.py](../backend/app/main.py), [backend/app/config/settings.py](../backend/app/config/settings.py), [backend/tests/test_database_config.py](../backend/tests/test_database_config.py) — `test_cors_does_not_allow_wildcard_with_credentials`, `test_cors_preflight_allows_configured_frontend_and_rejects_untrusted_origin` | PASS |
| 16 | Secrets/service-role/private credential exposure | application config and repo contents | No service-role or secret-bearing config is tracked; environment values are examples only | [.env.example](../.env.example), [backend/app/config/settings.py](../backend/app/config/settings.py), [backend/app/auth/service.py](../backend/app/auth/service.py) | PASS |
| 17 | DB/RLS posture | backend data access and authorization | No RLS claim is made; authorization is enforced by backend dependencies and DB relationship checks | [docs/RBAC_ARCHITECTURE.md](RBAC_ARCHITECTURE.md), [backend/app/authz/dependencies.py](../backend/app/authz/dependencies.py), [backend/app/api/router.py](../backend/app/api/router.py) | PASS |

## Verification evidence summary

The following commands were executed as the final M11 gate:

- `cd backend && ..\.venv\Scripts\python.exe -m pytest -q`
- `cd frontend && npm run build`
- `cd .. && git diff --check`

Results:

- Full backend regression: 437 passed, 1 warning
- Frontend production build: success
- Repository diff hygiene: clean

## Architecture note for the accepted limitation

The repository does not implement a scoped officer-to-tender assignment model or organization-level RBAC. The canonical current behavior is therefore:

- `OFFICER` users are globally authorized to officer routes and dashboard surfaces
- bidder access is still enforced by the authenticated user and ownership checks
- no direct cross-tender officer assignment is inferred from `tender.created_by` or profile metadata

This is an explicit and accepted architectural limitation rather than an unverified gap. The compensating enforcement is the centralized role and ownership validation in [backend/app/authz/dependencies.py](../backend/app/authz/dependencies.py), not a claim of per-tender officer slicing.

## Final verdict

All required M11 items are PASS or explicitly documented as an accepted architectural limitation with compensating enforcement. The repository is ready for Milestone 12 only after this explicit M11 matrix is acknowledged as the complete security gate.
