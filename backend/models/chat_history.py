from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatHistoryCreate(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    client_id: str = Field(..., description="Client/tenant identifier")
    user_id: str = Field(..., description="User identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Conversation messages")


class ChatHistoryOut(BaseModel):
    id: str = Field(..., description="MongoDB ObjectId as string")
    session_id: str = Field(..., description="Unique session identifier")
    client_id: str = Field(..., description="Client/tenant identifier")
    user_id: str = Field(..., description="User identifier")
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
