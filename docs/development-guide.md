# SecondLook Development Guide

This document is the central development rulebook for SecondLook. It establishes how the repository should be developed by a small team and by AI-assisted coding agents while keeping the existing architecture stable.

## 3.1 Development Philosophy

SecondLook uses milestone-based development, small isolated changes, clear module ownership, interface-first architecture, mock-first development for external services, code review before merging, and minimal architectural changes.

Developers should prefer modifying existing modules rather than creating new architectural structures. When a change is small, local, and clearly within the ownership of one team area, it should remain in that area. When a change crosses a shared boundary, it must be discussed and coordinated.

SecondLook architecture is intentionally layered:

```text
User
  ↓
React Frontend
  ↓
FastAPI REST API
  ↓
Service Layer
  ↓
Repository / Data Access
  ↓
Supabase PostgreSQL
```

External integrations will use abstraction and interface seams:

```text
Service
   ↓
Integration Interface
   ↓
Real Provider / Mock Provider
```

The repository must evolve through milestones, not through unplanned feature jumps.

## Ownership Structure

| Area | Primary Owner | Location |
|------|---------------|----------|
| Frontend | Frontend Developer | `frontend/` |
| Backend | Backend Developer | `backend/app/` |
| Database | Database Owner | `supabase/` |
| Backend Testing | Tester | `backend/tests/` |
| Frontend Testing | Tester / Frontend Developer | `frontend/` test structure |
| Documentation | All developers | `docs/` |
| Infrastructure | Team / Lead | root Docker files |

### Responsibilities

- Frontend Developer owns the user-facing React + Vite experience and future frontend structure under `frontend/`.
- Backend Developer owns the FastAPI application and service/repository responsibilities under `backend/app/` when that area is introduced in a later milestone.
- Database Owner owns the Supabase/PostgreSQL configuration, migration workflow, seeds, indexes, constraints, and data-shape documentation under `supabase/`.
- Tester owns backend test ownership under `backend/tests/` and contributes to frontend behavior validation inside the frontend test structure where that structure later exists.
- All developers contribute to documentation in `docs/`.
- Team or lead owns start-up and infrastructure configuration in the root Docker and Compose files.

## Frontend Ownership

The `frontend/` directory is the primary working area for the frontend developer.

Future frontend responsibilities include:

- React components
- pages
- UI
- frontend routing
- frontend state
- frontend API client
- frontend hooks
- frontend styling
- frontend tests

The frontend developer communicates with the backend through REST APIs and must not directly access the Supabase PostgreSQL database.

Correct architecture:

```text
React
  ↓
FastAPI REST API
  ↓
Database
```

Incorrect architecture:

```text
React
  ↓
Supabase database
```

## Backend Ownership

The `backend/app/` directory is the primary backend developer working area in future steps. That ownership is documented here as the intended milestone direction.

Future backend responsibilities include:

- FastAPI application
- API routes
- request/response schemas
- service layer
- business logic
- repository/data-access layer
- integrations
- verification pipeline
- AI/OCR interfaces

Database schema and migration ownership remains under `supabase/`.

## Database Ownership

The `supabase/` directory is the database ownership area.

Future responsibilities include:

- database migrations
- schema definitions
- seed data
- database documentation
- indexes
- constraints
- database-level configuration

Backend developers should not casually modify database schemas. Any database changes should pass through an agreed process:

```text
Requirement
    ↓
Database change proposed
    ↓
Team agreement
    ↓
Migration created
    ↓
Tested
    ↓
Merged
```

No actual database migrations or schema implementation should be added in this milestone.

## Testing Ownership

Backend testing belongs in `backend/tests/` when it is introduced in a future milestone. Frontend tests remain in the frontend project test structure.

Testing responsibilities include:

- unit tests
- integration tests
- regression testing
- API testing
- frontend behavior testing
- validation of milestone acceptance criteria

Tests should be updated whenever relevant functionality changes. This milestone only documents ownership; it does not install or configure a complete testing framework.

## Documentation Ownership

The `docs/` directory is shared documentation owned by all developers.

Developers may update documentation relevant to their work.

### Architecture changes

Changes to `docs/architecture.md` require agreement before changing the established architecture.

### API changes

Changes to `docs/api-contract.md` must be coordinated with both frontend and backend developers.

## 🚫 DO NOT

The following rules must be treated as architecture boundaries and discipline constraints.

### DO NOT randomly create architecture folders

Developers must not create things like:

```text
backend/new_architecture/
backend/core2/
backend/utils2/
frontend/new-system/
services2/
api_new/
```

without architectural agreement. If an existing module can handle the responsibility, modify it instead of creating another architectural layer.

### DO NOT modify another developer's module without agreement

Example:

- Frontend developer should not randomly modify `backend/app/`.
- Backend developer should not randomly modify `frontend/`.
- Database changes should not be made casually inside `backend/` unless required and agreed upon.

### DO NOT change API contracts without agreement

The API contract is a shared boundary between:

```text
Frontend
      ↕
FastAPI Backend
```

A backend developer must not silently change:

- request format
- response format
- endpoint names
- field names
- status codes
- authentication expectations

without coordinating with the frontend developer.

### DO NOT commit `.env`

Never commit:

```text
.env
```

Never commit:

- API keys
- passwords
- access tokens
- Supabase service-role keys
- private credentials

Only:

```text
.env.example
```

belongs in Git.

### DO NOT put business logic in React

React should handle:

```text
UI
State
User interaction
API communication
Presentation
```

Business rules should belong in the backend.

Incorrect:

```text
React
  ↓
Complex compliance calculation
```

Correct:

```text
React
  ↓
FastAPI
  ↓
Service / Business Logic
```

### DO NOT put database logic inside API routes

Avoid:

```python
@app.get("/bidder")
def bidder():
    # SQL/database operations directly here
```

Instead use:

```text
API Route
    ↓
Service
    ↓
Repository
    ↓
Database
```

API routes should remain thin.

## AI/Vibe-Coding Rules

Because SecondLook will use AI coding tools, AI-generated code must follow repository architecture and not redefine it.

AI agents must:

1. Inspect the existing repository before creating files.
2. Understand the architecture before modifying code.
3. Reuse existing modules where possible.
4. Avoid creating duplicate abstractions.
5. Never introduce a new architectural layer without approval.
6. Follow existing naming conventions.
7. Follow the ownership boundaries.
8. Avoid modifying unrelated files.
9. Explain architectural changes before making them.
10. Never commit secrets.
11. Never silently change API contracts.
12. Never silently change database schemas.
13. Run relevant tests after modifications.
14. Keep changes focused on the requested milestone.

Add this principle:

> AI-generated code follows the repository architecture; it does not redefine the architecture.

## Milestone Rules

The development workflow is:

```text
Milestone
   ↓
Define scope
   ↓
Implement only milestone requirements
   ↓
Test
   ↓
Audit
   ↓
Review
   ↓
Commit
   ↓
Next milestone
```

Developers must not jump ahead. If working on M02, they must not implement M05 functionality, government integrations, AI verification, or production database schemas.

## Git Workflow

The recommended workflow is:

```text
development
     ↓
feature/<name>
     ↓
implement
     ↓
test
     ↓
review
     ↓
merge into development
     ↓
stable milestone
     ↓
main
```

Examples:

```text
feature/backend-foundation
feature/tender-upload
feature/bidder-verification
fix/api-validation
milestone/M02-development-rules
```

Use clear commit messages such as:

```text
feat: add bidder verification service
fix: correct GST validation
docs: update API contract
test: add bidder service tests
chore: update Docker configuration
```

## Change Classification

Developers should classify changes before making them.

### Small change

Examples:

- bug fix
- UI adjustment
- test update
- documentation update

Can normally be handled within the developer's owned area.

### Cross-module change

Examples:

- Frontend + Backend
- Backend + Database
- Backend + Integration

Requires communication with the relevant owner.

### Architectural change

Examples:

- adding a new major layer
- replacing FastAPI
- replacing React
- changing database technology
- changing API architecture
- changing repository structure

Requires explicit team agreement.

This milestone documents ownership and workflow boundaries only. It does not implement APIs, UI, integrations, or database systems.
