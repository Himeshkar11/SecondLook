"""Service-layer package for M10 demo service boundary.

Services are intentionally independent from FastAPI HTTP objects and
return deterministic demonstration payloads that can later be replaced by
repository-backed implementations without changing the API route contract.
"""
