# SecondLook Architecture

This document records the intended architecture and ownership boundaries for the SecondLook repository foundation.

## Current architecture direction

```text
REST Route
    ↓
Service
    ↓
Repository
    ↓
Database
```

The architecture is intentionally layered. Routes are responsible only for HTTP concerns, services coordinate domain operations, repositories own database access, and the database layer owns persistence.

## Responsibility map

### API / Route

Responsible for:

- HTTP
- request parsing
- response formatting
- HTTP status codes
- dependency injection

Routes must not contain business logic or direct database queries.

### Service

Responsible for:

- domain operations
- business rules
- orchestration

M10 services provide deterministic demo behavior suitable for the contract boundary. They may be replaced by repository-backed services later without changing the public API contract.

### Repository

Responsible for:

- database access
- persistence
- queries

### Database

Responsible for:

- persistent data
- constraints
- relationships

## Ownership diagram

```text
┌──────────────────────┐
│      Frontend        │
│     frontend/        │
│ Frontend Developer   │
└──────────┬───────────┘
           │
           │ REST API
           ▼
┌──────────────────────┐
│       Backend        │
│    backend/app/      │
│  Backend Developer   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     Repository       │
│    Data Access       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       Supabase       │
│      supabase/       │
│   Database Owner     │
└──────────────────────┘
```

## Ownership boundaries

- Frontend developer owns the UI and frontend deliverables in `frontend/`.
- Backend developer owns API routes, services, and future business orchestration under `backend/app/`.
- Database owner owns migration and schema configuration under `supabase/`.
- The repository and data access boundary exists between the service layer and the Supabase PostgreSQL database.

The service ownership boundary for this milestone is:

```text
backend/app/api/      → API developers
backend/app/services/ → Backend/service developers
backend/app/database/ → Database/repository developers
backend/app/models/    → Database/domain model ownership
```

Front-end code must not directly access `Supabase PostgreSQL`. The correct data direction is:

```text
React
  ↓
FastAPI REST API
  ↓
Database
```

## Backend future responsibilities

The future backend is responsible for:

- AI/OCR interfaces
- Government integrations
- Verification pipeline
- Service orchestration

These areas are documented as future responsibilities and are not implemented in this milestone. They must remain behind interfaces and mock-first providers as required by the project architecture.

## Integration abstraction

External systems are reached through service and integration interfaces:

```text
Service
   ↓
IntegrationRegistry
   ↓
GovernmentIntegration.verify(request)
   ↓
Demo Provider / Future Provider
```

This keeps government and data-provider work separated from the core application flow. In this milestone, the registry points to provider demo classes that implement the same shared interface and never reach outside the application boundary. The M11 registry and contract stay intentionally provider-agnostic and documentation-backed, while the service route remains a public demo contract.

```text
REST Route
    ↓
VerificationService
    ↓
IntegrationRegistry
    ↓
PAN / GST / Udyam / MCA / EPFO / ESIC / Startup India / NSIC / DigiLocker / Blacklist / OEM
```

The known M11 providers remain demonstration-only: they return contract objects and follow the shared integration status vocabulary without performing real verification tasks.

## Document Processing and AI Extraction Interfaces (M13 & M14)

Document OCR processing and AI extraction are isolated behind provider-neutral interfaces:

```text
DocumentInput
    ↓
OCRProcessor.process() (backend/app/ocr/)
    ↓
ExtractedText
    ↓
AIExtractor.extract() (backend/app/ai/)
    ↓
StructuredDocumentData
```

- **OCR Interface (`backend/app/ocr/`)**: Defines the `OCRProcessor` contract returning `ExtractedText`. The `DemoOCRProcessor` provides deterministic demo text without requiring external OCR engines or network calls.
- **AI Extraction Interface (`backend/app/ai/`)**: Defines the `AIExtractor` contract consuming `ExtractedText` and returning `StructuredDocumentData`. The `DemoAIExtractor` parses compliance fields deterministically. Provider-agnostic prompt templates are maintained in `backend/app/ai/prompts.py`.
- **Isolation Rules**: The OCR layer has no dependency on AI. The AI layer consumes only the `ExtractedText` contract and has no dependency on concrete OCR implementations. Neither layer interacts directly with the database, Supabase, or external networks.

## Verification Pipeline Skeleton (M15)

Milestone 15 establishes the central verification pipeline skeleton (`backend/app/verification/`), coordinating the end-to-end verification workflow via constructor dependency injection.

```text
DocumentInput
    ↓
1. OCRProcessor.process() (backend/app/ocr/)
    ↓ ExtractedText
2. AIExtractor.extract() (backend/app/ai/)
    ↓ StructuredDocumentData
3. GovernmentIntegration.verify() (backend/app/integrations/)
    ↓ IntegrationResponse
4. RulesEngine.evaluate() (backend/app/verification/rules.py)
    ↓ List[RuleEvaluationResult]
5. ScoringEngine.calculate() (backend/app/verification/scoring.py)
    ↓ ScoreResult
6. RiskEngine.assess() (backend/app/verification/risk.py)
    ↓ RiskResult
7. VerificationPipelineResult (backend/app/verification/pipeline.py)
```

- **Pipeline Orchestrator (`VerificationPipeline`)**: Coordinates the sequential execution of OCR, AI extraction, statutory government verification, rules evaluation, scoring, and risk classification. It does not implement OCR/AI logic, database queries, scoring formulas, or risk algorithms directly.
- **Rules Engine (`RulesEngine`)**: Evaluates a list of modular compliance rules against structured document data and government integration responses, returning `RuleEvaluationResult` objects.
- **Scoring Engine (`ScoringEngine`)**: Computes normalized score results (`ScoreResult`) from rule evaluation outcomes.
- **Risk Engine (`RiskEngine`)**: Categorizes risk levels (`LOW`, `MEDIUM`, `HIGH`) based on compliance scores and critical check failures.
- **Demo / Skeleton Status**: M15 is an in-memory orchestration skeleton. It does not write to the database, alter API contracts, or claim production legal compliance scoring.
- **Future Replacement Seam**: The pipeline depends solely on abstract interfaces (`OCRProcessor`, `AIExtractor`, `GovernmentIntegration`, `RulesEngine`, `ScoringEngine`, `RiskEngine`), allowing production providers to replace demo implementations without changing the orchestration logic.

## Async Worker and Job System Skeleton (M16)

Milestone 16 establishes the asynchronous worker and job orchestration skeleton (`backend/app/workers/`), decoupling the request handling boundary from long-running document verification pipelines.

```text
POST /verification/start
        ↓
Enqueue VerificationJobRecord (JobStatus.QUEUED)
        ↓
Worker.process_next_job()
        ↓
Transition to JobStatus.PROCESSING
        ↓
VerificationPipeline.run() (OCR → AI → Integrations → Rules → Score → Risk)
        ↓
Transition to JobStatus.COMPLETED or JobStatus.FAILED
        ↓
Attach VerificationPipelineResult or error diagnostic
```

- **Job Status Lifecycle**: Strictly enforces valid transitions:
  - `QUEUED` → `PROCESSING` → `COMPLETED`
  - `QUEUED` → `PROCESSING` → `FAILED`
  Direct or out-of-order jumps raise `InvalidStateTransitionError`.
- **Worker Execution Harness (`Worker`)**: Retrieves queued jobs and invokes the injected `VerificationPipeline`. The worker contains no OCR, AI, rules, scoring, risk thresholds, SQL, or HTTP network logic.
- **In-Memory Job Queue (`JobQueue`)**: Provides deterministic FIFO job management for development and testing.
- **Deferred Queue Infrastructure**: M16 is an architectural skeleton. Distributed queue technologies (Celery, Redis, RabbitMQ, SQS) and production database queue persistence are intentionally deferred.

## Frontend Architecture & Demo Dashboard (M17, M18, M19)

Milestones 17, 18, and 19 establish the frontend foundation (`frontend/src/`) using a minimal Indian government and enterprise portal aesthetic.

```text
React Router (App.jsx)
    ↓
MainLayout (Header + Sidebar + PageContainer)
    ↓
Pages (DashboardPage / PlaceholderPage)
    ↓
Components (StatCard / ComplianceCard / RiskCard / Common UI)
    ↓
Isolated Demo Data (frontend/src/data/dashboardData.js)
```

- **Design System (M17)**: Centralized design tokens (`styles/tokens.css`) specifying accessible typography, a 4px grid spacing system, compact border radii, and a restrained color palette subtly inspired by the Indian National Flag (`#1E4E8C` blue, `#138808` green, `#FF9933`/`#D97706` saffron, neutral surfaces). Common reusable components include `Button`, `Badge`, `Modal`, `Loading`, and `EmptyState`.
- **Application Layout (M18)**: Structured `MainLayout` providing a sticky government-styled `Header` with national accent bar and auditor status chip, a responsive navigation `Sidebar` mapping all defined routes (`/dashboard`, `/tenders`, `/bidders`, `/documents`, `/verification`, `/audit`, `/settings`), and a standardized `PageContainer`.
- **Complete Demo Dashboard (M19)**: An information-dense compliance dashboard rendering key metrics (`Active Tenders: 24`, `Verification Pending: 08`, `Compliant Bidders: 71`), a Recent Tenders compliance review table, a statutory `ComplianceCard` (82% overall rate), and a `RiskCard` (LOW risk).
- **Data Isolation & Future Replacement**: All dashboard values are decoupled in `frontend/src/data/dashboardData.js` and passed via props, making future integration with the backend REST API (`GET /api/v1/dashboard/summary`) straightforward without modifying presentation components.




