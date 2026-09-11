# SecondLook Contribution Guide

This document is the contributor workflow guide for the SecondLook repository. It establishes the ownership and coordination expectations for developers and AI coding agents working on the repository foundation and future milestones.

## Before starting work

A developer should:

1. Pull the latest changes.
2. Read the relevant documentation.
3. Identify the module owner.
4. Confirm the task belongs to the current milestone.
5. Inspect the existing code before creating new files.

## While working

A developer should:

- stay within their ownership area
- make small changes
- avoid unrelated refactoring
- write/update tests where appropriate
- keep API contracts stable
- keep secrets out of Git

## Before committing

Check:

```text
[ ] Only relevant files changed
[ ] No secrets
[ ] No accidental architecture changes
[ ] No API contract changes without agreement
[ ] Tests pass where applicable
[ ] Documentation updated if required
```

## Before merging

Check:

```text
[ ] Code reviewed
[ ] Ownership respected
[ ] Cross-module changes communicated
[ ] No milestone scope creep
```

## Ownership reminder

- Frontend development belongs in `frontend/`.
- Backend development belongs in `backend/app/` for future implementation.
- Database changes belong in `supabase/`.
- Documentation belongs in `docs/`.

This M02 contribution guide remains documentation-only and does not introduce feature implementation, database schema, or route definitions.
