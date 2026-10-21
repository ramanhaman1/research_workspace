
import os
from datetime import datetime, timedelta, timezone

import jwt


ALGORITHM = "HS256"
ISSUER = "research-workspace"
AUDIENCE = "resource-service"

ALLOWED_SCOPES = {
    "datasets:create",
    "datasets:read",
}


def create_internal_token(
    username: str,
    role: str,
    scope: str,
    dataset_id: int | None = None,
) -> str:

    if scope not in ALLOWED_SCOPES:
        raise ValueError("Invalid scope")

    if not username or role != "researcher":
        raise ValueError("Invalid user or role")

    if scope == "datasets:read":
        if type(dataset_id) is not int or dataset_id < 1:
            raise ValueError("Dataset ID required")
    elif dataset_id is not None:
        raise ValueError("Dataset ID not allowed for create")

    secret = os.environ.get("RW_INTERNAL_JWT_SECRET")

    if not secret or len(secret) < 32:
        raise RuntimeError("Internal JWT secret is not configured")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": username,
        "role": role,
        "scope": scope,
        "azp": "application-api",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=60),
    }

    if dataset_id is not None:
        payload["dataset_id"] = dataset_id

    return jwt.encode(
        payload,
        secret,
        algorithm=ALGORITHM,
    )
