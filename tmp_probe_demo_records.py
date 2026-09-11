import sys
from pathlib import Path

sys.path.insert(0, str(Path('backend').resolve()))

from sqlalchemy import create_engine, text
from app.config.settings import settings

if not settings.database_url:
    raise SystemExit('DATABASE_URL is not configured')

engine = create_engine(settings.database_url, future=True, echo=False)
with engine.begin() as conn:
    rows = conn.execute(text("""
        SELECT provider, identifier, status, name
        FROM demo_government_records
        WHERE provider IN ('PAN','GST','UDYAM','MCA','DIGILOCKER','EPFO','ESIC','BLACKLIST')
        ORDER BY provider
    """)).fetchall()
    print(rows)
