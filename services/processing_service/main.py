import httpx

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from csv_helper import generate_csv


app = FastAPI(title="Research Workspace - Processing Service")


class CSVExportRequest(BaseModel):
    rows: list[dict[str, str | int | float | bool | None]] = Field(
        min_length=1,
        max_length=1000,
    )


def verify_processing_key(
    api_key: str | None = Header(
        default=None,
        alias="X-Processing-Key",
    ),
):
    expected_key = os.environ.get("RW_PROCESSING_API_KEY")

    if not expected_key or len(expected_key) < 32:
        raise RuntimeError("Processing API key is not configured")

    if not api_key or not secrets.compare_digest(
        api_key, expected_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )


RESOURCE_SERVICE_URL = "http://127.0.0.1:8001"

export_bearer = HTTPBearer(auto_error=False)


class DatasetExportRequest(BaseModel):
    dataset_id: int = Field(gt=0)


async def get_resource_client():
    async with httpx.AsyncClient(
        timeout=5.0,
        trust_env=False,
        follow_redirects=False,
    ) as client:
        yield client


@app.get("/health")
def health_check():
    return {
        "service": "Processing Service",
        "status": "ok",
    }


@app.post("/internal/render-csv")
def render_csv(
    request: CSVExportRequest,
    _: None = Depends(verify_processing_key),
):
    try:
        csv_content = generate_csv(request.rows)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid CSV data",
        ) from exc

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="export.csv"'
        },
    )


@app.post("/internal/export-dataset")
async def export_dataset(
    request: DatasetExportRequest,
    _: None = Depends(verify_processing_key),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        export_bearer
    ),
    client: httpx.AsyncClient = Depends(get_resource_client),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Export token required",
        )

    # Request only the dataset specified in the export job.
    try:
        response = await client.get(
            f"{RESOURCE_SERVICE_URL}/internal/exports/{request.dataset_id}",
            headers={
                "Authorization": f"Bearer {credentials.credentials}"
            },
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Resource Service unavailable",
        ) from exc

    # Resource Service is responsible for authorization.
    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=403,
            detail="Export not permitted",
        )

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

    # Validate the response before processing its contents.
    try:
        dataset = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Invalid Resource Service response",
        ) from exc

    if not isinstance(dataset, dict):
        raise HTTPException(
            status_code=502,
            detail="Invalid Resource Service response",
        )

    rows = dataset.get("rows")

    if (
        type(dataset.get("dataset_id")) is not int
        or dataset["dataset_id"] != request.dataset_id
        or not isinstance(rows, list)
        or not 1 <= len(rows) <= 1000
    ):
        raise HTTPException(
            status_code=502,
            detail="Invalid Resource Service response",
        )

    # Convert the authorized dataset to CSV.
    try:
        csv_content = generate_csv(rows)
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Invalid dataset data",
        ) from exc

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="export.csv"'
        },
    )
