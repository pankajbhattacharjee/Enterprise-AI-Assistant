from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    jwt_secret: str = "development-secret-change-me"
    access_token_expire_minutes: int = 480
    database_url: str = "sqlite:///./enterprise_assistant.db"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    firebase_credentials_path: str | None = None
    max_upload_mb: int = 15
    cors_origins: str = "http://localhost:8501"
    upload_dir: Path = Path("uploads")
    report_dir: Path = Path("reports")
    index_dir: Path = Path("data")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
