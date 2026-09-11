# Dynamic Data Audit

**Project:** SecondLook — GeM Bid Compliance & Statutory Verification Platform  
**Audit Date:** September 2026  
**Scope:** Full repository audit (Frontend React, Backend FastAPI, Supabase PostgreSQL, Demo Data, Integrations, and Tests)  
**Objective:** Document current data flow, pinpoint all hardcoded and static data sources, map backend endpoints to database tables, and establish a dependency-ordered dynamic integration roadmap without prematurely altering existing code.

---

## 1. Current Architecture

The SecondLook platform is currently structured into three distinct layers with minimal inter-layer runtime coupling:

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                   │
│  - 10 pages, reusable UI components, CSS design tokens       │
│  - 100% of pages read from local static demo files          │
│  - Zero network/API calls made from React components         │
└──────────────────────────────┬──────────────────────────────┘
                               │ (MISSING CONNECTION)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)                  │
│  - REST API routes under `/api/v1`                          │
│  - Contract-only demo service classes                       │
│  - Services return hardcoded dicts; no DB queries executed  │
│  - Only `DemoGovernmentRepository` has real DB read logic   │
└──────────────────────────────┬──────────────────────────────┘
                               │ (PARTIALLY WIRED)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Supabase Database (PostgreSQL)              │
│  - 9 tables provisioned via SQL migrations                  │
│  - SQLAlchemy ORM models and settings configured            │
│  - Contains seeded `demo_government_records`                │
│  - Core domain tables (tenders, bidders) currently empty    │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Findings:
1. **Frontend Isolation:** The frontend operates entirely as a deterministic standalone mockup. All routing, filtering, stat counts, and simulated verification animations rely directly on `frontend/src/data/demoData.js` and `frontend/src/data/dashboardData.js`. No `fetch` or HTTP client exists in `frontend/src/`.
2. **Backend Service Stubbing:** The FastAPI routes in `backend/app/api/router.py` strictly serve the M09/M10 contract boundary. The service layer (`TenderService`, `BidderService`, `DocumentService`, `VerificationService`) returns hardcoded dictionaries with dummy UUIDs (`00000000-0000-0000-0000-000000000001`, etc.).
3. **Database Layer Status:** SQLAlchemy database configuration (`connection.py`, `repository.py`, `settings.py`) and full declarative ORM models (`app/models/`) are properly written and match the Supabase migrations. However, none of the service classes inject or invoke the database session for core entities.

---

## 2. Frontend Pages

| Page | File | Current Data Source | API Connected | Backend Endpoint | Supabase Source | Status |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **Dashboard** | `frontend/src/pages/DashboardPage.jsx` | `dashboardData.js` (`DASHBOARD_STATS`, `COMPLIANCE_DATA`, `RISK_DATA`, `RECENT_TENDERS`) | No | `GET /api/v1/dashboard/summary`, `GET /api/v1/tenders` | `tenders`, `bidders`, `verification_jobs`, `verification_results` | Static / Mock data |
| **Tenders** | `frontend/src/pages/TendersPage.jsx` | `demoData.js` (`DEMO_TENDERS`) | No | `GET /api/v1/tenders` | `tenders` | Static / Mock data |
| **Tender Details** | `frontend/src/pages/TenderDetailPage.jsx` | `demoData.js` (`getTenderById`, `getBiddersByTender`) | No | `GET /api/v1/tenders/{id}` | `tenders`, `tender_bidders`, `bidders` | Static / Mock data |
| **Bidders** | `frontend/src/pages/BiddersPage.jsx` | `demoData.js` (`getAllBidders`, `getTenderById`) | No | `GET /api/v1/bidders` | `bidders` | Static / Mock data |
| **Bidder Details** | `frontend/src/pages/BidderDetailPage.jsx` | `demoData.js` (`getBidderById`, `getDocumentsByBidder`, `getTenderById`) | No | `GET /api/v1/bidders/{id}` | `bidders`, `documents`, `tenders`, `tender_bidders` | Static / Mock data |
| **Documents** | `frontend/src/pages/DocumentsPage.jsx` | `demoData.js` (`DEMO_DOCUMENTS`, `getBidderById`) | No | `POST /api/v1/documents/upload` *(Missing `GET /documents`)* | `documents`, `bidders` | Static / Mock data |
| **Verification** | `frontend/src/pages/VerificationPage.jsx` | `demoData.js` (`getAllBidders`, `getBidderById`, `getVerificationResult`) + simulated `setInterval` | No | `POST /api/v1/verification/start`, `GET /api/v1/verification/{id}` | `verification_jobs`, `verification_results`, `demo_government_records` | Static / Simulated runner |
| **Audit Log** | `frontend/src/pages/AuditPage.jsx` | `demoData.js` (`DEMO_AUDIT_LOG`) | No | `GET /api/v1/audit/{id}` *(Missing `GET /audit`)* | `audit_logs`, `users` | Static / Mock data |
| **Settings** | `frontend/src/pages/SettingsPage.jsx` | Local constants (`THRESHOLD_SETTINGS`, `API_REGISTRIES`) | No | None *(No settings endpoint)* | None (platform config) | Static / Read-only UI |
| **Portal Access / Login** | `frontend/src/pages/PlaceholderPage.jsx` | Hardcoded component props in `App.jsx` | No | None *(No auth endpoint)* | `users` | Static placeholder |

---

## 3. Static Data Locations

| File | Data | Used By | Replacement Needed |
| :--- | :--- | :--- | :--- |
| `frontend/src/data/dashboardData.js` | `DASHBOARD_STATS`, `COMPLIANCE_DATA`, `RISK_DATA`, `RECENT_TENDERS` | `DashboardPage.jsx` | Wire to `GET /api/v1/dashboard/summary` and `GET /api/v1/tenders?limit=5`. |
| `frontend/src/data/demoData.js` | `DEMO_TENDERS` (6 records), `DEMO_BIDDERS` (6 records), `DEMO_DOCUMENTS` (10 records), `DEMO_VERIFICATION_RESULTS` (6 result sets), `DEMO_AUDIT_LOG` (10 event records), and 6 helper lookup functions | `TendersPage.jsx`, `TenderDetailPage.jsx`, `BiddersPage.jsx`, `BidderDetailPage.jsx`, `DocumentsPage.jsx`, `VerificationPage.jsx`, `AuditPage.jsx` | Replace direct module imports with async API service calls backed by Supabase DB rows. |
| `frontend/src/pages/SettingsPage.jsx` | Hardcoded arrays `THRESHOLD_SETTINGS` (5 items) and `API_REGISTRIES` (7 items) | `SettingsPage.jsx` | Connect to backend health check / registry status endpoint or preserve as UI configuration until settings API is created. |
| `frontend/src/components/layout/Header.jsx` | Hardcoded auditor profile (`"Auditor Officer"`, initials `"AO"`) and `"Demo Portal"` badge | `Header.jsx` | Connect to current user/session context once authentication is wired. |
| `backend/app/services/tender_service.py` | Single hardcoded mock tender item (`DEMO-TENDER-001`, UUID `00000000-0000-0000-0000-000000000001`) | `list_tenders`, `get_tender` in `api/router.py` | Replace hardcoded dictionary returns with SQLAlchemy queries against `tenders` table. |
| `backend/app/services/bidder_service.py` | Single hardcoded mock bidder item (`DEMO-BIDDER-001`, UUID `00000000-0000-0000-0000-000000000002`) | `list_bidders`, `get_bidder` in `api/router.py` | Replace hardcoded dictionary returns with SQLAlchemy queries against `bidders` table. |
| `backend/app/services/document_service.py` | Hardcoded mock upload metadata returning fixed UUID `00000000-0000-0000-0000-000000000004` without storing files | `upload_document` in `api/router.py` | Implement actual storage handling (Supabase Storage / local volume) and persist document row into `documents` table. |
| `backend/app/services/verification_service.py` | Hardcoded job UUID `00000000-0000-0000-0000-000000000003` and static result envelope | `start_verification`, `get_verification` in `api/router.py` | Persist verification jobs to `verification_jobs` table, trigger verification pipeline/worker, and persist `verification_results`. |
| `backend/app/api/router.py` | Hardcoded zero-counts dictionary in `get_dashboard_summary` and single dummy event in `get_audit` | `/api/v1/dashboard/summary`, `/api/v1/audit/{id}` | Connect to live aggregation queries and `audit_logs` table queries. |

---

## 4. Existing Backend APIs

| Method | Endpoint | File | Purpose | Database Connected | Status |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `GET` | `/` | `backend/app/main.py` | Root service identification probe | NO | Implemented (static JSON) |
| `GET` | `/health` | `backend/app/main.py` | Service health check | NO | Implemented (does not test DB connectivity) |
| `GET` | `/api/v1/tenders` | `backend/app/api/router.py` | List procurement tenders (supports pagination `page`, `page_size`) | NO | Contract stub (returns 1 mock tender) |
| `GET` | `/api/v1/tenders/{id}` | `backend/app/api/router.py` | Fetch single tender by UUID | NO | Contract stub (only matches hardcoded UUID `...0001`) |
| `GET` | `/api/v1/bidders` | `backend/app/api/router.py` | List bidders/vendors (supports pagination `page`, `page_size`) | NO | Contract stub (returns 1 mock bidder) |
| `GET` | `/api/v1/bidders/{id}` | `backend/app/api/router.py` | Fetch single bidder profile by UUID | NO | Contract stub (only matches hardcoded UUID `...0002`) |
| `POST` | `/api/v1/documents/upload` | `backend/app/api/router.py` | Upload vendor compliance document (`multipart/form-data`) | NO | Contract stub (validates extension, returns mock UUID `...0004`) |
| `POST` | `/api/v1/verification/start` | `backend/app/api/router.py` | Start statutory verification check against government provider | PARTIAL *(Reads `demo_government_records` if configured, but does NOT save job)* | Demo service stub (returns mock job UUID `...0003`) |
| `GET` | `/api/v1/verification/{id}` | `backend/app/api/router.py` | Retrieve verification job status and result | NO | Contract stub (only matches hardcoded UUID `...0003`) |
| `GET` | `/api/v1/dashboard/summary` | `backend/app/api/router.py` | High-level compliance dashboard metrics | NO | Contract stub (returns all zeros) |
| `GET` | `/api/v1/audit/{id}` | `backend/app/api/router.py` | Retrieve audit event record by UUID | NO | Contract stub (returns single dummy event) |

---

## 5. Supabase Schema

The database schema is defined in `supabase/migrations/20260911_create_core_domain_schema.sql` and `supabase/migrations/20260911_create_demo_government_data.sql`.

| Table | Important Columns | Relationships | Used By |
| :--- | :--- | :--- | :--- |
| `users` | `id` (UUID PK), `email` (VARCHAR UNIQUE), `full_name`, `role`, `is_active`, `created_at`, `updated_at` | 1:M with `tenders` (`created_by`), 1:M with `bidders` (`user_id`), 1:M with `audit_logs` (`user_id`) | User profiles, tender creators, audit actors |
| `tenders` | `id` (UUID PK), `title`, `reference_number` (VARCHAR UNIQUE), `description`, `status`, `created_by` (FK -> `users.id`), `created_at`, `updated_at` | M:1 with `users`, M:M with `bidders` via `tender_bidders` | Tenders Page, Tender Details Page, Dashboard |
| `bidders` | `id` (UUID PK), `user_id` (FK -> `users.id`), `legal_name`, `registration_number`, `gst_number`, `pan_number`, `status`, `created_at`, `updated_at` | M:1 with `users`, M:M with `tenders` via `tender_bidders`, 1:M with `documents`, 1:M with `verification_jobs` | Bidders Page, Bidder Details Page, Verification Page |
| `tender_bidders` | `tender_id` (UUID FK -> `tenders.id`), `bidder_id` (UUID FK -> `bidders.id`), `created_at` *(Composite PK: `tender_id, bidder_id`)* | Junction table between `tenders` and `bidders` | Tender-bidder associations, Tender Details, Bidder Details |
| `documents` | `id` (UUID PK), `bidder_id` (UUID FK -> `bidders.id`), `document_type`, `file_name`, `storage_path`, `mime_type`, `status`, `uploaded_at`, `created_at`, `updated_at` | M:1 with `bidders`, 1:M with `verification_jobs` | Documents Page, Bidder Details, OCR / AI pipeline |
| `verification_jobs` | `id` (UUID PK), `bidder_id` (UUID FK -> `bidders.id`), `document_id` (UUID FK -> `documents.id` NULLABLE), `verification_type`, `provider`, `status`, `started_at`, `completed_at`, `created_at` | M:1 with `bidders`, M:1 with `documents`, 1:M with `verification_results` | Verification Page, background job workers |
| `verification_results` | `id` (UUID PK), `verification_job_id` (UUID FK -> `verification_jobs.id`), `status`, `result` (JSONB), `confidence` (NUMERIC), `message`, `created_at` | M:1 with `verification_jobs` | Verification results inspection, Compliance / Risk scoring |
| `audit_logs` | `id` (UUID PK), `user_id` (UUID FK -> `users.id` NULLABLE), `action`, `entity_type`, `entity_id` (UUID), `details` (JSONB), `created_at` | M:1 with `users` | Audit Log Page, compliance traceability |
| `demo_government_records` | `id` (UUID PK), `provider` (VARCHAR), `identifier` (VARCHAR), `status`, `name`, `data` (JSONB), `created_at`, `updated_at` *(UNIQUE: `provider, identifier`)* | Read-only simulation reference table for integrations | Government verification adapters (PAN, GST, UDYAM, MCA, EPFO, ESIC, BLACKLIST) |

---

## 6. Missing Connections

### Frontend → Backend Missing Connections:
- **No HTTP Client:** Frontend lacks an API client (e.g., `fetch` wrapper or Axios instance) pointing to the backend URL.
- **No Environment Configuration Consumption:** `VITE_API_BASE_URL` is configured in `docker-compose.yml` but never read in the frontend codebase.
- **Zero API Invocations:** Every page imports synchronous data arrays and objects directly from `src/data/demoData.js` and `src/data/dashboardData.js`.
- **Missing Endpoints for Frontend Views:**
  - `GET /api/v1/documents` (list documents with bidder details) does not exist on the backend.
  - `GET /api/v1/audit` (list paginated audit logs) does not exist on the backend.
  - `GET /api/v1/tenders/{id}/bidders` or query filter `GET /api/v1/bidders?tender_id={id}` does not exist.

### Backend → Supabase Missing Connections:
- **Service Layer Detached from DB:** `TenderService`, `BidderService`, `DocumentService`, and `VerificationService` do not accept or use SQLAlchemy `Session`.
- **No DB Dependency in Route Handlers:** Routes in `backend/app/api/router.py` instantiate services without passing `db = Depends(get_db)`.
- **Health Check Doesn't Probe Database:** `GET /health` in `main.py` returns `{"status": "ok"}` unconditionally without checking `select_one()` from `repository.py`.
- **No Storage Integration:** `DocumentService.upload_document` does not write file binaries to Supabase Storage buckets or local filesystem.

### Frontend → API Service Missing Connections:
- No service layer directory (`frontend/src/api/` or `frontend/src/services/`).
- No React state management for loading spinners, error alerts, or retry flows on API failure (components assume immediate synchronous data availability).

---

## 7. Recommended Implementation Order

To safely transition SecondLook from static mocks to live Supabase-backed dynamic operations without regressions or architectural churn, follow this dependency order:

```
Step 01: Connect FastAPI ↔ Supabase (Verify session lifecycle, health check DB probe)
   │
   ▼
Step 02: Backend CRUD for Tenders (SQLAlchemy repository/service queries, seed sample tender)
   │
   ▼
Step 03: Connect Tenders Frontend to API (Create frontend API client, fetch live tenders in TendersPage)
   │
   ▼
Step 04: Backend CRUD for Bidders & Tender-Bidder relationships
   │
   ▼
Step 05: Connect Bidders Frontend to API (BiddersPage live listing)
   │
   ▼
Step 06: Dynamic Tender Details (Backend GET /tenders/{id} + associated bidders; frontend wiring)
   │
   ▼
Step 07: Dynamic Bidder Details (Backend GET /bidders/{id} + associated documents & tenders)
   │
   ▼
Step 08: Document Storage & Backend Documents Listing (Supabase Storage upload + GET /documents)
   │
   ▼
Step 09: Verification Job Persistence (Save verification job to DB, return real job ID)
   │
   ▼
Step 10: Verification Execution & Government Integrations (Connect pipeline to `demo_government_records`)
   │
   ▼
Step 11: Compliance & Risk Calculation Engine (Aggregate rules and persist `verification_results`)
   │
   ▼
Step 12: Dynamic Verification Page (Frontend triggers real job, polls status, renders DB results)
   │
   ▼
Step 13: Dynamic Dashboard (Backend summary queries against tenders, bidders, jobs, results)
   │
   ▼
Step 14: Tamper-Evident Audit Trail (Log all actions to `audit_logs` table, connect AuditPage)
   │
   ▼
Step 15: Officer Decision Workflow (Approve / Reject / Request Clarification endpoints)
   │
   ▼
Step 16: Error, Loading, and Empty State Polish
   │
   ▼
Step 17: End-to-End Testing & Verification
```

---

## 8. Files That Should NOT Be Modified During Initial Integration

To preserve core stability and avoid breaking established patterns:

1. **Database Schema Migrations:**
   - `supabase/migrations/20260911_create_core_domain_schema.sql`
   - `supabase/migrations/20260911_create_demo_government_data.sql`
   - `supabase/seed.sql`
   *(Do not alter schema or drop tables; use existing columns and relationships).*

2. **Core ORM & Domain Models:**
   - `backend/app/models/base.py`
   - `backend/app/models/tender.py`
   - `backend/app/models/bidder.py`
   - `backend/app/models/document.py`
   - `backend/app/models/verification_job.py`
   - `backend/app/models/verification_result.py`
   - `backend/app/models/audit_log.py`
   - `backend/app/models/user.py`
   *(These models already accurately reflect the database schema).*

3. **Government Integration Adapters:**
   - `backend/app/integrations/base.py`
   - `backend/app/integrations/registry.py`
   - Individual adapters: `pan.py`, `gst.py`, `udyam.py`, `mca.py`, `epfo.py`, `esic.py`, `blacklist.py`
   *(The adapter contract and registry pattern are already functional and tested).*

4. **Frontend Layout & Atomic UI Components:**
   - `frontend/src/components/layout/MainLayout.jsx`
   - `frontend/src/components/layout/Header.jsx`
   - `frontend/src/components/layout/Sidebar.jsx`
   - `frontend/src/components/layout/PageContainer.jsx`
   - `frontend/src/components/common/*` (`Badge.jsx`, `Button.jsx`, `EmptyState.jsx`, `Loading.jsx`, `Modal.jsx`)
   - `frontend/src/components/cards/*` (`StatCard.jsx`, `ComplianceCard.jsx`, `RiskCard.jsx`)
   - `frontend/src/styles/*` (CSS tokens and variables)
   *(Presentational components are clean, reusable, and design-compliant).*

5. **Static Demo Data Files (DO NOT DELETE YET):**
   - `frontend/src/data/demoData.js`
   - `frontend/src/data/dashboardData.js`
   *(Must be retained as fallback fixtures and test reference data until all live API connections are proven).*
