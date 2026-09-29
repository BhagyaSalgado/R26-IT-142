import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import settings

_db = None


def get_firestore_client():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(settings.FIREBASE_CREDENTIALS_PATH))
            firebase_admin.initialize_app(
                cred,
                {"projectId": settings.FIREBASE_PROJECT_ID},
            )
        _db = firestore.client()
    return _db
