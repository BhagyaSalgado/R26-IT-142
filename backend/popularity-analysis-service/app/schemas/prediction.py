from typing import Dict

from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    id: str
    trailer_id: str
    predicted_reaction: str = Field(description="LOW_REACTION, MEDIUM_REACTION, or HIGH_REACTION")
    confidence_score: float = Field(ge=0, le=1)
    model_name: str
    model_version: str
    probabilities: Dict[str, float]
    recommendation: str
    created_at: str
