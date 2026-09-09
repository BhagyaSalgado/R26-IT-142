from __future__ import annotations

from typing import Any, Dict, List, Protocol


class BaseRepository(Protocol):
    """Repository protocol used by both Firestore and local in-memory implementations."""

    def set_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def get_document(self, collection: str, document_id: str) -> Dict[str, Any] | None:
        ...

    def delete_document(self, collection: str, document_id: str) -> bool:
        ...

    def list_documents(self, collection: str, limit: int = 50, order_by: str | None = None, descending: bool = True) -> List[Dict[str, Any]]:
        ...
