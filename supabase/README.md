# Supabase PostgreSQL Infrastructure

SecondLook Backend
     ↓
Database Layer
     ↓
SQLAlchemy
     ↓
PostgreSQL Driver
     ↓
Supabase PostgreSQL

This repository uses Supabase PostgreSQL as the long-term platform for backend data storage. Docker remains responsible only for the frontend and backend services; Docker does not host PostgreSQL. Database credentials come from environment variables and are supplied to the backend configuration layer through the central settings object.

The backend database layer is expected to use the central settings module and the configured `DATABASE_URL` value. The backend must not embed credentials in source, logs, tests, Dockerfiles, or documentation. Future schema changes must follow the migration contract:

Requirement
    ↓
Schema design
    ↓
Migration
    ↓
Test
    ↓
Review
    ↓
Merge

The frontend must not connect directly to PostgreSQL. Application access to data must continue to flow through the backend database layer. This milestone intentionally creates only the migration directory and the empty `seed.sql` placeholder. No application schema or business tables are introduced here.
