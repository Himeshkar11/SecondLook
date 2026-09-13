-- Migration: Add Tender Requirements and Requirement Evaluations (Task 11)

CREATE TABLE IF NOT EXISTS tender_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL DEFAULT 'GST',
    mandatory BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 1,
    rule_config JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS requirement_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES tender_requirements(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'NOT_VERIFIED', -- PASS, FAIL, PARTIAL, NOT_VERIFIED, NOT_APPLICABLE
    result JSONB,
    rule_results JSONB,
    evidence JSONB,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tender_requirements_tender ON tender_requirements(tender_id);
CREATE INDEX IF NOT EXISTS idx_tender_requirements_code ON tender_requirements(code);
CREATE INDEX IF NOT EXISTS idx_requirement_evaluations_req ON requirement_evaluations(requirement_id);
CREATE INDEX IF NOT EXISTS idx_requirement_evaluations_bidder ON requirement_evaluations(bidder_id);
CREATE INDEX IF NOT EXISTS idx_requirement_evaluations_tender ON requirement_evaluations(tender_id);
