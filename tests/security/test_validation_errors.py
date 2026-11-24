"""Validation errors must not repeat what the client sent (passwords!)."""

SHORT_PASSWORD = "Sh0rt!"


def test_rejected_password_is_not_echoed_back_on_signup(client):
    response = client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": SHORT_PASSWORD,
        },
    )

    assert response.status_code == 422
    assert SHORT_PASSWORD not in response.text


def test_rejected_login_does_not_echo_the_password(client):
    response = client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "Sup3rS3cretValue"},
    )

    assert response.status_code == 422
    assert "Sup3rS3cretValue" not in response.text


def test_validation_errors_still_tell_the_client_which_field_failed(client):
    response = client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": SHORT_PASSWORD,
        },
    )

    errors = response.json()["detail"]

    assert errors[0]["loc"] == ["body", "password"]
    assert set(errors[0]) == {"type", "loc", "msg"}


def test_malformed_json_returns_422_without_echoing_the_body(client):
    response = client.post(
        "/auth/login",
        content='{"email": "a@example.com", "password": "Leaky-P4ss" ',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert "Leaky-P4ss" not in response.text
