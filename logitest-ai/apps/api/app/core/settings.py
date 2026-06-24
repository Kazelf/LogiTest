from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://logitest:logitest@localhost:5432/logitest_ai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
