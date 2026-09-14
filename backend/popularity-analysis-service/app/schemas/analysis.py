from pydantic import BaseModel, Field, HttpUrl

from app.schemas.features import TrailerFeatures
from app.schemas.metrics import TrailerMetrics
from app.schemas.prediction import PredictionResult
from app.schemas.trailer import Trailer


class AnalyzeTrailerRequest(BaseModel):
    youtube_url: HttpUrl | str = Field(description="YouTube trailer URL or video id")


class BatchAnalyzeRequest(BaseModel):
    youtube_urls: list[HttpUrl | str] = Field(min_length=1, max_length=20)


class AnalysisData(BaseModel):
    video_id: str
    trailer: Trailer
    metrics: TrailerMetrics
    features: TrailerFeatures
    prediction: PredictionResult


class AnalysisHistoryItem(BaseModel):
    id: str
    video_id: str
    title: str
    predicted_reaction: str
    confidence_score: float
    popularity_score: float
    created_at: str


class ComponentOutput(BaseModel):
    component: str = "popularity_metrics_analysis"
    video_id: str
    prediction: str
    confidence: float
    popularity_score: float
    engagement_rate: float
    model_version: str
