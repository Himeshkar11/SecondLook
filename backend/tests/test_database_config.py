import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.settings import settings
from app.database.repository import select_one


def test_settings_module_imports_and_defaults():
    assert settings.environment == "development"
    assert settings.api_base_url == "http://localhost:8000"


def test_database_probe_returns_one_for_configured_database_url():
    assert select_one() == 1
