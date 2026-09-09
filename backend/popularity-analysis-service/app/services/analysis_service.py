from __future__ import annotations

import math
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

    def predict_future_metrics(self, youtube_url: str, horizon_days: int = 7, save_result: bool = True) -> dict:
        analysis = self.analyze(youtube_url)
        metrics = analysis.metrics
        features = analysis.features
        now = utc_now_iso()

        growth_multiplier = self._future_growth_multiplier(features.popularity_score, horizon_days)
        engagement_lift = max(0.01, min(0.75, features.engagement_rate * (horizon_days / 14)))

        predicted_views = int(metrics.view_count * (1 + growth_multiplier))
        predicted_likes = int(metrics.like_count * (1 + growth_multiplier + engagement_lift))
        predicted_comments = int(metrics.comment_count * (1 + growth_multiplier + (engagement_lift / 2)))
        future_features = self._build_future_feature_row(
            features=features,
            predicted_views=predicted_views,
            predicted_likes=predicted_likes,
            predicted_comments=predicted_comments,
            horizon_days=horizon_days,
        )
        future_prediction_payload = self.prediction_service.predict(
            f"{analysis.video_id}_{horizon_days}",
            future_features,
        )

        future_prediction = {
            "id": f"{analysis.video_id}_{horizon_days}",
            "trailer_id": analysis.video_id,
            "horizon_days": horizon_days,
            "current_views": metrics.view_count,
            "current_likes": metrics.like_count,
            "current_comment_count": metrics.comment_count,
            "predicted_views": predicted_views,
            "predicted_likes": predicted_likes,
            "predicted_comment_count": predicted_comments,
            "expected_view_growth": predicted_views - metrics.view_count,
            "expected_like_growth": predicted_likes - metrics.like_count,
            "expected_comment_growth": predicted_comments - metrics.comment_count,
            "expected_view_growth_percent": ((predicted_views - metrics.view_count) / max(metrics.view_count, 1)) * 100,
            "expected_like_growth_percent": ((predicted_likes - metrics.like_count) / max(metrics.like_count, 1)) * 100,
            "expected_comment_growth_percent": ((predicted_comments - metrics.comment_count) / max(metrics.comment_count, 1)) * 100,
            "predicted_engagement_rate": (predicted_likes + predicted_comments) / max(predicted_views, 1),
            "predicted_reaction": future_prediction_payload["predicted_reaction"],
            "confidence_score": future_prediction_payload["confidence_score"],
            "probabilities": future_prediction_payload["probabilities"],
            "recommendation": future_prediction_payload["recommendation"],
            "model_name": future_prediction_payload["model_name"],
            "model_version": self.settings.model_version,
            "feature_row": future_features,
            "created_at": now,
        }

        payload = {
            "video_id": analysis.video_id,
            "trailer": analysis.trailer.model_dump(),
            "metrics": metrics.model_dump(),
            "features": features.model_dump(),
            "prediction": analysis.prediction.model_dump(),
            "future_prediction": future_prediction,
        }

        if save_result:
            history_id = str(uuid4())
            self.repository.set_document("future_predictions", future_prediction["id"], future_prediction)
            self.repository.set_document(
                "future_metrics_history",
                history_id,
                {
                    "id": history_id,
                    "video_id": analysis.video_id,
                    "title": analysis.trailer.title,
                    "horizon_days": horizon_days,
                    "current_views": metrics.view_count,
                    "predicted_views": predicted_views,
                    "predicted_reaction": future_prediction["predicted_reaction"],
                    "confidence_score": future_prediction["confidence_score"],
                    "popularity_score": future_features["popularity_score"],
                    "expected_view_growth_percent": future_prediction["expected_view_growth_percent"],
                    "created_at": now,
                },
            )

        return payload

    def get_future_prediction(self, video_id: str, horizon_days: int = 7) -> dict:
        doc = self.repository.get_document("future_predictions", f"{video_id}_{horizon_days}")
        if not doc:
            raise EntityNotFoundError("Future prediction not found. Run a future metrics prediction first.")
        return doc

    def list_future_history(self, limit: int = 20) -> list[dict]:
        return self.repository.list_documents("future_metrics_history", limit=limit, order_by="created_at", descending=True)

    def list_combined_history(self, limit: int = 20) -> dict:
        return {
            "trailer_analysis": self.list_history(limit=limit),
            "popularity_analysis": self.list_future_history(limit=limit),
        }

    def _future_growth_multiplier(self, popularity_score: float, horizon_days: int) -> float:
        score_factor = max(0.05, min(1.0, popularity_score / 100))
        horizon_factor = max(1, horizon_days) / 7
        return max(0.03, min(2.5, score_factor * 0.18 * horizon_factor))

    def _build_future_feature_row(
        self,
        features: TrailerFeatures,
        predicted_views: int,
        predicted_likes: int,
        predicted_comments: int,
        horizon_days: int,
    ) -> dict:
        future_age = max(features.video_age_days + horizon_days, 1)
        safe_views = max(predicted_views, 1)
        engagement_rate = (predicted_likes + predicted_comments) / safe_views
        like_ratio = predicted_likes / safe_views
        comment_rate = predicted_comments / safe_views
        comments_per_1000_views = comment_rate * 1000
        views_per_day = predicted_views / future_age
        likes_per_day = predicted_likes / future_age
        comments_per_day = predicted_comments / future_age
        popularity_score = min(
            100,
            (min(engagement_rate / 0.12, 1) * 45)
            + (min(like_ratio / 0.1, 1) * 25)
            + (min(comments_per_1000_views / 10, 1) * 15)
            + (min(views_per_day / 1_000_000, 1) * 15),
        )

        return {
            "views": predicted_views,
            "likes": predicted_likes,
            "comment_count": predicted_comments,
            "video_age_days": future_age,
            "engagement_rate": round(engagement_rate, 6),
            "like_ratio": round(like_ratio, 6),
            "comment_rate": round(comment_rate, 6),
            "comments_per_1000_views": round(comments_per_1000_views, 4),
            "views_per_day": round(views_per_day, 4),
            "likes_per_day": round(likes_per_day, 4),
            "comments_per_day": round(comments_per_day, 4),
            "log_views": round(math.log1p(predicted_views), 4),
            "log_likes": round(math.log1p(predicted_likes), 4),
            "log_comments": round(math.log1p(predicted_comments), 4),
            "growth_rate": round(views_per_day, 4),
            "popularity_score": round(popularity_score, 2),
        }

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
