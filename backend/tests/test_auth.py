
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def post_with_csrf(url: str, payload: dict):
    """Send a POST request with a valid CSRF cookie and header."""
    csrf_response = client.get("/auth/csrf")

    assert csrf_response.status_code == 200

    csrf_token = csrf_response.json()["csrf_token"]

    return client.post(
        url,
        json=payload,
        headers={"X-CSRF-Token": csrf_token},
    )


def test_csrf_endpoint_returns_token():
    response = client.get("/auth/csrf")

    assert response.status_code == 200
    assert response.json().get("csrf_token")
    assert "dermai_csrf_token" in response.cookies


def test_post_without_csrf_token_is_rejected():
    response = client.post("/auth/logout")

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF token missing"


def test_post_with_invalid_csrf_token_is_rejected():
    response = client.post(
        "/auth/logout",
        cookies={"dermai_csrf_token": "invalid-token"},
        headers={"X-CSRF-Token": "invalid-token"},
    )

    assert response.status_code == 403


def test_register_user_success():
    payload = {
        "username": f"testuser_{uuid4().hex[:8]}",
        "email": f"{uuid4().hex[:10]}@example.com",
        "password": "TestPassword123!",
    }

    response = post_with_csrf("/auth/register", payload)

    assert response.status_code == 201

    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "role" in data
    assert "created_at" in data
    assert "password" not in data


def test_register_user_invalid_email():
    payload = {
        "username": "testuser",
        "email": "not-an-email",
        "password": "TestPassword123!",
    }

    response = post_with_csrf("/auth/register", payload)

    assert response.status_code == 422


def test_login_invalid_credentials():
    payload = {
        "email": f"{uuid4().hex[:10]}@example.com",
        "password": "WrongPassword123!",
    }

    response = post_with_csrf("/auth/login", payload)

    assert response.status_code in (400, 401)
    assert "dermai_access_token" not in response.cookies
