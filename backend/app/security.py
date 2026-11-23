import os
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from dotenv import load_dotenv

# This module reads secrets at import time, and it is imported (through the
# routes) before main.py reaches its own load_dotenv(). Loading the .env here
# makes it independent of import order. load_dotenv() never overrides
# variables that are already set in the real environment.
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

# The algorithm is fixed in code on purpose. Letting an environment variable
# choose it would let a misconfiguration weaken token verification.
ALGORITHM = "HS256"

MIN_SECRET_KEY_BYTES = 32  # RFC 7518, section 3.2 (HS256)

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não configurada.")

if len(SECRET_KEY.encode("utf-8")) < MIN_SECRET_KEY_BYTES:
    raise RuntimeError(
        f"SECRET_KEY muito curta: use pelo menos {MIN_SECRET_KEY_BYTES} bytes."
    )

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
except ValueError as exc:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES deve ser um número inteiro."
    ) from exc

if not 1 <= ACCESS_TOKEN_EXPIRE_MINUTES <= 24 * 60:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES deve estar entre 1 e 1440."
    )

password_hasher = PasswordHasher()

# A real Argon2 hash of a throw-away password. It is verified when a login
# names an account that does not exist, so that "unknown e-mail" and "wrong
# password" take the same time and cannot be told apart by timing.
_DUMMY_PASSWORD_HASH = password_hasher.hash("not-a-real-password")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_password_against_dummy(password: str) -> bool:
    """Spend the same time as a real check. Always returns False."""
    verify_password(password, _DUMMY_PASSWORD_HASH)
    return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    now = datetime.now(timezone.utc)

    # Set after the copy so the caller cannot override them.
    to_encode.update(
        {
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        }
    )

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        # Without "require", PyJWT accepts a token that has no "exp" at all,
        # i.e. one that never expires.
        options={"require": ["exp", "sub"]},
    )
