from __future__ import annotations

from typing import Dict

from app.core.config import Settings
from app.ml.simulated_model import SimulatedPopularityModel


class PredictionService:
    """Prediction layer.

    This currently uses a simulated model so the microservice can be integrated with
    frontend and Firebase immediately. Replace this service when trained models are ready.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = SimulatedPopularityModel()
        # self.model = SimulatedPopularityModel()

    def predict(self, trailer_id: str, features: Dict[str, float]) -> Dict:
        predicted_class, confidence, probabilities = self.model.predict(features)
        recommendation = self._build_recommendation(predicted_class, features)
        return {
            "id": trailer_id,
            "trailer_id": trailer_id,
            "predicted_reaction": predicted_class,
            "confidence_score": confidence,
            "model_name": self.settings.model_name,
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
