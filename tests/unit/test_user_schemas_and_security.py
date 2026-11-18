from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserRead
from app.security import hash_password, verify_password


def test_user_create_valid():
    u = UserCreate(username="hermann_t", email="h@example.com", password="Secret123")
    assert u.username == "hermann_t"


@pytest.mark.parametrize(
    "field, value",
    [
        ("username", "ab"),
        ("username", "bad name!"),
        ("email", "not-an-email"),
        ("password", "short1A"),
        ("password", "alllowercase1"),
        ("password", "ALLUPPERCASE1"),
        ("password", "NoDigitsHere"),
    ],
)
def test_user_create_invalid(field, value):
    payload = {"username": "valid_user", "email": "v@example.com", "password": "Secret123", field: value}
    with pytest.raises(ValidationError):
        UserCreate(**payload)


def test_user_read_excludes_password_hash():
    obj = SimpleNamespace(id=1, username="alice", email="alice@example.com",
                          password_hash="$2b$12$...", created_at=datetime.now(timezone.utc))
    data = UserRead.model_validate(obj).model_dump()
    assert "password_hash" not in data and "password" not in data


def test_hash_and_verify_password():
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert verify_password("Secret123", hashed)
    assert not verify_password("wrong", hashed)
