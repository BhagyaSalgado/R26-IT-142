from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import Settings
from app.core.exceptions import EntityNotFoundError
from app.repositories.base import BaseRepository
from app.schemas.analysis import AnalysisData, AnalysisHistoryItem, ComponentOutput
from app.schemas.features import TrailerFeatures
from app.schemas.metrics import TrailerMetrics
from app.schemas.prediction import PredictionResult
from app.schemas.trailer import Trailer
from app.services.feature_engineering_service import FeatureEngineeringService
from app.services.prediction_service import PredictionService
from app.services.report_service import ReportService
from app.services.youtube_service import YouTubeService


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AnalysisService:
    def __init__(self, settings: Settings, repository: BaseRepository) -> None:
        self.settings = settings
        self.repository = repository
        self.youtube_service = YouTubeService(settings)
        self.feature_service = FeatureEngineeringService()
        self.prediction_service = PredictionService(settings)
        self.report_service = ReportService()

    def analyze(self, youtube_url: str) -> AnalysisData:
        raw_data = self.youtube_service.fetch_trailer_data(youtube_url)
        video_id = raw_data["video_id"]
        now = utc_now_iso()

        existing = self.repository.get_document("trailers", video_id)
        created_at = existing.get("created_at") if existing else now

        trailer = Trailer(
            id=video_id,
            youtube_video_id=video_id,
            youtube_url=raw_data["youtube_url"],
            title=raw_data["title"],
            channel_name=raw_data["channel_name"],
            published_at=raw_data["published_at"],
            thumbnail_url=raw_data.get("thumbnail_url"),
            created_at=created_at,
            updated_at=now,
        )

        metrics_payload = raw_data["metrics"]
        metrics = TrailerMetrics(
            id=video_id,
            trailer_id=video_id,
            view_count=metrics_payload["view_count"],
            like_count=metrics_payload["like_count"],
            comment_count=metrics_payload["comment_count"],
            favorite_count=metrics_payload.get("favorite_count", 0),
            source=metrics_payload.get("source", "simulated"),
            collected_at=now,
        )

        feature_payload = self.feature_service.build_features(
            trailer_id=video_id,
            published_at=trailer.published_at,
            metrics=metrics.model_dump(),
        )
        features = TrailerFeatures(**feature_payload, created_at=now)

        prediction_payload = self.prediction_service.predict(video_id, features.model_dump())
        prediction = PredictionResult(**prediction_payload, created_at=now)

        self.repository.set_document("trailers", video_id, trailer.model_dump())
        self.repository.set_document("trailer_metrics", video_id, metrics.model_dump())
        self.repository.set_document("trailer_features", video_id, features.model_dump())
        self.repository.set_document("predictions", video_id, prediction.model_dump())

        history_id = str(uuid4())
        history_item = AnalysisHistoryItem(
            id=history_id,
            video_id=video_id,
            title=trailer.title,
            predicted_reaction=prediction.predicted_reaction,
            confidence_score=prediction.confidence_score,
            popularity_score=features.popularity_score,
            created_at=now,
        )
        self.repository.set_document("analysis_history", history_id, history_item.model_dump())

        return AnalysisData(video_id=video_id, trailer=trailer, metrics=metrics, features=features, prediction=prediction)

    def get_trailer(self, video_id: str) -> Trailer:
        doc = self.repository.get_document("trailers", video_id)
        if not doc:
            raise EntityNotFoundError("Trailer not found. Analyze it first.")
        return Trailer(**doc)

    def get_metrics(self, video_id: str) -> TrailerMetrics:
        doc = self.repository.get_document("trailer_metrics", video_id)
        if not doc:
            raise EntityNotFoundError("Metrics not found. Analyze the trailer first.")
        return TrailerMetrics(**doc)

    def get_features(self, video_id: str) -> TrailerFeatures:
        doc = self.repository.get_document("trailer_features", video_id)
        if not doc:
            raise EntityNotFoundError("Features not found. Analyze the trailer first.")
        return TrailerFeatures(**doc)

    def get_prediction(self, video_id: str) -> PredictionResult:
        doc = self.repository.get_document("predictions", video_id)
        if not doc:
            raise EntityNotFoundError("Prediction not found. Analyze the trailer first.")
        return PredictionResult(**doc)

    def get_component_output(self, video_id: str) -> ComponentOutput:
        features = self.get_features(video_id)
        prediction = self.get_prediction(video_id)
        return self.report_service.build_component_output(video_id=video_id, features=features, prediction=prediction)

    def list_history(self, limit: int = 20) -> list[AnalysisHistoryItem]:
        docs = self.repository.list_documents("analysis_history", limit=limit, order_by="created_at", descending=True)
        return [AnalysisHistoryItem(**doc) for doc in docs]

    def create_simulated_evaluation(self) -> dict:
        now = utc_now_iso()
        evaluation_id = str(uuid4())
        evaluation = {
            "id": evaluation_id,
            "model_name": self.settings.model_name,
            "model_version": self.settings.model_version,
            "accuracy": 0.84,
            "precision": 0.82,
            "recall": 0.81,
            "f1_score": 0.815,
            "dataset_size": 250,
            "trained_at": now,
            "notes": "Simulated evaluation record. Replace after real model training.",
        }
        self.repository.set_document("model_evaluations", evaluation_id, evaluation)
        return evaluation

    def get_latest_model_performance(self) -> dict:
        docs = self.repository.list_documents("model_evaluations", limit=1, order_by="trained_at", descending=True)
        if docs:
            return docs[0]
        return {
            "id": "simulated-default",
            "model_name": self.settings.model_name,
            "model_version": self.settings.model_version,
            "accuracy": 0.84,
            "precision": 0.82,
            "recall": 0.81,
            "f1_score": 0.815,
            "dataset_size": 250,
            "trained_at": utc_now_iso(),
            "notes": "Default simulated performance. No real model has been trained yet.",
        }
