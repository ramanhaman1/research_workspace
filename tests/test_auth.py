
import os

from fastapi.testclient import TestClient
from services.application_api.main import app

client = TestClient(app)


def test_login_success():
    response = client.post("/login", json={
        "username": "ali",
        "password": os.environ["RW_ALI_PASSWORD"]
    })

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_access_with_valid_token():
    login = client.post("/login", json={
        "username": "ali",
        "password": os.environ["RW_ALI_PASSWORD"]
    })

    token = login.json()["access_token"]

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "username": "ali",
        "role": "researcher"
    }


def test_access_without_token():
    response = client.get("/me")

    assert response.status_code == 401


def test_login_wrong_password():
    response = client.post("/login", json={
        "username": "ali",
        "password": "incorrect-password"
    })

    assert response.status_code == 401


def test_invalid_token():
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401
