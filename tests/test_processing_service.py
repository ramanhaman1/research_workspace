
import csv
import io
import secrets

import pytest
from fastapi.testclient import TestClient

from services.processing_service.main import app


@pytest.fixture
def client(monkeypatch):
    api_key = secrets.token_urlsafe(48)

    monkeypatch.setenv(
        "RW_PROCESSING_API_KEY",
        api_key,
    )

    with TestClient(app) as test_client:
        yield test_client, api_key


def test_processing_health(client):
    test_client, _ = client

    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_csv_export(client):
    test_client, api_key = client

    response = test_client.post(
        "/internal/render-csv",
        json={
            "rows": [
                {"participant": 1, "score": 80},
                {"participant": 2, "score": 92},
            ]
        },
        headers={"X-Processing-Key": api_key},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    parsed = list(csv.reader(io.StringIO(response.text)))

    assert parsed == [
        ["participant", "score"],
        ["1", "80"],
        ["2", "92"],
    ]


def test_csv_export_without_key(client):
    test_client, _ = client

    response = test_client.post(
        "/internal/render-csv",
        json={"rows": [{"value": 100}]},
    )

    assert response.status_code == 401


def test_csv_export_invalid_key(client):
    test_client, _ = client

    response = test_client.post(
        "/internal/render-csv",
        json={"rows": [{"value": 100}]},
        headers={"X-Processing-Key": "invalid-key"},
    )

    assert response.status_code == 401


def test_csv_export_invalid_columns(client):
    test_client, api_key = client

    response = test_client.post(
        "/internal/render-csv",
        json={
            "rows": [
                {"participant": 1},
                {"score": 80},
            ]
        },
        headers={"X-Processing-Key": api_key},
    )

    assert response.status_code == 422
