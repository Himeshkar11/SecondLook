-- M12: demo government verification source-of-truth table
-- PostgreSQL/Supabase migration

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS demo_government_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(80) NOT NULL,
    identifier VARCHAR(255) NOT NULL,
    status VARCHAR(80) NOT NULL,
    name VARCHAR(255) NULL,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT demo_government_records_provider_identifier_unique UNIQUE (provider, identifier)
);

CREATE INDEX IF NOT EXISTS idx_demo_government_records_provider
    ON demo_government_records(provider);

CREATE INDEX IF NOT EXISTS idx_demo_government_records_identifier
    ON demo_government_records(identifier);

CREATE INDEX IF NOT EXISTS idx_demo_government_records_provider_identifier
    ON demo_government_records(provider, identifier);
