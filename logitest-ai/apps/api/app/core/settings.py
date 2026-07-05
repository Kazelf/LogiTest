from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

LOGITEST_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    database_url: str = "postgresql://logitest:logitest@localhost:5432/logitest_ai"
    elasticsearch_url: str = "http://localhost:9200"
    demo_log_index: str = "logitest-demo-logs"
    staging_api_base_url: str = "http://localhost:4000"
    shoplite_log_path: str | None = None
    google_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    ai_provider: str = "gemini"
    ai_fallback_rule_based: bool = True

    model_config = SettingsConfigDict(env_file=LOGITEST_ROOT / ".env", extra="ignore")


settings = Settings()
