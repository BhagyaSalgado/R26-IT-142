from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


class InMemoryRepository:
    """Simple local repository for quick development without Firebase credentials."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, dict[str, Any]]] = {}

    def set_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        self._store.setdefault(collection, {})[document_id] = deepcopy(data)
        return deepcopy(data)

    def get_document(self, collection: str, document_id: str) -> Dict[str, Any] | None:
        value = self._store.get(collection, {}).get(document_id)
        return deepcopy(value) if value is not None else None

    def delete_document(self, collection: str, document_id: str) -> bool:
        if document_id in self._store.get(collection, {}):
            del self._store[collection][document_id]
            return True
        return False

    def list_documents(self, collection: str, limit: int = 50, order_by: str | None = None, descending: bool = True) -> List[Dict[str, Any]]:
        docs = list(self._store.get(collection, {}).values())
        if order_by:
            docs.sort(key=lambda item: item.get(order_by, ""), reverse=descending)
        return deepcopy(docs[:limit])
