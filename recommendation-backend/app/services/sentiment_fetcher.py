"""Fetches audience sentiment data from the Firestore `analyses` collection.

The sentiment backend (port 5000) saves analysis results to the `analyses`
Firestore collection with the following top-level fields:
  - trailer_id       : YouTube video ID (e.g. "0ucTl-cxIjc")
  - trailer_title    : human-readable title
  - sentiment        : {"positive": float, "neutral": float, "negative": float}
  - deeperEmotions   : {"joy": float, "surprise": float, "sadness": float, ...}
  - commentTopics    : [{"topic": str, "mentions": int}, ...]
  - totalComments    : int
  - modelUsed        : str
  - modelMetrics     : {"accuracy": float, "f1Score": float, ...}
  - timestamp        : ISO datetime string

This module provides a single public function `get_sentiment_context()` which
returns a SentimentContext dataclass or None if Firestore is unavailable or
the collection is empty.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.firebase.firebase_config import get_firestore_client
from app.schemas.recommendation_schema import SentimentContext

logger = logging.getLogger(__name__)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dominant_emotion(deeper_emotions: dict[str, Any]) -> str:
    """Return the emotion with the highest percentage."""
    if not deeper_emotions:
        return "unknown"
    try:
        return max(deeper_emotions, key=lambda k: _safe_float(deeper_emotions[k]))
    except Exception:
        return "unknown"


def _sentiment_label(positive: float, negative: float) -> str:
    """Convert percentage split into a human-readable label."""
    if positive >= 60:
        return "Predominantly Positive"
    if negative >= 60:
        return "Predominantly Negative"
    if abs(positive - negative) <= 15:
        return "Mixed Reception"
    if positive > negative:
        return "Mostly Positive"
    return "Mostly Negative"


def get_sentiment_context(user_id: str, trailer_id: str | None = None) -> SentimentContext | None:
    """Return the latest (or trailer_id-matched) sentiment context from Firestore.

    Only reads the calling user's own sentiment analyses — the sentiment
    backend now saves each analysis under users/{uid}/analyses, so this must
    read from that same per-user path.

    Args:
        user_id: Firebase uid of the signed-in user making the request.
        trailer_id: YouTube video ID. When provided, the function tries to match
                    the `trailer_id` field in the collection first, then falls
                    back to the latest document.

    Returns:
        SentimentContext populated from Firestore, or None if unavailable.
    """
    db = get_firestore_client()
    if db is None:
        logger.warning("Firestore unavailable — sentiment context will be absent from recommendations.")
        return None

    settings = get_settings()
    safe_uid = user_id.replace("/", "_")
    collection_name = f"users/{safe_uid}/{settings.sentiment_firestore_collection}"

    try:
        doc_data: dict[str, Any] | None = None

        # 1. Try to find an exact trailer_id match first
        if trailer_id:
            docs = (
                db.collection(collection_name)
                .where("trailer_id", "==", trailer_id)
                .limit(1)
                .stream(retry=None, timeout=settings.firestore_timeout_seconds)
            )
            for doc in docs:
                doc_data = doc.to_dict()
                break

        # 2. Fall back to the most recent document
        if doc_data is None:
            docs = (
                db.collection(collection_name)
                .order_by("timestamp", direction="DESCENDING")
                .limit(1)
                .stream(retry=None, timeout=settings.firestore_timeout_seconds)
            )
            for doc in docs:
                doc_data = doc.to_dict()
                break

        if not doc_data:
            logger.info("No sentiment documents found in '%s' collection.", collection_name)
            return None

        # Parse sentiment percentages
        raw_sentiment: dict[str, Any] = doc_data.get("sentiment") or {}
        positive_pct = _safe_float(raw_sentiment.get("positive", 0))
        negative_pct = _safe_float(raw_sentiment.get("negative", 0))
        neutral_pct = _safe_float(raw_sentiment.get("neutral", 0))

        # Parse deeper emotions
        raw_emotions: dict[str, Any] = doc_data.get("deeperEmotions") or {}
        emotion_dist: dict[str, float] = {
            k: _safe_float(v) for k, v in raw_emotions.items()
        }

        # Parse comment topics (sorted by mention count, top 3)
        raw_topics: list[dict] = doc_data.get("commentTopics") or []
        top_topics = [
            t["topic"]
            for t in sorted(raw_topics, key=lambda x: _safe_float(x.get("mentions", 0)), reverse=True)
            if isinstance(t, dict) and t.get("topic")
        ][:3]

        # Parse model metrics
        raw_metrics: dict[str, Any] = doc_data.get("modelMetrics") or {}
        model_accuracy = _safe_float(raw_metrics.get("accuracy")) if raw_metrics else None

        ctx = SentimentContext(
            trailer_id=doc_data.get("trailer_id"),
            trailer_title=doc_data.get("trailer_title"),
            positive_pct=positive_pct,
            negative_pct=negative_pct,
            neutral_pct=neutral_pct,
            dominant_emotion=_dominant_emotion(emotion_dist),
            emotion_distribution=emotion_dist,
            top_topics=top_topics,
            total_comments=doc_data.get("totalComments"),
            model_used=doc_data.get("modelUsed"),
            model_accuracy=model_accuracy,
            sentiment_label=_sentiment_label(positive_pct, negative_pct),
        )

        logger.info(
            "Sentiment context loaded: trailer_id=%s, positive=%.1f%%, negative=%.1f%%, "
            "dominant=%s, topics=%s",
            ctx.trailer_id,
            positive_pct,
            negative_pct,
            ctx.dominant_emotion,
            top_topics,
        )
        return ctx

    except Exception as exc:
        logger.warning("Failed to fetch sentiment context from Firestore: %s", exc)
        return None
