import sys
from pathlib import Path

sys.path.insert(0, str(Path('backend').resolve()))

from sqlalchemy import create_engine, text
from app.config.settings import settings

if not settings.database_url:
    raise SystemExit('DATABASE_URL is not configured')

engine = create_engine(settings.database_url, future=True, echo=False)
seed_rows = [
    ('PAN', 'ABCDE1234F', 'VERIFIED', 'Demo PAN Account', '{"name":"Demo PAN Account","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('GST', '27ABCDE1234F1Z5', 'VERIFIED', 'Demo GST Account', '{"name":"Demo GST Account","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('UDYAM', 'UDYAM-TEST-001', 'VERIFIED', 'Demo Udyam Enterprise', '{"name":"Demo Udyam Enterprise","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('MCA', 'U12345', 'VERIFIED', 'Demo Company', '{"name":"Demo Company","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('DIGILOCKER', 'DL-USER-001', 'VERIFIED', 'Demo DigiLocker User', '{"name":"Demo DigiLocker User","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('EPFO', 'EPFO-123456', 'VERIFIED', 'Demo EPFO Member', '{"name":"Demo EPFO Member","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('ESIC', 'ESIC-123456', 'VERIFIED', 'Demo ESIC Member', '{"name":"Demo ESIC Member","entity_type":"bidder","verification_type":"vendor-gst","result":"verified"}'),
    ('BLACKLIST', 'DEMO-CLEAR-001', 'CLEAR', 'Demo Clear Blacklist Record', '{"name":"Demo Clear Blacklist Record","entity_type":"bidder","verification_type":"vendor-gst","result":"clear","listed":false}'),
    ('BLACKLIST', 'DEMO-BLACKLISTED-001', 'BLACKLISTED', 'Demo Blacklisted Record', '{"name":"Demo Blacklisted Record","entity_type":"bidder","verification_type":"vendor-gst","result":"blacklisted","listed":true}'),
]

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    conn.execute(text("CREATE TABLE IF NOT EXISTS demo_government_records (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), provider VARCHAR(80) NOT NULL, identifier VARCHAR(255) NOT NULL, status VARCHAR(80) NOT NULL, name VARCHAR(255) NULL, data JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), CONSTRAINT demo_government_records_provider_identifier_unique UNIQUE (provider, identifier))"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_demo_government_records_provider ON demo_government_records(provider)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_demo_government_records_identifier ON demo_government_records(identifier)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_demo_government_records_provider_identifier ON demo_government_records(provider, identifier)"))
    conn.execute(text("DELETE FROM demo_government_records WHERE provider = 'BLACKLIST' AND identifier = 'BLACKLIST-CASE-0001'"))

    for provider, identifier, status, name, data in seed_rows:
        conn.execute(
            text(
                """
                INSERT INTO demo_government_records (provider, identifier, status, name, data)
                VALUES (:provider, :identifier, :status, :name, CAST(:data AS jsonb))
                ON CONFLICT (provider, identifier)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    name = EXCLUDED.name,
                    data = EXCLUDED.data,
                    updated_at = NOW()
                """
            ),
            {
                'provider': provider,
                'identifier': identifier,
                'status': status,
                'name': name,
                'data': data,
            },
        )

print('live_m12_demo_seed_ok')
