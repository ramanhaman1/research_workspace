
from fastapi import FastAPI

app = FastAPI(title="Research Workspace - Resource Service")


@app.get("/health")
def health_check():
    return {
        "service": "Resource Service",
        "status": "ok"
    }
