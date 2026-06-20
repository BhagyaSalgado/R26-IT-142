from __future__ import annotations

from typing import Dict

from app.core.config import Settings
from app.ml.trained_model import TrainedPopularityModel


class PredictionService:
    """Prediction layer backed by trained ML artifacts."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = TrainedPopularityModel(
            artifacts_dir=settings.ml_artifacts_dir,
            model_type=settings.model_type,
        )

    def predict(self, trailer_id: str, features: Dict[str, float]) -> Dict:
        predicted_class, confidence, probabilities = self.model.predict(features)
        recommendation = self._build_recommendation(predicted_class, features)

        return {
            "id": trailer_id,
            "trailer_id": trailer_id,
            "predicted_reaction": predicted_class,
            "confidence_score": confidence,
            "model_name": self.model.model_name,
            "model_version": self.settings.model_version,
            "probabilities": probabilities,
            "recommendation": recommendation,
        }

    def _build_recommendation(self, predicted_class: str, features: Dict[str, float]) -> str:
        popularity_score = float(features.get("popularity_score", 0.0))
        engagement_rate = float(features.get("engagement_rate", 0.0))

        if predicted_class == "HIGH_REACTION":
            return (
                "Audience engagement is strong. Increase promotion, use retargeting campaigns, "
                "and highlight the trailer across social platforms."
            )
        if predicted_class == "MEDIUM_REACTION":
            return (
                "Audience engagement is moderate. Improve the thumbnail, title, posting time, "
                "and cross-platform sharing strategy."
            )
        return (
            "Audience engagement is low. Consider revising the trailer cut, title, thumbnail, "
            f"or campaign targeting. Current popularity score: {popularity_score:.2f}, "
            f"engagement rate: {engagement_rate:.4f}."
        )
