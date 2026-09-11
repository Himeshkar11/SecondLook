from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Centralized typed configuration for SecondLook backend services.

    Values are sourced from environment variables and optionally from the
    repository root local .env file. The settings object is intentionally the
    single place where configuration is loaded.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    database_url: str = Field(default="", alias="DATABASE_URL")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")
    vite_supabase_url: str = Field(default="", alias="VITE_SUPABASE_URL")
    vite_supabase_publishable_key: str = Field(default="", alias="VITE_SUPABASE_PUBLISHABLE_KEY")

    max_document_size_mb: int = Field(default=10, alias="MAX_DOCUMENT_SIZE_MB")
    storage_bucket: str = Field(default="bidder-documents", alias="STORAGE_BUCKET")

    ai_api_key: str = Field(default="", alias="AI_API_KEY")

    ocr_provider: str = Field(default="", alias="OCR_PROVIDER")
    ocr_api_key: str = Field(default="", alias="OCR_API_KEY")
    ocr_base_url: str = Field(default="", alias="OCR_BASE_URL")

    def model_post_init(self, __context) -> None:
        if not self.supabase_url and self.vite_supabase_url:
            self.supabase_url = self.vite_supabase_url
        if not self.supabase_key and self.vite_supabase_publishable_key:
            self.supabase_key = self.vite_supabase_publishable_key

    @property
    def app_environment(self) -> str:
        return self.environment


settings = Settings()
