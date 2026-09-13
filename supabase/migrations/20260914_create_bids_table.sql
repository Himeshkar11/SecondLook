-- Migration: 20260914_create_bids_table.sql
-- Description: Create bids table representing bidder submission workspaces for tenders, and link documents to bids (Milestone 08).

-- 1. Create bids table
CREATE TABLE IF NOT EXISTS bids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bidder_id UUID NOT NULL,
    tender_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_bids_bidder
        FOREIGN KEY (bidder_id) REFERENCES bidders(id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_bids_tender
        FOREIGN KEY (tender_id) REFERENCES tenders(id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT uq_bids_bidder_tender
        UNIQUE (bidder_id, tender_id)
);

CREATE INDEX IF NOT EXISTS idx_bids_bidder_id ON bids(bidder_id);
CREATE INDEX IF NOT EXISTS idx_bids_tender_id ON bids(tender_id);
CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status);

-- 2. Add bid_id to documents table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'bid_id'
    ) THEN
        ALTER TABLE documents
            ADD COLUMN bid_id UUID REFERENCES bids(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_documents_bid_id ON documents(bid_id);
    END IF;
END $$;
