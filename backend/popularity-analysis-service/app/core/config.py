from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Movie Trailer Popularity Metrics Service", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    firebase_mock_mode: bool = Field(default=True, alias="FIREBASE_MOCK_MODE")
    firebase_project_id: str | None = Field(default=None, alias="FIREBASE_PROJECT_ID")
    firebase_credentials_path: str | None = Field(default="serviceAccountKey.json", alias="FIREBASE_CREDENTIALS_PATH")

    youtube_api_key: str | None = Field(default=None, alias="YOUTUBE_API_KEY")
    youtube_api_timeout_seconds: int = Field(default=10, alias="YOUTUBE_API_TIMEOUT_SECONDS")

    model_name: str = Field(default="SimulatedPopularityClassifier", alias="MODEL_NAME")
    model_version: str = Field(default="v0.1-simulated", alias="MODEL_VERSION")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
