from __future__ import annotations

import math
from typing import Dict, Tuple

REACTION_CLASSES = ["LOW_REACTION", "MEDIUM_REACTION", "HIGH_REACTION"]


class SimulatedPopularityModel:
    """Temporary classifier used before real ML models are trained.

    Replace this class later with real Logistic Regression, Random Forest, or SVM models.
    """

    def predict(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        score = float(features.get("popularity_score", 0.0))
        engagement_rate = float(features.get("engagement_rate", 0.0))

        if score >= 70:
            predicted = "HIGH_REACTION"
        elif score >= 40:
            predicted = "MEDIUM_REACTION"
        else:
            predicted = "LOW_REACTION"

        probabilities = self._probabilities(score, engagement_rate)
        confidence = max(probabilities.values())
        return predicted, round(confidence, 4), probabilities

    def _probabilities(self, score: float, engagement_rate: float) -> Dict[str, float]:
        # Small engagement bonus keeps the output responsive to like/comment activity.
        engagement_bonus = min(engagement_rate / 0.08, 1.0) * 8.0
        adjusted_score = max(0.0, min(100.0, score + engagement_bonus))

        low_logit = (40 - adjusted_score) / 15
        medium_logit = -abs(adjusted_score - 55) / 18 + 1
        high_logit = (adjusted_score - 65) / 15
        logits = [low_logit, medium_logit, high_logit]
        exp_values = [math.exp(x) for x in logits]
        total = sum(exp_values)
        probs = [value / total for value in exp_values]

        return {label: round(prob, 4) for label, prob in zip(REACTION_CLASSES, probs)}
