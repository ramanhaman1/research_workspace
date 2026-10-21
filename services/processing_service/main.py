
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
