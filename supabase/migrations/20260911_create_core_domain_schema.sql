-- M08: initial core domain schema for SecondLook
-- PostgreSQL/Supabase migration

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'admin',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    reference_number VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_tenders_created_by
        FOREIGN KEY (created_by) REFERENCES users(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS bidders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    legal_name TEXT NOT NULL,
    registration_number VARCHAR(255),
    gst_number VARCHAR(255),
    pan_number VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_bidders_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tender_bidders (
    tender_id UUID NOT NULL,
    bidder_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tender_id, bidder_id),
    CONSTRAINT fk_tender_bidders_tender
        FOREIGN KEY (tender_id) REFERENCES tenders(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT,
    CONSTRAINT fk_tender_bidders_bidder
        FOREIGN KEY (bidder_id) REFERENCES bidders(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bidder_id UUID NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    storage_path TEXT,
    mime_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    uploaded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_documents_bidder
        FOREIGN KEY (bidder_id) REFERENCES bidders(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS verification_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bidder_id UUID NOT NULL,
    document_id UUID,
    verification_type VARCHAR(100) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_verification_jobs_bidder
        FOREIGN KEY (bidder_id) REFERENCES bidders(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT,
    CONSTRAINT fk_verification_jobs_document
        FOREIGN KEY (document_id) REFERENCES documents(id)
        ON UPDATE NO ACTION
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS verification_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    verification_job_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    result JSONB,
    confidence NUMERIC,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_verification_results_job
        FOREIGN KEY (verification_job_id) REFERENCES verification_jobs(id)
        ON UPDATE NO ACTION
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON UPDATE NO ACTION
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_tenders_reference_number ON tenders(reference_number);
CREATE INDEX IF NOT EXISTS idx_tenders_created_by ON tenders(created_by);
CREATE INDEX IF NOT EXISTS idx_bidders_user_id ON bidders(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_bidder_id ON documents(bidder_id);
CREATE INDEX IF NOT EXISTS idx_verification_jobs_bidder_id ON verification_jobs(bidder_id);
CREATE INDEX IF NOT EXISTS idx_verification_jobs_document_id ON verification_jobs(document_id);
CREATE INDEX IF NOT EXISTS idx_verification_results_verification_job_id ON verification_results(verification_job_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type_entity_id ON audit_logs(entity_type, entity_id);
