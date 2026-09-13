-- Migration: Add Government Verification table and document verification lifecycle status (Task 10)

CREATE TABLE IF NOT EXISTS government_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    bidder_id UUID REFERENCES bidders(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL, -- 'GST' or 'PAN'
    provider VARCHAR(50) NOT NULL, -- 'demo' or specific adapter token
    identifier VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    verification_result VARCHAR(50), -- VERIFIED, MISMATCH, NOT_FOUND, SOURCE_ERROR
    government_data JSONB,
    field_results JSONB,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'VERIFICATION_PENDING';

CREATE INDEX IF NOT EXISTS idx_government_verifications_doc ON government_verifications(document_id);
CREATE INDEX IF NOT EXISTS idx_government_verifications_bidder ON government_verifications(bidder_id);
CREATE INDEX IF NOT EXISTS idx_government_verifications_status ON government_verifications(status);
CREATE INDEX IF NOT EXISTS idx_documents_verification_status ON documents(verification_status);
