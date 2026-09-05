from functools import lru_cache
from typing import Any, Dict, List

from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.firebase.firebase_app import initialize_firebase_app, initialize_firestore
from app.repositories.base import BaseRepository
from app.repositories.firestore_repository import FirestoreRepository


class AuthenticatedUser(BaseModel):
    uid: str
    email: str | None = None
    name: str | None = None


class UserScopedRepository:
    """Repository wrapper that stores user data under users/{uid}/..."""

    def __init__(self, repository: BaseRepository, user_id: str) -> None:
        self.repository = repository
        self.user_id = user_id.replace("/", "_")

    def _collection(self, collection: str) -> str:
        return f"users/{self.user_id}/{collection}"

    def set_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.repository.set_document(
            self._collection(collection),
            document_id,
            {**data, "user_id": self.user_id},
        )

    def get_document(self, collection: str, document_id: str) -> Dict[str, Any] | None:
        return self.repository.get_document(self._collection(collection), document_id)

    def delete_document(self, collection: str, document_id: str) -> bool:
        return self.repository.delete_document(self._collection(collection), document_id)

    def list_documents(self, collection: str, limit: int = 50, order_by: str | None = None, descending: bool = True) -> List[Dict[str, Any]]:
        return self.repository.list_documents(self._collection(collection), limit=limit, order_by=order_by, descending=descending)


@lru_cache
def get_repository() -> BaseRepository:
    settings: Settings = get_settings()
    db = initialize_firestore(settings)
    return FirestoreRepository(db)


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Sign in and send a Firebase ID token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        initialize_firebase_app(settings)
        decoded_token = auth.verify_id_token(token, check_revoked=True)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid or expired Firebase ID token. Sign in again and confirm the "
                f"frontend Firebase project matches backend FIREBASE_PROJECT_ID={settings.firebase_project_id}."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    uid = decoded_token.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token does not contain a user id.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(
        uid=uid,
        email=decoded_token.get("email"),
        name=decoded_token.get("name"),
    )


def get_user_repository(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: BaseRepository = Depends(get_repository),
) -> BaseRepository:
    return UserScopedRepository(repository, current_user.uid)
