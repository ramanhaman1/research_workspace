
import secrets

import jwt
import pytest

from services.application_api.internal_tokens import (
    create_internal_token,
)


@pytest.fixture
def secret(monkeypatch):
    value = secrets.token_urlsafe(48)
    monkeypatch.setenv("RW_INTERNAL_JWT_SECRET", value)
    return value


def test_create_internal_token(secret):
    token = create_internal_token(
        username="ali",
        role="researcher",
        scope="datasets:create",
    )

    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="resource-service",
        issuer="research-workspace",
    )

    assert payload["sub"] == "ali"
    assert payload["scope"] == "datasets:create"
    assert payload["azp"] == "application-api"


def test_read_token_contains_dataset_id(secret):
    token = create_internal_token(
        username="ali",
        role="researcher",
        scope="datasets:read",
        dataset_id=1,
    )

    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        audience="resource-service",
    )

    assert payload["dataset_id"] == 1


def test_invalid_scope_rejected(secret):
    with pytest.raises(ValueError):
        create_internal_token(
            username="ali",
            role="researcher",
            scope="admin:all",
        )


def test_read_requires_dataset_id(secret):
    with pytest.raises(ValueError):
        create_internal_token(
            username="ali",
            role="researcher",
            scope="datasets:read",
        )


def test_admin_cannot_get_dataset_token(secret):
    with pytest.raises(ValueError):
        create_internal_token(
            username="admin",
            role="admin",
            scope="datasets:create",
        )
