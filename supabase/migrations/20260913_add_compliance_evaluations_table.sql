-- Migration: Add Compliance Evaluations and Evaluation History (Task 13)

CREATE TABLE IF NOT EXISTS compliance_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    summary JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add evaluation_id to requirement_evaluations to link each requirement evaluation to a run
ALTER TABLE public.requirement_evaluations 
ADD COLUMN IF NOT EXISTS evaluation_id UUID REFERENCES compliance_evaluations(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_compliance_evaluations_tender ON compliance_evaluations(tender_id);
CREATE INDEX IF NOT EXISTS idx_compliance_evaluations_bidder ON compliance_evaluations(bidder_id);
CREATE INDEX IF NOT EXISTS idx_compliance_evaluations_status ON compliance_evaluations(status);
CREATE INDEX IF NOT EXISTS idx_requirement_evaluations_evaluation ON requirement_evaluations(evaluation_id);
