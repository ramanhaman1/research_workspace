
from fastapi import FastAPI

app = FastAPI(title="Research Workspace - Processing Service")


@app.get("/health")
def health_check():
    return {
        "service": "Processing Service",
        "status": "ok"
    }
