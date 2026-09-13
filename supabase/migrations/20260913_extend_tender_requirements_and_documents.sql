-- Migration: 20260913_extend_tender_requirements_and_documents.sql
-- Description: Extend documents to support tender association and extend tender_requirements with full lifecycle, AI extraction, and approval metadata (Task 12).

-- 1. Extend documents table for tender document association
ALTER TABLE documents
    ALTER COLUMN bidder_id DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'tender_id'
    ) THEN
        ALTER TABLE documents
            ADD COLUMN tender_id UUID REFERENCES tenders(id) ON DELETE CASCADE;
        CREATE INDEX IF NOT EXISTS idx_documents_tender_id ON documents(tender_id);
    END IF;
END $$;

-- 2. Extend tender_requirements table with lifecycle and source traceability
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tender_requirements' AND column_name = 'status'
    ) THEN
        ALTER TABLE tender_requirements
            ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'APPROVED',
            ADD COLUMN rule_type VARCHAR(50) NULL,
            ADD COLUMN parameters JSONB NULL,
            ADD COLUMN source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
            ADD COLUMN source_text TEXT NULL,
            ADD COLUMN source_page INTEGER NULL,
            ADD COLUMN source_section VARCHAR(255) NULL,
            ADD COLUMN created_by UUID REFERENCES users(id) ON DELETE SET NULL,
            ADD COLUMN approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
            ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ADD COLUMN approved_at TIMESTAMPTZ NULL;

        CREATE INDEX IF NOT EXISTS idx_tender_requirements_status ON tender_requirements(status);
        CREATE INDEX IF NOT EXISTS idx_tender_requirements_source_doc ON tender_requirements(source_document_id);
    END IF;
END $$;
