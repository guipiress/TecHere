import logging
from unittest.mock import patch

FAKE_USER = {
    "id": 10,
    "name": "Usuário Teste",
    "email": "teste@example.com",
    "password_hash": "hash-ficticio",
    "role": "CUSTOMER",
    "is_active": True,
}

AUTH = "backend.app.api.routes.auth"


def _login(client, email="teste@example.com", password="SenhaForte123!"):
    return client.post(
        "/auth/login", json={"email": email, "password": password}
    )


def _fail(client, times, email="teste@example.com"):
    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=False):
            for _ in range(times):
                assert _login(client, email).status_code == 401


# --- timing: unknown e-mail must cost the same as a wrong password -----------

def test_unknown_email_still_performs_a_password_check(client):
    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=None):
        with patch(
            f"{AUTH}.verify_password_against_dummy", return_value=False
        ) as mock_dummy:
            with patch(f"{AUTH}.verify_password") as mock_verify:
                response = _login(client, "ghost@example.com", "qualquer-coisa")

    assert response.status_code == 401
    mock_dummy.assert_called_once_with("qualquer-coisa")
    mock_verify.assert_not_called()


def test_known_email_does_not_use_the_dummy_check(client):
    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=True):
            with patch(
                f"{AUTH}.verify_password_against_dummy"
            ) as mock_dummy:
                response = _login(client)

    assert response.status_code == 200
    mock_dummy.assert_not_called()


def test_every_failure_returns_the_same_response(client):
    inactive = {**FAKE_USER, "is_active": False}
    bodies = set()

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=None):
        r = _login(client, "ghost@example.com")
        bodies.add((r.status_code, r.text))

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=False):
            r = _login(client, "a@example.com")
            bodies.add((r.status_code, r.text))

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=inactive):
        with patch(f"{AUTH}.verify_password", return_value=True):
            r = _login(client, "b@example.com")
            bodies.add((r.status_code, r.text))

    assert len(bodies) == 1


# --- rate limiting -----------------------------------------------------------

def test_account_is_blocked_after_five_failures(client):
    _fail(client, 5)

    with patch(
        f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER
    ) as mock_fetch:
        response = _login(client)

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    # Rejected before the database or the hash function were touched.
    mock_fetch.assert_not_called()


def test_correct_password_is_refused_while_blocked(client):
    _fail(client, 5)

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=True):
            response = _login(client)

    assert response.status_code == 429


def test_blocking_one_account_does_not_block_another(client):
    _fail(client, 5, email="victim@example.com")

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=True):
            response = _login(client, "other@example.com")

    assert response.status_code == 200


def test_successful_login_resets_the_account_counter(client):
    _fail(client, 4)

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=True):
            assert _login(client).status_code == 200

    # Four more failures would reach nine in total without the reset.
    _fail(client, 4)

    with patch(f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER):
        with patch(f"{AUTH}.verify_password", return_value=False):
            assert _login(client).status_code == 401


def test_address_is_blocked_after_twenty_failures_across_accounts(client):
    for i in range(20):
        _fail(client, 1, email=f"user{i}@example.com")

    with patch(
        f"{AUTH}.fetch_user_by_email_for_auth", return_value=FAKE_USER
    ) as mock_fetch:
        response = _login(client, "brand-new@example.com")

    assert response.status_code == 429
    mock_fetch.assert_not_called()


# --- logging -----------------------------------------------------------------

def test_failed_login_is_logged_without_the_email(client, caplog):
    with caplog.at_level(logging.WARNING, logger="techere.auth"):
        _fail(client, 1, email="secret.person@example.com")

    assert "failed login" in caplog.text
    assert "secret.person@example.com" not in caplog.text
