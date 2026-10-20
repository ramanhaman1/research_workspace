
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.resource_service.database import (
    create_dataset,
    get_dataset,
)
from services.resource_service.service_auth import verify_service_token


app = FastAPI(title="Research Workspace - Resource Service")


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    rows: list[dict[str, str | int | float | bool | None]] = Field(
        min_length=1,
        max_length=1000,
    )


@app.get("/health")
def health_check():
    return {
        "service": "Resource Service",
        "status": "ok"
    }


@app.post("/datasets", status_code=201)
def create_new_dataset(
    request: DatasetCreate,
    claims: dict = Depends(verify_service_token),
):
    if (
        claims["scope"] != "datasets:create"
        or claims["azp"] != "application-api"
        or claims.get("role") != "researcher"
    ):
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    try:
        dataset_id = create_dataset(
            owner_username=claims["sub"],
            name=request.name,
            rows=request.rows,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc

    return {
        "id": dataset_id,
        "message": "Dataset created"
    }


@app.get("/datasets/{dataset_id}")
def read_dataset(
    dataset_id: int,
    claims: dict = Depends(verify_service_token),
):
    if (
        claims["scope"] != "datasets:read"
        or claims.get("role") != "researcher"
    ):
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    # The token must authorize this specific dataset.
    if type(claims.get("dataset_id")) is not int or (
        claims["dataset_id"] != dataset_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Dataset not authorized"
        )

    dataset = get_dataset(
        dataset_id=dataset_id,
        requester_username=claims["sub"],
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    return dataset
