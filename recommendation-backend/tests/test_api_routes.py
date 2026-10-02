from fastapi.testclient import TestClient

from app.api import routes
from app.dependencies import AuthenticatedUser, get_current_user
from app.main import app
from app.schemas.recommendation_schema import RecommendationResponse, RecommendationSummary


def _authenticated_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-123", email="user@example.com", id_token="firebase-token")


def _response() -> RecommendationResponse:
    return RecommendationResponse(
        summary=RecommendationSummary(
            trailer_title="API Test",
            total_scenes=0,
            average_emotional_intensity=0.0,
            main_problem="No significant issues detected",
            overall_recommendation="No change required.",
        ),
        timeline_insights=[],
        recommendations=[],
    )


def test_health_endpoint_reports_service_status():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_history_endpoint_is_scoped_to_authenticated_user(monkeypatch):
    app.dependency_overrides[get_current_user] = _authenticated_user
    captured = {}

    def list_recent(user_id: str, limit: int):
        captured.update(user_id=user_id, limit=limit)
        return [{"recommendation_id": "rec-1"}]

    monkeypatch.setattr(routes.recommendation_repository, "list_recent", list_recent)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/recommendations/history?limit=5")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"items": [{"recommendation_id": "rec-1"}]}
    assert captured == {"user_id": "user-123", "limit": 5}


def test_missing_history_record_returns_404(monkeypatch):
    app.dependency_overrides[get_current_user] = _authenticated_user
    monkeypatch.setattr(routes.recommendation_repository, "get", lambda recommendation_id, user_id: None)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/recommendations/history/missing")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Recommendation result not found."


def test_generate_endpoint_uses_authenticated_identity(monkeypatch):
    app.dependency_overrides[get_current_user] = _authenticated_user
    generated = _response()
    captured = {}

    async def no_popularity(_token: str):
        return None

    def save(response: RecommendationResponse, user_id: str):
        captured["user_id"] = user_id
        return response

    monkeypatch.setattr(routes, "_load_latest_popularity_context", no_popularity)
    monkeypatch.setattr(routes, "get_sentiment_context", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(routes, "generate_recommendations", lambda *_args, **_kwargs: generated)
    monkeypatch.setattr(routes.recommendation_repository, "save", save)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/recommendations/generate",
                json={"trailer_title": "API Test", "final_system_output": []},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["summary"]["trailer_title"] == "API Test"
    assert captured["user_id"] == "user-123"
