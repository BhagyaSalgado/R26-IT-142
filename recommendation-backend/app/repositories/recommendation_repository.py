import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import get_settings
from app.firebase.firebase_config import get_firestore_client
from app.schemas.recommendation_schema import RecommendationResponse

logger = logging.getLogger(__name__)


def _user_collection(user_id: str, collection: str) -> str:
    # Every signed-in user's saved recommendations live under their own
    # Firestore subtree so one user can never list or read another user's data.
    safe_uid = user_id.replace("/", "_")
    return f"users/{safe_uid}/{collection}"


class RecommendationRepository:
    def save(self, response: RecommendationResponse, user_id: str) -> RecommendationResponse:
        settings = get_settings()
        recommendation_id = response.recommendation_id or f"REC-RUN-{uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc)

        response.recommendation_id = recommendation_id
        response.created_at = created_at.isoformat()

        db = get_firestore_client()
        if db is None:
            logger.warning("Firestore unavailable; returning recommendation without saving history.")
            return response

        try:
            doc_ref = db.collection(_user_collection(user_id, settings.firebase_collection)).document(recommendation_id)
            doc_ref.set(
                {
                    **response.model_dump(mode="json"),
                    "user_id": user_id,
                    "created_at": created_at,
                },
                retry=None,
                timeout=settings.firestore_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("Could not save recommendation history: %s", exc)
        return response

    def get(self, recommendation_id: str, user_id: str) -> dict | None:
        settings = get_settings()
        db = get_firestore_client()
        if db is None:
            return None
        try:
            document = (
                db.collection(_user_collection(user_id, settings.firebase_collection))
                .document(recommendation_id)
                .get(retry=None, timeout=settings.firestore_timeout_seconds)
            )
        except Exception as exc:
            logger.warning("Could not load recommendation '%s': %s", recommendation_id, exc)
            return None
        if not document.exists:
            return None

        return self._normalize_document(document.id, document.to_dict() or {})

    def list_recent(self, user_id: str, limit: int = 12) -> list[dict]:
        settings = get_settings()
        db = get_firestore_client()
        if db is None:
            return []
        try:
            documents = (
                db.collection(_user_collection(user_id, settings.firebase_collection))
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream(retry=None, timeout=settings.firestore_timeout_seconds)
            )
            return [self._normalize_document(document.id, document.to_dict() or {}) for document in documents]
        except Exception as exc:
            logger.warning("Could not load recommendation history: %s", exc)
            return []

    @staticmethod
    def _normalize_document(document_id: str, data: dict) -> dict:
        created_at = data.get("created_at")
        if hasattr(created_at, "isoformat"):
            data["created_at"] = created_at.isoformat()
        data["recommendation_id"] = data.get("recommendation_id") or document_id
        return data
