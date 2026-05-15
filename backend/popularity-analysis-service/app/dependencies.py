from functools import lru_cache

from app.core.config import Settings, get_settings
from app.firebase.firebase_app import initialize_firestore
from app.repositories.base import BaseRepository
from app.repositories.firestore_repository import FirestoreRepository
from app.repositories.memory_repository import InMemoryRepository


@lru_cache
def get_repository() -> BaseRepository:
    settings: Settings = get_settings()
    if settings.firebase_mock_mode:
        return InMemoryRepository()
    db = initialize_firestore(settings)
    return FirestoreRepository(db)
