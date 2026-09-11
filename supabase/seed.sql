-- M12: Supabase demo government verification seed data.
-- This file is deterministic and intentionally references only the
-- `demo_government_records` table. No local JSON or provider-specific
-- fixture files are used for the source-of-truth records.

INSERT INTO demo_government_records (provider, identifier, status, name, data)
VALUES
    ('PAN', 'ABCDE1234F', 'VERIFIED', 'Demo PAN Account', '{"name":"Demo PAN Account","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('GST', '27ABCDE1234F1Z5', 'VERIFIED', 'Demo GST Account', '{"name":"Demo GST Account","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('UDYAM', 'UDYAM-TEST-001', 'VERIFIED', 'Demo Udyam Enterprise', '{"name":"Demo Udyam Enterprise","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('MCA', 'U12345', 'VERIFIED', 'Demo Company', '{"name":"Demo Company","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('DIGILOCKER', 'DL-USER-001', 'VERIFIED', 'Demo DigiLocker User', '{"name":"Demo DigiLocker User","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('EPFO', 'EPFO-123456', 'VERIFIED', 'Demo EPFO Member', '{"name":"Demo EPFO Member","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('ESIC', 'ESIC-123456', 'VERIFIED', 'Demo ESIC Member', '{"name":"Demo ESIC Member","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'::jsonb),
    ('BLACKLIST', 'DEMO-CLEAR-001', 'CLEAR', 'Demo Clear Blacklist Record', '{"name":"Demo Clear Blacklist Record","entity_type":"bidder","verification_type":"vendor-gst","result":"clear","listed":false}'::jsonb),
    ('BLACKLIST', 'DEMO-BLACKLISTED-001', 'BLACKLISTED', 'Demo Blacklisted Record', '{"name":"Demo Blacklisted Record","entity_type":"bidder","verification_type":"vendor-gst","result":"blacklisted","listed":true}'::jsonb)
ON CONFLICT (provider, identifier) DO UPDATE
SET status = EXCLUDED.status,
    name = EXCLUDED.name,
    data = EXCLUDED.data,
    updated_at = NOW();

-- Intentionally no BLACKLIST demo record for DEMO-UNKNOWN-999. The
-- repository-backed architecture will return NOT_FOUND from the no-row case.

