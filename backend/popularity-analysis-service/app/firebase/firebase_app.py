from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

from app.core.config import Settings


def initialize_firestore(settings: Settings):
    """Initialize Firebase Admin SDK and return a Firestore client.

    The function supports either:
    1. Service account JSON configured by FIREBASE_CREDENTIALS_PATH.
    2. Application default credentials if no service account path exists.

    In local development, prefer FIREBASE_MOCK_MODE=true to avoid requiring credentials.
    """

    if firebase_admin._apps:
        return firestore.client()

    options = {}
    if settings.firebase_project_id:
        options["projectId"] = settings.firebase_project_id

    cred = None
    if settings.firebase_credentials_path:
        path = Path(settings.firebase_credentials_path)
        if path.exists():
            cred = credentials.Certificate(str(path))

    if cred is None:
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred, options=options)
    return firestore.client()
