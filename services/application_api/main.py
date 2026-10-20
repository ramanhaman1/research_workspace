
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
