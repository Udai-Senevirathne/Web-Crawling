from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    role: str = Field("user")
    client_id: Optional[str] = None


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    client_id: Optional[str] = None
