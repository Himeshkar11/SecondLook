-- Migration: Add multi-source verification support columns (Task 14)

ALTER TABLE government_verifications
    ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE government_verifications
    ADD COLUMN IF NOT EXISTS retrieved_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_government_verifications_is_demo ON government_verifications(is_demo);

