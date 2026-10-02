from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.dependencies import get_current_user


def test_missing_bearer_token_is_rejected_by_default():
    with patch("app.dependencies.get_settings", return_value=SimpleNamespace(allow_anonymous_access=False)):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_anonymous_access_requires_explicit_opt_in():
    with patch("app.dependencies.get_settings", return_value=SimpleNamespace(allow_anonymous_access=True)):
        user = get_current_user(None)

    assert user.uid == "anonymous"
    assert user.id_token == ""


def test_valid_firebase_token_returns_authenticated_user():
    decoded = {"uid": "user-123", "email": "user@example.com", "name": "Test User"}
    with (
        patch("app.dependencies.get_firestore_client"),
        patch("app.dependencies.auth.verify_id_token", return_value=decoded) as verify,
    ):
        user = get_current_user("Bearer valid-token")

    verify.assert_called_once_with("valid-token", check_revoked=True)
    assert user.uid == "user-123"
    assert user.email == "user@example.com"
    assert user.name == "Test User"
    assert user.id_token == "valid-token"


def test_invalid_firebase_token_is_rejected():
    with (
        patch("app.dependencies.get_settings", return_value=SimpleNamespace(allow_anonymous_access=False)),
        patch("app.dependencies.get_firestore_client"),
        patch("app.dependencies.auth.verify_id_token", side_effect=ValueError("invalid token")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("Bearer invalid-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired authentication token."
