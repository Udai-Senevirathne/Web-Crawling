from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
)
from backend.services.db import get_db as _get_db

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    client_id: str | None = None


@router.post("/auth/register")
def register(req: RegisterRequest):
    db = _get_db()
    existing = db.users.find_one({"username": req.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_doc = {
        "username": req.username,
        "password_hash": get_password_hash(req.password),
        "role": req.role,
        "client_id": req.client_id,
    }
    res = db.users.insert_one(user_doc)
    return {"id": str(res.inserted_id), "username": req.username}


class Auth(BaseModel):
    username : str
    password : str


@router.post("/auth/login")
def login(auth : Auth):
    user = authenticate_user(auth.username, auth.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # include client_id and role in token claims
    extra = {"role": user.get("role"), "client_id": user.get("client_id")}
    access_token = create_access_token(subject=user.get("username"), data=extra)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me")
def me(user=Depends(get_current_user)):
    """Return current authenticated user info."""
    # sanitize MongoDB object
    return {
        "id": str(user.get("_id")) if user.get("_id") else user.get("id"),
        "username": user.get("username"),
        "role": user.get("role"),
        "client_id": user.get("client_id")
    }
