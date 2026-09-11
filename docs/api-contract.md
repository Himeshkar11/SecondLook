# SecondLook API Contract

This document is a placeholder for API contract discipline and future REST contract documentation.

The API contract is a shared boundary between frontend and backend. All changes to the API contract must require coordination between the frontend developer and backend developer before implementation.

## Shared boundary

```text
Frontend
      ↕
FastAPI Backend
```

The API contract includes, but is not limited to:

- Endpoint path
- HTTP method
- Request body
- Response body
- Field names
- Field types
- Status codes
- Error format
- Authentication requirements

These values must remain stable unless there is successful coordination and review. No actual application endpoints or production API implementations are created in this M02 milestone.

## Scope

This document is intentionally limited to foundational rules. It does not define endpoints, schemas, or service responses. Future milestones will define those details in a coordinated manner.
