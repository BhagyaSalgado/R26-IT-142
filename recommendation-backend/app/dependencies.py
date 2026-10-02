import logging
from fastapi import Header
from firebase_admin import auth
from pydantic import BaseModel

from app.firebase.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)


class AuthenticatedUser(BaseModel):
    uid: str = "anonymous"
    email: str | None = None
    name: str | None = None
    id_token: str = ""


def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        return AuthenticatedUser(uid="anonymous", id_token="")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return AuthenticatedUser(uid="anonymous", id_token="")

    try:
        # Ensures the Firebase Admin app is initialized before token verification.
        get_firestore_client()
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        uid = decoded_token.get("uid") or "anonymous"
        return AuthenticatedUser(
            uid=uid,
            email=decoded_token.get("email"),
            name=decoded_token.get("name"),
            id_token=token,
        )
    except Exception as exc:
        logger.warning("Token verification failed: %s — continuing as anonymous", exc)
        return AuthenticatedUser(uid="anonymous", id_token="")
