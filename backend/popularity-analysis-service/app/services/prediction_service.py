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
        if predicted_class == "HIGH_REACTION":
            return "Audience engagement is strong. Consider increasing trailer promotion and retargeting campaigns."
        if predicted_class == "MEDIUM_REACTION":
            return "Audience engagement is moderate. Improve thumbnails, release timing, and social sharing strategy."
        return "Audience engagement is low. Consider revising promotional content, title, thumbnail, or campaign targeting."
