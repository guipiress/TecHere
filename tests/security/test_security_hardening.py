import runpy
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import dotenv
import jwt
import pytest

from backend.app.security import (
    ALGORITHM,
    MAX_CONCURRENT_HASHES,
    SECRET_KEY,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    verify_password_against_dummy,
)

SECURITY_MODULE = (
    Path(__file__).resolve().parents[2] / "backend" / "app" / "security.py"
)


def _future():
    return datetime.now(timezone.utc) + timedelta(minutes=5)


# --- token validation --------------------------------------------------------

def test_algorithm_is_fixed_in_code():
    assert ALGORITHM == "HS256"


def test_token_carries_iat_and_exp():
    payload = decode_access_token(create_access_token({"sub": "42"}))

    assert "iat" in payload
    assert payload["exp"] > payload["iat"]


def test_caller_cannot_override_exp():
    token = create_access_token(
        {"sub": "42", "exp": datetime(2999, 1, 1, tzinfo=timezone.utc)}
    )

    payload = decode_access_token(token)

    assert payload["exp"] < datetime(2100, 1, 1, tzinfo=timezone.utc).timestamp()


def test_token_without_exp_is_rejected():
    # Signed with the right key, but it would never expire.
    token = jwt.encode({"sub": "42"}, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_token_without_sub_is_rejected():
    token = jwt.encode({"exp": _future()}, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_unsigned_none_algorithm_token_is_rejected():
    token = jwt.encode(
        {"sub": "42", "exp": _future()}, "", algorithm="none"
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_token_signed_with_another_hmac_algorithm_is_rejected():
    token = jwt.encode(
        {"sub": "42", "exp": _future()}, SECRET_KEY, algorithm="HS512"
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token({"sub": "42"})
    header, payload, signature = token.split(".")
    # Change a character that carries real information (not the padding bits
    # of the last one) and make sure it really is different.
    replacement = "A" if signature[-3] != "A" else "B"
    tampered = ".".join(
        [header, payload, signature[:-3] + replacement + signature[-2:]]
    )
    assert tampered != token

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered)


# --- password helpers ----------------------------------------------------------

def test_malformed_hash_is_treated_as_wrong_password():
    assert verify_password("anything", "this-is-not-an-argon2-hash") is False


def test_dummy_check_runs_a_real_verification_and_returns_false():
    with patch("backend.app.security.verify_password") as mock_verify:
        result = verify_password_against_dummy("whatever")

    assert result is False
    mock_verify.assert_called_once()
    assert mock_verify.call_args.args[0] == "whatever"
    assert mock_verify.call_args.args[1].startswith("$argon2")


def test_password_hashing_concurrency_is_bounded():
    # Each real Argon2 hash needs ~64 MiB; without a cap a burst of requests
    # would hold (threads x 64 MiB) at once.
    state = {"running": 0, "peak": 0}
    lock = threading.Lock()

    class SlowHasher:
        def _work(self):
            with lock:
                state["running"] += 1
                state["peak"] = max(state["peak"], state["running"])
            time.sleep(0.03)
            with lock:
                state["running"] -= 1

        def hash(self, password):
            self._work()
            return "$argon2id$fake"

        def verify(self, password_hash, password):
            self._work()
            return True

    with patch("backend.app.security.password_hasher", SlowHasher()):
        threads = [
            threading.Thread(
                target=hash_password if i % 2 else verify_password,
                args=("x",) if i % 2 else ("x", "hash"),
            )
            for i in range(24)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    assert 1 <= state["peak"] <= MAX_CONCURRENT_HASHES


# --- start-up configuration (executed in a fresh namespace) -------------------

def _run_security(monkeypatch, **env):
    # Neutralise python-dotenv so a developer's real .env cannot interfere.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)

    for name in ("SECRET_KEY", "ACCESS_TOKEN_EXPIRE_MINUTES", "ALGORITHM"):
        monkeypatch.delenv(name, raising=False)

    for name, value in env.items():
        monkeypatch.setenv(name, value)

    return runpy.run_path(str(SECURITY_MODULE))


def test_startup_fails_without_secret_key(monkeypatch):
    with pytest.raises(RuntimeError, match="não configurada"):
        _run_security(monkeypatch)


def test_startup_fails_with_short_secret_key(monkeypatch):
    with pytest.raises(RuntimeError, match="muito curta"):
        _run_security(monkeypatch, SECRET_KEY="x" * 31)


def test_startup_accepts_a_32_byte_key(monkeypatch):
    namespace = _run_security(monkeypatch, SECRET_KEY="x" * 32)

    assert namespace["ALGORITHM"] == "HS256"


def test_algorithm_environment_variable_is_ignored(monkeypatch):
    namespace = _run_security(
        monkeypatch, SECRET_KEY="x" * 32, ALGORITHM="none"
    )

    assert namespace["ALGORITHM"] == "HS256"


@pytest.mark.parametrize("value", ["abc", "0", "-5", "1441"])
def test_startup_rejects_invalid_token_lifetime(monkeypatch, value):
    with pytest.raises(RuntimeError):
        _run_security(
            monkeypatch,
            SECRET_KEY="x" * 32,
            ACCESS_TOKEN_EXPIRE_MINUTES=value,
        )
