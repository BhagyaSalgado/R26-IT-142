import logging

from fastapi import Header, HTTPException, status
from firebase_admin import auth
from pydantic import BaseModel

from app.core.config import get_settings
from app.firebase.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)


class AuthenticatedUser(BaseModel):
    uid: str = "anonymous"
    email: str | None = None
    name: str | None = None
    id_token: str = ""


def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        return _anonymous_or_unauthorized("Authentication credentials are required.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return _anonymous_or_unauthorized("Authentication credentials are required.")

    try:
        # Ensure the Firebase Admin app is initialized before token verification.
        get_firestore_client()
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        uid = decoded_token.get("uid")
        if not uid:
            return _anonymous_or_unauthorized("Authentication token does not contain a user identifier.")
        return AuthenticatedUser(
            uid=uid,
            email=decoded_token.get("email"),
            name=decoded_token.get("name"),
            id_token=token,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Token verification failed: %s", exc)
        return _anonymous_or_unauthorized("Invalid or expired authentication token.")


def _anonymous_or_unauthorized(detail: str) -> AuthenticatedUser:
    """Allow anonymous access only when explicitly enabled for local development."""
    if get_settings().allow_anonymous_access:
        return AuthenticatedUser(uid="anonymous", id_token="")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
