import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_db = None


def get_firestore_client():
    """Return a Firestore client, or None if Firebase cannot be initialised."""
    global _db
    if _db is not None:
        return _db

    settings = get_settings()
    credentials_path = Path(settings.firebase_credentials_path)

    if not credentials_path.exists():
        logger.warning(
            "Firebase credentials file not found at %s — Firestore features disabled.",
            credentials_path,
        )
        return None

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(credentials_path))
            firebase_admin.initialize_app(
                cred,
                {"projectId": settings.firebase_project_id},
            )
        _db = firestore.client()
        return _db
    except Exception as exc:
        logger.warning("Firebase initialisation failed: %s — Firestore features disabled.", exc)
        return None
