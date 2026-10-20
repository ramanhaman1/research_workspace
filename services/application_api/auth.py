
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = os.environ["RW_JWT_SECRET"]
ALGORITHM = "HS256"

if len(SECRET_KEY) < 32:
    raise RuntimeError("JWT secret must be at least 32 characters")


# Local test accounts
users = {
    "ali": {
        "role": "researcher",
        "password_hash": password_hash.hash(
            os.environ["RW_ALI_PASSWORD"]
        ),
    },
    "Raman": {
        "role": "researcher",
        "password_hash": password_hash.hash(
            os.environ["RW_RAMAN_PASSWORD"]
        ),
    },
    "admin": {
        "role": "admin",
        "password_hash": password_hash.hash(
            os.environ["RW_ADMIN_PASSWORD"]
        ),
    },
}


def authenticate_user(username: str, password: str):
    user = users.get(username)

    if not user:
        return None

    if not password_hash.verify(password, user["password_hash"]):
        return None

    return user


def create_access_token(username: str, role: str):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": username,
        "role": role,
        "iss": "research-workspace",
        "aud": "application-api",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer="research-workspace",
            audience="application-api",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    user = users.get(username)

    if not user or payload.get("role") != user["role"]:
        raise HTTPException(status_code=401, detail="Invalid user")

    return {"username": username, "role": user["role"]}
