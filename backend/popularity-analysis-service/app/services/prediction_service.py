from __future__ import annotations

from typing import Dict

from app.core.config import Settings
from app.ml.simulated_model import SimulatedPopularityModel
from app.ml.trained_model import TrainedPopularityModel


class PredictionService:
    """Prediction layer using real ML artifacts when available.

    If USE_SIMULATED_MODEL=true, it uses the old simulated model.
    If USE_SIMULATED_MODEL=false, it loads trained artifacts from ML_ARTIFACTS_DIR.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.using_real_model = False

        if settings.use_simulated_model:
            self.model = SimulatedPopularityModel()
            return

        try:
            self.model = TrainedPopularityModel(
                artifacts_dir=settings.ml_artifacts_dir,
                model_type=settings.model_type,
            )
            self.using_real_model = True
        except Exception as exc:
            # Keep the API running during development instead of crashing.
            # For production, set this to raise the exception.
            print(f"[PredictionService] Real model loading failed: {exc}")
            print("[PredictionService] Falling back to SimulatedPopularityModel.")
            self.model = SimulatedPopularityModel()

    def predict(self, trailer_id: str, features: Dict[str, float]) -> Dict:
        predicted_class, confidence, probabilities = self.model.predict(features)
        recommendation = self._build_recommendation(predicted_class, features)

        model_name = self.settings.model_name
        if self.using_real_model and hasattr(self.model, "model_name"):
            model_name = self.model.model_name

        return {
            "id": trailer_id,
            "trailer_id": trailer_id,
            "predicted_reaction": predicted_class,
            "confidence_score": confidence,
            "model_name": model_name,
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
