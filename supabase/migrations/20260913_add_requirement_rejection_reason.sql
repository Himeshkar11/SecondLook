-- Add durable officer rejection reason without modifying existing requirement lifecycle data.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tender_requirements' AND column_name = 'rejection_reason'
    ) THEN
        ALTER TABLE tender_requirements ADD COLUMN rejection_reason TEXT NULL;
    END IF;
END $$;
