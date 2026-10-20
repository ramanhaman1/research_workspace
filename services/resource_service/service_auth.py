
import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ISSUER = "research-workspace"
AUDIENCE = "resource-service"


def verify_service_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    secret = os.environ.get("RW_INTERNAL_JWT_SECRET")

    if not secret or len(secret) < 32:
        raise RuntimeError("Internal JWT secret is not configured")

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": [
                    "sub", "iss", "aud", "iat",
                    "exp", "scope", "azp"
                ]
            },
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    if (
        not isinstance(payload.get("sub"), str)
        or not payload["sub"]
        or payload.get("azp") not in (
            "application-api", "processing-service"
        )
        or payload.get("scope") not in (
            "datasets:create", "datasets:read"
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid authorization claims"
        )

    return payload
