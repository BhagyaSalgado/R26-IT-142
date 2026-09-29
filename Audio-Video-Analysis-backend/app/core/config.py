from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "AI Movie Trailer Emotion Analyzer"
    API_PREFIX: str = "/api/v1"
    MODEL_DIR: Path = Path("app/models")
    UPLOAD_DIR: Path = Path("storage/uploads")
    OUTPUT_DIR: Path = Path("storage/outputs")
    SCENE_DURATION_SECONDS: int = 8
    VIDEO_IMG_SIZE: int = 224
    USE_YOLO: bool = True
    USE_DEEPFACE: bool = True
    USE_SHOT_BOUNDARY_DETECTION: bool = True
    MIN_SHOT_DURATION_SEC: float = 0.4
    MAX_SHOT_DURATION_SEC: float = 15.0
    USE_TRAINED_SCENE_MODELS: bool = False
    FIREBASE_CREDENTIALS_PATH: Path = Path("firebase-service-account.json")
    FIREBASE_PROJECT_ID: str = "movie-trailer-analyzer"
    FIREBASE_COLLECTION: str = "trailer_predictions"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
