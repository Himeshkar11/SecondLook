-- Migration: Add OCR and AI extraction lifecycle columns to documents table (Tasks 08 & 09)

ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS ocr_status VARCHAR(50) DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS ocr_text TEXT,
    ADD COLUMN IF NOT EXISTS ocr_error TEXT,
    ADD COLUMN IF NOT EXISTS ocr_completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ai_status VARCHAR(50) DEFAULT 'AI_PENDING',
    ADD COLUMN IF NOT EXISTS ai_extraction JSONB,
    ADD COLUMN IF NOT EXISTS ai_error TEXT,
    ADD COLUMN IF NOT EXISTS ai_completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ai_model VARCHAR(255),
    ADD COLUMN IF NOT EXISTS ai_prompt_version VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_documents_ocr_status ON documents(ocr_status);
CREATE INDEX IF NOT EXISTS idx_documents_ai_status ON documents(ai_status);
