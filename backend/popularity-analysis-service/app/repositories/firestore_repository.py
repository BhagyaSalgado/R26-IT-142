from __future__ import annotations

from typing import Any, Dict, List

from google.cloud.firestore_v1 import Query


class FirestoreRepository:
    """Firestore-backed repository.

    Collections used by this service:
    - trailers
    - trailer_metrics
    - trailer_features
    - predictions
    - analysis_history
    - model_evaluations
    """

    def __init__(self, db) -> None:
        self.db = db

    def set_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        self.db.collection(collection).document(document_id).set(data, merge=True)
        return data

    def get_document(self, collection: str, document_id: str) -> Dict[str, Any] | None:
        snapshot = self.db.collection(collection).document(document_id).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()

    def delete_document(self, collection: str, document_id: str) -> bool:
        self.db.collection(collection).document(document_id).delete()
        return True

    def list_documents(self, collection: str, limit: int = 50, order_by: str | None = None, descending: bool = True) -> List[Dict[str, Any]]:
        query = self.db.collection(collection)
        if order_by:
            direction = Query.DESCENDING if descending else Query.ASCENDING
            query = query.order_by(order_by, direction=direction)
        query = query.limit(limit)
        return [doc.to_dict() for doc in query.stream()]
