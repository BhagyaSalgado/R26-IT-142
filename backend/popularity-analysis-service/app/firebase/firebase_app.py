from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from google.auth.exceptions import DefaultCredentialsError

from app.core.config import Settings


def initialize_firebase_app(settings: Settings):
    """Initialize Firebase Admin SDK and return the default app.

    The function supports either:
    1. Service account JSON configured by FIREBASE_CREDENTIALS_PATH.
    2. Application default credentials if no service account path exists.

    Firebase Auth token verification and Firestore both use this app.
    """

    if firebase_admin._apps:
        return firebase_admin.get_app()

    options = {"projectId": settings.firebase_project_id}

    cred = None
    if settings.firebase_credentials_path:
        path = Path(settings.firebase_credentials_path)
        if path.exists():
            cred = credentials.Certificate(str(path))

    if cred is None:
        try:
            cred = credentials.ApplicationDefault()
        except DefaultCredentialsError as exc:
            raise RuntimeError(
                "Firebase Admin credentials are required. Add serviceAccountKey.json "
                "to popularity_analysis_service or set FIREBASE_CREDENTIALS_PATH to a "
                "valid Firebase service account JSON file."
            ) from exc

    return firebase_admin.initialize_app(cred, options=options)


def initialize_firestore(settings: Settings):
    """Initialize Firebase Admin SDK and return a Firestore client.

    In local development, prefer FIREBASE_MOCK_MODE=true to avoid requiring credentials
    for Firestore persistence. Authenticated API routes still verify Firebase ID tokens.
    """

    initialize_firebase_app(settings)
    return firestore.client()
