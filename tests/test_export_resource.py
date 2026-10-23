
import secrets

import jwt
import pytest
from fastapi.testclient import TestClient

from services.application_api.internal_tokens import (
    create_internal_token,
)
from services.resource_service import database
from services.resource_service.main import app
from services.resource_service.database import create_dataset


@pytest.fixture
def export_setup(tmp_path, monkeypatch):
    secret = secrets.token_urlsafe(48)

    monkeypatch.setenv(
        "RW_INTERNAL_JWT_SECRET",
        secret,
    )

    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "export_test.db",
    )

    database.init_db()

    with TestClient(app) as client:
        create_token = create_internal_token(
            username="ali",
            role="researcher",
            scope="datasets:create",
        )

        response = client.post(
            "/datasets",
            json={
                "name": "Student Survey",
                "rows": [
                    {"participant": 1, "score": 80},
                ],
            },
            headers={
                "Authorization": f"Bearer {create_token}"
            },
        )

        assert response.status_code == 201

        dataset_id = response.json()["id"]

        yield client, dataset_id, secret


def export_token(username, dataset_id):
    return create_internal_token(
        username=username,
        role="researcher",
        scope="datasets:export",
        dataset_id=dataset_id,
    )


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_authorized_export(export_setup):
    client, dataset_id, _ = export_setup

    token = export_token("ali", dataset_id)

    response = client.get(
        f"/internal/exports/{dataset_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 200, response.json()
    assert response.json()["dataset_id"] == dataset_id
    assert response.json()["rows"] == [
        {"participant": 1, "score": 80}
    ]


def test_export_without_token(export_setup):
    client, dataset_id, _ = export_setup

    response = client.get(
        f"/internal/exports/{dataset_id}"
    )

    assert response.status_code == 401


def test_export_wrong_scope(export_setup):
    client, dataset_id, _ = export_setup

    token = create_internal_token(
        username="ali",
        role="researcher",
        scope="datasets:read",
        dataset_id=dataset_id,
    )

    response = client.get(
        f"/internal/exports/{dataset_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 403

def test_export_wrong_dataset(export_setup):
    client, dataset_a, _ = export_setup

    dataset_b = create_dataset(
        owner_username="ali",
        name="Second dataset",
        rows=[{"value": "DATASET_B"}],
    )

    assert dataset_a != dataset_b

    token = export_token("ali", dataset_a)

    response = client.get(
        f"/internal/exports/{dataset_b}",
        headers=auth_header(token),
    )

    print("V4 evidence:", response.status_code)

    assert response.status_code == 403


def test_export_other_user_denied(export_setup):
    client, dataset_id, _ = export_setup

    token = export_token("Raman", dataset_id)

    response = client.get(
        f"/internal/exports/{dataset_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 404, response.json()


def test_export_wrong_delegation(export_setup):
    client, dataset_id, secret = export_setup

    token = export_token("ali", dataset_id)

    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="resource-service",
        issuer="research-workspace",
    )

    payload["delegate_to"] = "unknown-service"

    invalid_delegation = jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )

    response = client.get(
        f"/internal/exports/{dataset_id}",
        headers=auth_header(invalid_delegation),
    )

    assert response.status_code == 403
