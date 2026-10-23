import os
import time
import jwt

import csv
import io
import secrets

import httpx
import pytest
from fastapi.testclient import TestClient

from services.application_api.internal_tokens import (
    create_internal_token,
)
from services.processing_service.main import (
    app as processing_app,
    get_resource_client,
)
from services.resource_service import database
from services.resource_service.main import app as resource_app
from services.resource_service import database as resource_database


@pytest.fixture
def export_client(tmp_path, monkeypatch):
    secret = secrets.token_urlsafe(48)
    api_key = secrets.token_urlsafe(48)

    monkeypatch.setenv("RW_INTERNAL_JWT_SECRET", secret)
    monkeypatch.setenv("RW_PROCESSING_API_KEY", api_key)

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "processing_export.db",
    )
    database.init_db()

    # Create a dataset owned by ali.
    create_token = create_internal_token(
        username="ali",
        role="researcher",
        scope="datasets:create",
    )

    with TestClient(resource_app) as resource_client:
        response = resource_client.post(
            "/datasets",
            json={
                "name": "Student Survey",
                "rows": [
                    {"participant": 1, "score": 80},
                    {"participant": 2, "score": 92},
                ],
            },
            headers={
                "Authorization": f"Bearer {create_token}"
            },
        )

    assert response.status_code == 201

    dataset_id = response.json()["id"]

    # Send Processing Service requests to the real
    # Resource Service app without starting Uvicorn.
    async def override_resource_client():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=resource_app),
            base_url="http://127.0.0.1:8001",
        ) as client:
            yield client

    processing_app.dependency_overrides[
        get_resource_client
    ] = override_resource_client

    try:
        with TestClient(processing_app) as client:
            yield client, dataset_id, api_key
    finally:
        processing_app.dependency_overrides.pop(
            get_resource_client,
            None,
        )


def make_token(username, dataset_id, scope="datasets:export"):
    return create_internal_token(
        username=username,
        role="researcher",
        scope=scope,
        dataset_id=dataset_id,
    )


def auth_headers(api_key, token=None):
    headers = {"X-Processing-Key": api_key}

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def test_authorized_csv_export(export_client):
    client, dataset_id, api_key = export_client
    token = make_token("ali", dataset_id)

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")

    rows = list(csv.reader(io.StringIO(response.text)))

    assert rows == [
        ["participant", "score"],
        ["1", "80"],
        ["2", "92"],
    ]


def test_export_without_processing_key(export_client):
    client, dataset_id, _ = export_client
    token = make_token("ali", dataset_id)

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_export_without_token(export_client):
    client, dataset_id, api_key = export_client

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key),
    )

    assert response.status_code == 401


def test_export_wrong_dataset_denied(export_client):
    client, dataset_id, api_key = export_client

    token = make_token("ali", dataset_id + 1)

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 403


def test_export_other_user_denied(export_client):
    client, dataset_id, api_key = export_client

    token = make_token("Raman", dataset_id)

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 404


def test_export_wrong_scope_denied(export_client):
    client, dataset_id, api_key = export_client

    token = make_token(
        "ali",
        dataset_id,
        scope="datasets:read",
    )

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 403


def test_expired_export_token_denied(export_client):
    client, dataset_id, api_key = export_client

    secret = os.environ["RW_INTERNAL_JWT_SECRET"]
    token = make_token("ali", dataset_id)

    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="resource-service",
        issuer="research-workspace",
    )

    # Create a correctly signed but expired token.
    payload["exp"] = int(time.time()) - 60

    expired_token = jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, expired_token),
    )

    assert response.status_code == 403


def test_invalid_token_signature_denied(export_client):
    client, dataset_id, api_key = export_client

    secret = os.environ["RW_INTERNAL_JWT_SECRET"]
    token = make_token("ali", dataset_id)

    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="resource-service",
        issuer="research-workspace",
    )

    # Sign the token with a different key.
    invalid_token = jwt.encode(
        payload,
        secrets.token_urlsafe(48),
        algorithm="HS256",
    )

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, invalid_token),
    )

    assert response.status_code == 403


def test_invalid_dataset_id_rejected(export_client):
    client, dataset_id, api_key = export_client
    token = make_token("ali", dataset_id)

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": 0},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 422


def test_resource_service_unavailable(export_client):
    client, dataset_id, api_key = export_client
    token = make_token("ali", dataset_id)

    def connection_failure(request):
        raise httpx.ConnectError(
            "Simulated connection failure",
            request=request,
        )

    async def unavailable_client():
        transport = httpx.MockTransport(connection_failure)

        async with httpx.AsyncClient(
            transport=transport
        ) as resource_client:
            yield resource_client

    processing_app.dependency_overrides[
        get_resource_client
    ] = unavailable_client

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Resource Service unavailable"
    )

def test_mismatched_resource_response_rejected(export_client):
    client, dataset_id, api_key = export_client
    token = make_token("ali", dataset_id)

    def wrong_dataset_response(request):
        return httpx.Response(
            status_code=200,
            json={
                "dataset_id": dataset_id + 1,
                "rows": [{"participant": 1, "score": 80}],
            },
            request=request,
        )

    async def incorrect_resource_client():
        transport = httpx.MockTransport(wrong_dataset_response)

        async with httpx.AsyncClient(
            transport=transport
        ) as resource_client:
            yield resource_client

    processing_app.dependency_overrides[
        get_resource_client
    ] = incorrect_resource_client

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_id},
        headers=auth_headers(api_key, token),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Invalid Resource Service response"
    )

def test_cross_service_dataset_scope(export_client):
    client, dataset_a, api_key = export_client

    dataset_b = resource_database.create_dataset(
        owner_username="ali",
        name="Second dataset",
        rows=[{"value": "DATASET_B_MARKER"}],
    )

    assert dataset_a != dataset_b

    token = make_token("ali", dataset_a)

    response = client.post(
        "/internal/export-dataset",
        json={"dataset_id": dataset_b},
        headers=auth_headers(api_key, token),
    )

    print("V4 cross-service evidence:", response.status_code)

    if response.status_code == 200:
        assert "DATASET_B_MARKER" in response.text

    assert response.status_code == 403
    