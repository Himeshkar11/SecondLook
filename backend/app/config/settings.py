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
    ai_provider: str = Field(default="demo", alias="AI_PROVIDER")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_primary_model: str = Field(default="google/gemini-2.5-flash", alias="OPENROUTER_PRIMARY_MODEL")
    openrouter_fallback_model_1: str = Field(default="anthropic/claude-3-haiku", alias="OPENROUTER_FALLBACK_MODEL_1")
    openrouter_fallback_model_2: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_FALLBACK_MODEL_2")
    ai_timeout_seconds: float = Field(default=60.0, alias="AI_TIMEOUT_SECONDS")
    ai_max_retries: int = Field(default=1, alias="AI_MAX_RETRIES")

    ocr_provider: str = Field(default="", alias="OCR_PROVIDER")
    ocr_api_key: str = Field(default="", alias="OCR_API_KEY")
    ocr_base_url: str = Field(default="", alias="OCR_BASE_URL")

    gst_provider: str = Field(default="demo", alias="GST_PROVIDER")
    gst_api_url: str = Field(default="", alias="GST_API_URL")
    gst_api_key: str = Field(default="", alias="GST_API_KEY")

    pan_provider: str = Field(default="demo", alias="PAN_PROVIDER")
    pan_api_url: str = Field(default="", alias="PAN_API_URL")
    pan_api_key: str = Field(default="", alias="PAN_API_KEY")

    udyam_provider: str = Field(default="demo", alias="UDYAM_PROVIDER")
    epfo_provider: str = Field(default="demo", alias="EPFO_PROVIDER")
    esic_provider: str = Field(default="demo", alias="ESIC_PROVIDER")
    startup_india_provider: str = Field(default="demo", alias="STARTUP_INDIA_PROVIDER")
    nsic_provider: str = Field(default="demo", alias="NSIC_PROVIDER")
    make_in_india_provider: str = Field(default="demo", alias="MAKE_IN_INDIA_PROVIDER")
    oem_provider: str = Field(default="demo", alias="OEM_PROVIDER")
    blacklist_provider: str = Field(default="demo", alias="BLACKLIST_PROVIDER")


    def model_post_init(self, __context) -> None:
        if not self.supabase_url and self.vite_supabase_url:
            self.supabase_url = self.vite_supabase_url
        if not self.supabase_key and self.vite_supabase_publishable_key:
            self.supabase_key = self.vite_supabase_publishable_key
        if not self.openrouter_api_key and self.ai_api_key:
            self.openrouter_api_key = self.ai_api_key

    @property
    def app_environment(self) -> str:
        return self.environment


settings = Settings()
