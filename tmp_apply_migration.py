from pathlib import Path
import re

from sqlalchemy import text

from app.database.connection import engine
from app.config.settings import settings

migration_path = Path("supabase/migrations/20260911_create_core_domain_schema.sql")
migration = migration_path.read_text(encoding="utf-8")

destructive = bool(re.search(r"\bDROP\s+(TABLE|SCHEMA|DATABASE)\b", migration, re.IGNORECASE))
if destructive:
    print("Migration inspected: FAIL")
    raise SystemExit(2)

print("Migration inspected: PASS")

# Split by semicolon and execute only non-empty PostgreSQL statements.
statements = [part.strip() for part in migration.split(";") if part.strip()]

with engine.begin() as conn:
    for statement in statements:
        conn.execute(text(statement))

print("Migration applied: PASS")