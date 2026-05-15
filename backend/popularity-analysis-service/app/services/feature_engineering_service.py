from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _round(value: float) -> float:
    return round(float(value), 6)


class FeatureEngineeringService:
    """Calculates features used by the popularity prediction model."""

    def build_features(self, trailer_id: str, published_at: str, metrics: Dict[str, int]) -> Dict[str, float | int | str]:
        view_count = int(metrics.get("view_count", 0))
        like_count = int(metrics.get("like_count", 0))
        comment_count = int(metrics.get("comment_count", 0))

        now = datetime.now(timezone.utc)
        published_dt = _parse_datetime(published_at)
        video_age_days = max(1, (now - published_dt).days)

        engagement_rate = _safe_div(like_count + comment_count, view_count)
        like_ratio = _safe_div(like_count, view_count)
        comment_rate = _safe_div(comment_count, view_count)
        comments_per_1000_views = comment_rate * 1000
        views_per_day = _safe_div(view_count, video_age_days)
        growth_rate = views_per_day

        popularity_score = self._calculate_popularity_score(
            view_count=view_count,
            engagement_rate=engagement_rate,
            comments_per_1000_views=comments_per_1000_views,
            views_per_day=views_per_day,
        )

        return {
            "id": trailer_id,
            "trailer_id": trailer_id,
            "video_age_days": int(video_age_days),
            "engagement_rate": _round(engagement_rate),
            "like_ratio": _round(like_ratio),
            "comment_rate": _round(comment_rate),
            "comments_per_1000_views": _round(comments_per_1000_views),
            "views_per_day": _round(views_per_day),
            "growth_rate": _round(growth_rate),
            "popularity_score": _round(popularity_score),
        }

    def _calculate_popularity_score(
        self,
        view_count: int,
        engagement_rate: float,
        comments_per_1000_views: float,
        views_per_day: float,
    ) -> float:
        """Heuristic score from 0 to 100 used until a trained model is integrated."""
        view_score = min(math.log10(view_count + 1) / 7.5, 1.0) * 100
        engagement_score = min(engagement_rate / 0.08, 1.0) * 100
        comment_score = min(comments_per_1000_views / 10, 1.0) * 100
        growth_score = min(views_per_day / 1_000_000, 1.0) * 100

        score = (0.35 * view_score) + (0.30 * engagement_score) + (0.20 * comment_score) + (0.15 * growth_score)
        return max(0.0, min(100.0, score))
