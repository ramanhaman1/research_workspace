
import os
import secrets
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from services.application_api import main as application_api
from services.resource_service import database
from services.resource_service.main import app as resource_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Isolated database and internal signing key
    secret = secrets.token_urlsafe(48)
    monkeypatch.setenv("RW_INTERNAL_JWT_SECRET", secret)

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "integration.db"
    )
    database.init_db()

    # Route Application API HTTP requests to Resource Service
    # directly in the test process.
    def resource_client(*args, **kwargs):
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=resource_app),
            timeout=kwargs.get("timeout", 5.0),
        )

    monkeypatch.setattr(
        application_api,
        "httpx",
        SimpleNamespace(
            AsyncClient=resource_client,
            RequestError=httpx.RequestError,
        ),
    )

    with TestClient(application_api.app) as test_client:
        yield test_client


def login(client, username):
    password_variables = {
        "ali": "RW_ALI_PASSWORD",
        "Raman": "RW_RAMAN_PASSWORD",
        "admin": "RW_ADMIN_PASSWORD",
    }

    response = client.post(
        "/login",
        json={
            "username": username,
            "password": os.environ[password_variables[username]],
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_ali_dataset(client):
    headers = login(client, "ali")

    response = client.post(
        "/datasets",
        json={
            "name": "Student Survey",
            "rows": [
                {"participant": 1, "score": 80},
                {"participant": 2, "score": 92},
            ],
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_ali_can_create_and_read(client):
    dataset_id = create_ali_dataset(client)

    headers = login(client, "ali")

    response = client.get(
        f"/datasets/{dataset_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["owner_username"] == "ali"
    assert response.json()["name"] == "Student Survey"


def test_raman_cannot_read_alis_dataset(client):
    dataset_id = create_ali_dataset(client)

    headers = login(client, "Raman")

    response = client.get(
        f"/datasets/{dataset_id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset not found"


def test_access_without_token(client):
    response = client.get("/datasets/1")

    assert response.status_code == 401


def test_admin_cannot_create_dataset(client):
    headers = login(client, "admin")

    response = client.post(
        "/datasets",
        json={
            "name": "Admin Test",
            "rows": [{"value": 100}],
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_invalid_user_token(client):
    response = client.get(
        "/datasets/1",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401
