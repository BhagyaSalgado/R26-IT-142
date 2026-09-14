from __future__ import annotations

from app.schemas.analysis import ComponentOutput
from app.schemas.features import TrailerFeatures
from app.schemas.prediction import PredictionResult


class ReportService:
    """Builds integration output for the main AI Prediction Engine."""

    def build_component_output(self, video_id: str, features: TrailerFeatures, prediction: PredictionResult) -> ComponentOutput:
        return ComponentOutput(
            video_id=video_id,
            prediction=prediction.predicted_reaction,
            confidence=prediction.confidence_score,
            popularity_score=features.popularity_score,
            engagement_rate=features.engagement_rate,
            model_version=prediction.model_version,
        )
