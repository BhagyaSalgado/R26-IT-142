from datetime import datetime, timedelta, timezone

from app.services.feature_engineering_service import FeatureEngineeringService


def test_build_features():
    published_at = (datetime.now(timezone.utc) - timedelta(days=10)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metrics = {
        "view_count": 100000,
        "like_count": 5000,
        "comment_count": 700,
    }
    service = FeatureEngineeringService()
    features = service.build_features("abc123", published_at, metrics)
    assert features["trailer_id"] == "abc123"
    assert features["engagement_rate"] > 0
    assert 0 <= features["popularity_score"] <= 100
