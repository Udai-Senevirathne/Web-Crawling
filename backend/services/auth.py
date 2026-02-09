"""
Authentication utilities: password hashing, JWT handling, FastAPI dependencies.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import logging

from .db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "60"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    # Development helper: allow plain text passwords for testing
    if os.getenv("USE_FAKE_DB", "0") == "1" and isinstance(hashed_password, str) and hashed_password.startswith("plain:"):
        return plain_password == hashed_password.split("plain:", 1)[1]
    
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(subject: str, data: Optional[dict] = None, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject}
    if data:
        to_encode.update(data)
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # Use integer UNIX timestamp for exp to ensure compatibility with JWT libraries
    to_encode.update({"exp": int(expire.timestamp())})
    # issued-at
    to_encode.update({"iat": int(datetime.utcnow().timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str):
    db = get_db()
    user = db.users.find_one({"username": username})
    print("User Details..")
    print(user)
    if not user:
        return None
    # Support both possible password field names to be resilient to seed scripts
    pwd_hash = user.get("password_hash") or user.get("hashed_password") or ""
    if not verify_password(password, pwd_hash):
        return None
    user["id"] = str(user.get("_id"))
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    print("""Get current authenticated user.""")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token , key=None, options={"verify_signature": False})
        print("payload")
        print("payload")
        print("payload")
        print("payload")
        print("payload")
        print("payload")
        print(payload)
        print(payload)
        print(payload)
        print(payload)
        print(payload)
        print(payload)
        print(payload)
        print(payload)
        print(payload)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = get_db()
    user = db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    user["id"] = str(user.get("_id"))
    return user


def require_admin(user=Depends(get_current_user)):
    role = user.get("role")
    logger = logging.getLogger("uvicorn.access")
    logger.info("require_admin: user=%s role=%s", user.get("username"), role)
    if role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


def require_superadmin(user=Depends(get_current_user)):
    role = user.get("role")
    if role != "superadmin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user
