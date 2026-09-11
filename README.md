# SecondLook

## Overview

SecondLook is a government and tender bid-compliance platform designed to support the evaluation of tenders and bidders against required documents, eligibility rules, government registrations, and statutory compliance obligations. The repository is being established as a clear foundation for a later full-stack application that will integrate frontend, backend, database, and external verification services in a governed manner.

## Current Status

The project is currently in the foundation/development stage. Feature implementation will be added progressively through milestone-based development.

## Technology Stack

Frontend:
React + Vite

Backend:
Python + FastAPI

Database:
Supabase PostgreSQL

Infrastructure:
Docker + Docker Compose

Testing:
Pytest + frontend testing

AI/OCR:
Mock interfaces initially

## High-Level Architecture

The intended architecture is shown below and represents the planned direction for the repository. Not every component is implemented in this milestone.

```text
                ┌──────────────┐
                │    User      │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   React UI   │
                └──────┬───────┘
                       │ REST
                       ▼
                ┌──────────────┐
                │   FastAPI    │
                │   Backend    │
                └──────┬───────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      PostgreSQL     Services    Integrations
      (Supabase)                    │
                                    ▼
                            External Systems
```

## Repository Structure

This repository is organized around four major responsibilities:

- `docs/` contains architecture, development, API, database, and contribution documentation.
- `backend/` contains the Python/FastAPI backend code and later service, integration, AI/OCR interface, and testing direction.
- `frontend/` contains the React/Vite frontend application.
- `supabase/` contains database configuration, migrations, and seed-related project files.

## Branch Strategy

The repository will use the following branch structure:

```text
main
│
└── development
     │
     ├── feature/*
     ├── fix/*
     └── milestone/*
```

Branch usage:

- `main`: stable code only and production-ready code.
- `development`: integration branch where feature work is merged before production.
- `feature/*`: used for new functionality such as `feature/tender-upload` or `feature/dashboard`.
- `fix/*`: used for bug fixes such as `fix/gst-validation`.
- `milestone/*`: used for work on major milestones such as `milestone/M01-foundation`.

## Development Rules

The following rules apply at foundation stage and will guide future repository work:

### Rule 1 — Do not modify another team's area without agreement

The repository will eventually be worked on by multiple developers. Ownership boundaries are respected.

### Rule 2 — Keep responsibilities separated

Frontend code belongs in `frontend/`.
Backend code belongs in `backend/`.
Database migrations/configuration belong in `supabase/`.
Documentation belongs in `docs/`.

### Rule 3 — No secrets in Git

Never commit `.env`, API keys, passwords, tokens, Supabase service-role keys, or private credentials. Only `.env.example` should be committed.

### Rule 4 — Do not bypass architectural layers

Future implementation should follow:

```text
Frontend
   ↓
API
   ↓
Service
   ↓
Repository / Database / Integration
```

Do not allow frontend code to directly access the database.

### Rule 5 — Use interfaces for external integrations

Future government integrations should be implemented behind clearly defined interfaces so that:

```text
Real Provider
Mock Provider
```

can be swapped without changing the rest of the application.

### Rule 6 — Mock first

During early development, mock implementations will be used for API, OCR, AI, and government integrations when real access is unavailable.

### Rule 7 — Do not hardcode credentials

All configuration must eventually come from environment variables.

### Rule 8 — Small commits

Use clear commit messages such as:

```text
chore: initialize repository
docs: add architecture documentation
chore: add docker configuration
docs: add development rules
```

## Architecture Principles

For this repository foundation, the intended architecture is:

```text
Frontend
   ↓
REST API
   ↓
FastAPI
   ↓
Service Layer
   ↓
Repository Layer
   ↓
Supabase PostgreSQL
```

For external systems:

```text
Service
   ↓
Integration Interface
   ↓
Real Provider / Mock Provider
```

For AI/OCR:

```text
Service
   ↓
AI/OCR Interface
   ↓
Mock Implementation
```

This design keeps the architecture replaceable and mock-capable for future real integrations.

## Team Ownership Principle

SecondLook will eventually be developed by a small team. Responsibilities should be clearly separated:

```text
Frontend team
    → frontend/

Backend team
    → backend/

Database
    → supabase/

Architecture/documentation
    → docs/
```

No authentication control mechanism is implemented in this milestone. This remains a repository organization rule.

## Scope Guardrail

M01 is a repository foundation only. This workspace contains no application feature implementation, no government integrations, no detailed database schema, and no AI/OCR provider functionality.

## Getting Started

1. Copy `.env.example` to `.env` for local environment variables.
2. Review the project documentation in `docs/`.
3. Use Docker Compose for the frontend and backend services when images are prepared.

## License

This foundation repository has been prepared for milestone-based software development. License details should be added when the project begins formal delivery.
