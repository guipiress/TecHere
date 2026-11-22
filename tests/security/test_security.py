from datetime import datetime, timedelta, timezone
from backend.app.security import hash_password, verify_password
import jwt
import pytest

from backend.app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "42"})

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert "exp" in payload


def test_decode_token_with_invalid_signature():
    token = jwt.encode(
        {"sub": "42"},
        "outra-chave-secreta",
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)


def test_decode_expired_token():
    expired_token = jwt.encode(
        {
            "sub": "42",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)



def test_hash_password():
    password = "TecHere@2026"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2")


def test_verify_correct_password():
    password = "TecHere@2026"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_incorrect_password():
    password_hash = hash_password("TecHere@2026")

    assert verify_password("SenhaErrada@2026", password_hash) is False

