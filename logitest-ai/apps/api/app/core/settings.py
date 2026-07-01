from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://logitest:logitest@localhost:5432/logitest_ai"
    elasticsearch_url: str = "http://localhost:9200"
    demo_log_index: str = "logitest-demo-logs"
    staging_api_base_url: str = "http://localhost:4000"
    shoplite_log_path: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
