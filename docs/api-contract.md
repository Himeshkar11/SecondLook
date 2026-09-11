# SecondLook API Contract

This document is the shared frontend/backend API contract for SecondLook. It is the authoritative contract boundary for the API. Any future API change must:

1. Update this contract.
2. Get agreement from the relevant developers.
3. Update backend implementation.
4. Update frontend usage.
5. Update tests.

No developer should silently change an endpoint's request or response structure.

## Frontend/backend boundary

```text
React Frontend
      ↓
REST API
      ↓
FastAPI Router
      ↓
Service Layer
      ↓
Repository / Data Access
      ↓
Supabase PostgreSQL
```

Frontend responsibilities:

- The frontend is a React application and must communicate with the backend only through the REST API contract.
- Frontend code must not directly access Supabase PostgreSQL, contain database credentials, implement backend business logic, or call government APIs directly.

Backend responsibilities:

- The backend follows Router → Service → Repository → Database.
- Routers must not contain database queries.
- Business logic, services, repositories, and integrations remain outside this M09 placeholder scope.

## API versioning and routing

All application endpoints must be shelfed under the versioned prefix:

```text
/api/v1
```

Do not create unversioned application endpoints such as `/tenders`, `/bidders`, `/documents`, or `/verification`.

The existing `/` and `/health` endpoints remain unchanged.

## Endpoint table

| Method | Endpoint                   | Purpose            | Request      | Response                   |
| ------ | -------------------------- | ------------------ | ------------ | -------------------------- |
| GET    | /api/v1/tenders            | List tenders       | Query params | Paginated tenders          |
| GET    | /api/v1/tenders/{id}       | Get tender         | UUID         | Tender                     |
| GET    | /api/v1/bidders            | List bidders       | Query params | Paginated bidders          |
| GET    | /api/v1/bidders/{id}       | Get bidder         | UUID         | Bidder                     |
| POST   | /api/v1/documents/upload   | Upload document    | Multipart    | Document metadata          |
| POST   | /api/v1/verification/start | Start verification | JSON         | Verification job           |
| GET    | /api/v1/verification/{id}  | Get verification   | UUID         | Verification status/result |
| GET    | /api/v1/dashboard/summary  | Dashboard summary  | None         | Summary object             |
| GET    | /api/v1/audit/{id}         | Get audit          | UUID         | Audit information          |

## Resource contracts

The following example resource shapes are normative for the M09 contract layer. They intentionally mirror existing M08 models and avoid duplicating unnecessary business specifics.

### Tender example

```json
{
  "id": "uuid",
  "title": "string",
  "reference_number": "string",
  "description": "string",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Bidder example

```json
{
  "id": "uuid",
  "legal_name": "string",
  "registration_number": "string",
  "gst_number": "string|null",
  "pan_number": "string|null",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Document metadata example

```json
{
  "id": "uuid",
  "bidder_id": "uuid",
  "document_type": "string",
  "file_name": "string",
  "mime_type": "string",
  "status": "string",
  "uploaded_at": "datetime"
}
```

The upload request for `POST /api/v1/documents/upload` is a `multipart/form-data` request. The object returned by the endpoint after upload is document metadata only. No storage credentials or provider secrets are exposed.

### Verification job example

```json
{
  "id": "uuid",
  "bidder_id": "uuid",
  "document_id": "uuid|null",
  "verification_type": "string",
  "provider": "string",
  "status": "string",
  "started_at": "datetime|null",
  "completed_at": "datetime|null",
  "created_at": "datetime"
}
```

### Verification result example

```json
{
  "id": "uuid",
  "bidder_id": "uuid",
  "document_id": "uuid|null",
  "verification_type": "string",
  "provider": "string",
  "status": "string",
  "started_at": "datetime|null",
  "completed_at": "datetime|null",
  "created_at": "datetime",
  "result": {
    "overall_status": "passed|failed|pending",
    "checks": []
  }
}
```

Provider-specific implementation details remain outside the public contract where practical. The public contract treats verification results as a normalized status object and a list of simple check records rather than exposing provider internals.

## Pagination contract

The list endpoints `GET /api/v1/tenders` and `GET /api/v1/bidders` define a consistent pagination structure:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

The contract documents the initial list query parameters:

```text
page
page_size
```

Expected behavior:

- `page` is the one-based page index.
- `page_size` is the requested item count per page.
- These are contract placeholders only. No pagination business logic is implemented in M09.

## Query parameter contract

The initial contract is intentionally simple and preserves the M08 domain fields already present in the existing schemas and models:

```text
page
page_size
```

Filtering fields should remain minimal and should correspond to existing domain fields already modeled in the repository. No complex filtering or search system is introduced by this milestone.

## Error contract

All API errors follow the same structure:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Tender not found",
    "details": {}
  }
}
```

Standard error categories:

```text
VALIDATION_ERROR
RESOURCE_NOT_FOUND
CONFLICT
UNAUTHORIZED
FORBIDDEN
INTERNAL_ERROR
```

Authentication/authorization errors remain part of the M09 contract definition only and are not implemented by the backend.

## HTTP status codes

Expected success and error codes:

```text
200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
500 Internal Server Error
```

For each endpoint, the contract defines whether the endpoint is expected to return success or the listed error states. Placeholder route declarations must document response metadata in the OpenAPI schema.

## UUID behavior

All resource identifiers in this contract are UUIDs, matching the M08 model shape:

```text
/api/v1/tenders/{uuid}
/api/v1/bidders/{uuid}
/api/v1/verification/{uuid}
/api/v1/audit/{uuid}
```

No integer resource IDs are allowed in the public contract.

## OpenAPI behavior

FastAPI must expose the contract through `/docs` and `/openapi.json`. The `/api/v1` router will be included in the main FastAPI application via the application entry point. The endpoint declarations are minimal placeholder route declarations used for OpenAPI generation only. They are explicitly marked as contract placeholders and must not implement database access, CRUD, authentication, file storage, verification, external services, or AI/OCR.

## Status codes table

| Endpoint | Minimum expected success/error behavior |
|---------|-----------------------------------------|
| GET /api/v1/tenders | 200 OK; 400; 401; 403; 404; 500 |
| GET /api/v1/tenders/{id} | 200 OK; 404; 500 |
| GET /api/v1/bidders | 200 OK; 400; 401; 403; 404; 500 |
| GET /api/v1/bidders/{id} | 200 OK; 404; 500 |
| POST /api/v1/documents/upload | 201 Created; 400; 401; 403; 422; 500 |
| POST /api/v1/verification/start | 201 Created; 400; 401; 403; 422; 500 |
| GET /api/v1/verification/{id} | 200 OK; 404; 500 |
| GET /api/v1/dashboard/summary | 200 OK; 500 |
| GET /api/v1/audit/{id} | 200 OK; 404; 500 |

## Scope restrictions

This milestone is contract-only. The following remain out of scope and must not be implemented in the API layer:

```text
Authentication implementation
Authorization implementation
CRUD implementation
Service implementation
Repository implementation
Database queries
File storage
Supabase Storage
AI
OCR
Government APIs
GST integration
PAN integration
Udyam integration
MCA integration
EPFO integration
ESIC integration
Blacklist integration
Background workers
Celery
Redis
```

## Placeholder route declarations

The following placeholder routes exist for OpenAPI generation in this contract milestone:

```text
GET /api/v1/tenders
GET /api/v1/tenders/{id}
GET /api/v1/bidders
GET /api/v1/bidders/{id}
POST /api/v1/documents/upload
POST /api/v1/verification/start
GET /api/v1/verification/{id}
GET /api/v1/dashboard/summary
GET /api/v1/audit/{id}
```

They contain no business logic and return minimal contract-shaped payloads.

## Contract ownership

The API contract may be changed only through this agreement sequence:

1. Update the contract.
2. Get agreement from relevant developers.
3. Update backend implementation.
4. Update frontend usage.
5. Update tests.

No frontend or backend developer should silently change an endpoint's request or response structure.