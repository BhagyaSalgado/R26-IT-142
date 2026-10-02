from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Movie Trailer Recommendation Engine"
    emotion_api_base_url: str = "http://127.0.0.1:8000"
    emotion_output_dir: str = ""
    popularity_api_base_url: str = "http://127.0.0.1:8001"
    cors_origins: str = "http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:5173,http://localhost:5174"
    allow_anonymous_access: bool = False
    firebase_credentials_path: str = "firebase-service-account.json"
    firebase_project_id: str = "movie-trailer-analyzer"
    firebase_collection: str = "trailer_recommendations"
    sentiment_firestore_collection: str = "analyses"
    emotion_firestore_collection: str = "trailer_predictions"
    firestore_timeout_seconds: float = 5.0
    # Ground truth for the frame-level checks: the film's real title and
    # release date, so the OCR pass can tell whether the trailer ever shows
    # them. Get a free key at http://www.omdbapi.com/apikey.aspx and set
    # OMDB_API_KEY in .env. Without one those two checks are skipped.
    omdb_api_key: str = ""
    omdb_base_url: str = "https://www.omdbapi.com/"

    # Real, unique per-scene fix text generated live by Claude from the real
    # detected evidence, instead of picking from a fixed phrase template.
    # Get a key at https://console.anthropic.com/settings/keys. Without one,
    # fix text falls back to the template system (still genre-aware, just
    # not uniquely worded per scene).
    anthropic_api_key: str = ""
    llm_fix_model: str = "claude-opus-5"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]



@lru_cache
def get_settings() -> Settings:
    return Settings()
