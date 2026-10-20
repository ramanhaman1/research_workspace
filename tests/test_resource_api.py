
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from services.resource_service import database
from services.resource_service.main import app


@pytest.fixture
def api(tmp_path, monkeypatch):
    # Use a temporary database and signing key
    secret = secrets.token_urlsafe(48)

    monkeypatch.setenv("RW_INTERNAL_JWT_SECRET", secret)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")

    database.init_db()

    with TestClient(app) as client:
        yield client, secret


def make_token(
    secret,
    username="ali",
    scope="datasets:create",
    dataset_id=None,
    role="researcher",
    expires_in=300,
):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": username,
        "role": role,
        "scope": scope,
        "azp": "application-api",
        "iss": "research-workspace",
        "aud": "resource-service",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }

    if dataset_id is not None:
        payload["dataset_id"] = dataset_id

    return jwt.encode(payload, secret, algorithm="HS256")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def create_test_dataset(client, secret, username="ali"):
    token = make_token(secret, username=username)

    response = client.post(
        "/datasets",
        json={
            "name": "Student Survey",
            "rows": [{"participant": 1, "score": 80}],
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_missing_token(api):
    client, _ = api

    response = client.get("/datasets/1")
    assert response.status_code == 401

    response = client.post(
        "/datasets",
        json={"name": "Test", "rows": [{"value": 1}]},
    )
    assert response.status_code == 401


def test_create_dataset(api):
    client, secret = api

    dataset_id = create_test_dataset(client, secret)

    assert isinstance(dataset_id, int)


def test_read_own_dataset(api):
    client, secret = api

    dataset_id = create_test_dataset(client, secret)

    token = make_token(
        secret,
        scope="datasets:read",
        dataset_id=dataset_id,
    )

    response = client.get(
        f"/datasets/{dataset_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["owner_username"] == "ali"


def test_other_user_denied(api):
    client, secret = api

    dataset_id = create_test_dataset(client, secret, "ali")

    token = make_token(
        secret,
        username="Raman",
        scope="datasets:read",
        dataset_id=dataset_id,
    )

    response = client.get(
        f"/datasets/{dataset_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_wrong_scope_denied(api):
    client, secret = api

    token = make_token(secret, scope="datasets:read")

    response = client.post(
        "/datasets",
        json={"name": "Test", "rows": [{"value": 1}]},
        headers=auth_header(token),
    )

    assert response.status_code == 403


def test_dataset_scope_denied(api):
    client, secret = api

    first_id = create_test_dataset(client, secret)
    second_id = create_test_dataset(client, secret)

    token = make_token(
        secret,
        scope="datasets:read",
        dataset_id=first_id,
    )

    response = client.get(
        f"/datasets/{second_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 403


def test_expired_token(api):
    client, secret = api

    token = make_token(secret, expires_in=-60)

    response = client.post(
        "/datasets",
        json={"name": "Test", "rows": [{"value": 1}]},
        headers=auth_header(token),
    )

    assert response.status_code == 401


def test_admin_cannot_create_dataset(api):
    client, secret = api

    token = make_token(secret, username="admin", role="admin")

    response = client.post(
        "/datasets",
        json={"name": "Test", "rows": [{"value": 1}]},
        headers=auth_header(token),
    )

    assert response.status_code == 403


def test_invalid_token(api):
    client, _ = api

    response = client.get(
        "/datasets/1",
        headers=auth_header("invalid-token"),
    )

    assert response.status_code == 401
