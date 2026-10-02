from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.repositories.recommendation_repository import RecommendationRepository, _user_collection
from app.schemas.recommendation_schema import RecommendationResponse, RecommendationSummary


def _response() -> RecommendationResponse:
    return RecommendationResponse(
        summary=RecommendationSummary(
            trailer_title="Test Trailer",
            total_scenes=0,
            average_emotional_intensity=0.0,
            main_problem="No significant issues detected",
            overall_recommendation="No change required.",
        ),
        timeline_insights=[],
        recommendations=[],
    )


class _DocumentReference:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.saved = None

    def set(self, payload, **kwargs):
        self.saved = payload


class _Collection:
    def __init__(self, path: str):
        self.path = path
        self.document_reference = None

    def document(self, document_id: str):
        self.document_reference = _DocumentReference(document_id)
        return self.document_reference


class _Database:
    def __init__(self):
        self.collection_reference = None

    def collection(self, path: str):
        self.collection_reference = _Collection(path)
        return self.collection_reference


def test_user_collection_neutralizes_path_separators():
    assert _user_collection("user/with/slashes", "recommendations") == "users/user_with_slashes/recommendations"


def test_save_uses_user_scoped_collection_and_serializes_identity():
    database = _Database()
    settings = SimpleNamespace(firebase_collection="trailer_recommendations", firestore_timeout_seconds=5.0)

    with (
        patch("app.repositories.recommendation_repository.get_firestore_client", return_value=database),
        patch("app.repositories.recommendation_repository.get_settings", return_value=settings),
    ):
        saved_response = RecommendationRepository().save(_response(), "user-123")

    assert saved_response.recommendation_id
    assert saved_response.created_at
    assert database.collection_reference.path == "users/user-123/trailer_recommendations"
    document = database.collection_reference.document_reference
    assert document.document_id == saved_response.recommendation_id
    assert document.saved["user_id"] == "user-123"
    assert isinstance(document.saved["created_at"], datetime)


def test_save_remains_available_when_firestore_is_offline():
    settings = SimpleNamespace(firebase_collection="trailer_recommendations", firestore_timeout_seconds=5.0)
    with (
        patch("app.repositories.recommendation_repository.get_firestore_client", return_value=None),
        patch("app.repositories.recommendation_repository.get_settings", return_value=settings),
    ):
        saved_response = RecommendationRepository().save(_response(), "user-123")

    assert saved_response.recommendation_id
    assert saved_response.created_at


def test_normalize_document_converts_timestamp_and_uses_document_id():
    timestamp = datetime(2026, 10, 2, tzinfo=timezone.utc)
    result = RecommendationRepository._normalize_document("record-1", {"created_at": timestamp})

    assert result["recommendation_id"] == "record-1"
    assert result["created_at"] == timestamp.isoformat()
