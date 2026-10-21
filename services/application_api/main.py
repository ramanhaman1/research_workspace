import httpx
from pydantic import Field

from services.application_api.internal_tokens import (
    create_internal_token,
)

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from services.application_api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
)


app = FastAPI(title="Research Workspace - Application API")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health_check():
    return {
        "service": "Application API",
        "status": "ok"
    }


@app.post("/login")
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(
        request.username,
        user["role"]
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/me")
def read_current_user(user: dict = Depends(get_current_user)):
    return user

# Resource Service address
RESOURCE_URL = "http://127.0.0.1:8001"


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    rows: list[dict[str, str | int | float | bool | None]] = Field(
        min_length=1,
        max_length=1000,
    )


@app.post("/datasets", status_code=201)
async def create_new_dataset(
    request: DatasetCreate,
    user: dict = Depends(get_current_user),
):
    if user["role"] != "researcher":
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    token = create_internal_token(
        username=user["username"],
        role=user["role"],
        scope="datasets:create",
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{RESOURCE_URL}/datasets",
                json=request.model_dump(),
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Resource Service unavailable",
        ) from exc

    if response.status_code == 422:
        raise HTTPException(
            status_code=422,
            detail="Invalid dataset data",
        )

    if response.status_code != 201:
        raise HTTPException(
            status_code=502,
            detail="Resource Service rejected the request",
        )

    return response.json()


@app.get("/datasets/{dataset_id}")
async def read_dataset(
    dataset_id: int,
    user: dict = Depends(get_current_user),
):
    if user["role"] != "researcher":
        raise HTTPException(
            status_code=403,
            detail="Permission denied",
        )

    if dataset_id < 1:
        raise HTTPException(
            status_code=422,
            detail="Invalid dataset ID",
        )

    token = create_internal_token(
        username=user["username"],
        role=user["role"],
        scope="datasets:read",
        dataset_id=dataset_id,
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{RESOURCE_URL}/datasets/{dataset_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail="Resource Service unavailable",
        ) from exc

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Resource Service rejected the request",
        )

    return response.json()
