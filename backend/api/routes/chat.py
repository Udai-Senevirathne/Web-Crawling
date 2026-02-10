"""
Chat API endpoints.
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import logging

from backend.services.chatbot_orchestrator import ChatbotOrchestrator
from backend.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize orchestrator (singleton pattern)
orchestrator = None


def get_orchestrator():
    """Get or create orchestrator instance."""
    global orchestrator
    if orchestrator is None:
        orchestrator = ChatbotOrchestrator()
    return orchestrator


# Request/Response Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    conversation_history: Optional[List[ChatMessage]] = Field(None, description="Previous conversation messages")
    client_id: Optional[str] = Field(None, description="Client ID for tenant isolation (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are your pricing plans?",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi! How can I help you?"}
                ]
            }
        }


class Source(BaseModel):
    url: str
    title: str


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant response")
    sources: List[Source] = Field(..., description="Source documents used")
    session_id: str = Field(..., description="Session ID")
    context_used: bool = Field(..., description="Whether relevant context was found")
    timestamp: str = Field(..., description="Response timestamp")


class SettingsRequest(BaseModel):
    system_prompt: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, authorization: Optional[str] = Header(None)):
    """
    Process chat message and return AI-generated response.
    """
    try:
        # Get orchestrator
        orch = get_orchestrator()

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Use provided client_id or None (search all documents)
        client_id = request.client_id

        # Try to extract client_id from auth token if provided and client_id not in request
        if authorization and not client_id:
            try:
                # Basic token handling - in production use proper JWT validation
                token = authorization.replace('Bearer ', '').strip()
                pass 
            except Exception:
                pass

        # Load system prompt from settings
        db = get_db()
        settings = db.settings.find_one({"key": "chat_settings"}) or {}
        system_prompt = settings.get("system_prompt")

        # Process query
        result = await orch.process_query(
            query=request.message,
            session_id=session_id,
            conversation_history=[msg.dict() for msg in request.conversation_history] if request.conversation_history else None,
            client_id=client_id,
            system_prompt=system_prompt
        )
        
        # Format sources
        sources = [
            Source(url=s.get("url", ""), title=s.get("title", "")) 
            for s in result.get("sources", [])
        ]
        
        # Save session to DB (chat history)
        timestamp = datetime.utcnow().isoformat()
        
        # Get existing history to append to
        current_history = []
        if request.conversation_history:
            current_history = [msg.dict() for msg in request.conversation_history]
            
        current_history.append({"role": "user", "content": request.message})
        current_history.append({"role": "assistant", "content": result["response"]})
        
        session_doc = {
            "session_id": session_id,
            "last_message": request.message,
            "updated_at": timestamp,
            "messages": current_history
        }
        
        # Upsert session
        db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": session_doc},
            upsert=True
        )

        return ChatResponse(
            response=result["response"],
            sources=sources,
            session_id=session_id,
            context_used=result.get("context_used", False),
            timestamp=timestamp + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/chat/stats")
async def get_stats():
    """
    Get chatbot statistics.
    """
    try:
        orch = get_orchestrator()
        # Mock stats logic if method doesn't exist on orchestrator yet
        if hasattr(orch, 'get_stats'):
            stats = orch.get_stats()
        else:
            # Fallback stats
            vs = orch.vector_store
            stats = {
                "total_documents": vs.count(),
                "model": orch.llm_service.model
            }

        return {
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def get_chat_sessions():
    """Get list of chat sessions."""
    db = get_db()
    sessions = list(db.chat_sessions.find())
    # Sort by updated_at desc
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    return {
        "sessions": [
            {
                "session_id": s.get("session_id"),
                "last_message": s.get("last_message"),
                "updated_at": s.get("updated_at"),
                "message_count": len(s.get("messages", []))
            }
            for s in sessions
        ]
    }


@router.get("/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get specific chat session details."""
    db = get_db()
    session = db.chat_sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Convert _id to string if present
    if "_id" in session:
        session["_id"] = str(session["_id"])
        
    return session


@router.delete("/chat/sessions/{session_id}", status_code=204)
async def delete_chat_session(session_id: str):
    """Delete a chat session."""
    db = get_db()
    db.chat_sessions.delete_one({"session_id": session_id})
    return None


@router.get("/chat/settings")
async def get_chat_settings():
    """Get chat settings (system prompt)."""
    db = get_db()
    settings = db.settings.find_one({"key": "chat_settings"}) or {}
    return {
        "system_prompt": settings.get("system_prompt", "")
    }


@router.post("/chat/settings")
async def update_chat_settings(request: SettingsRequest):
    """Update chat settings."""
    db = get_db()
    db.settings.update_one(
        {"key": "chat_settings"},
        {"$set": {"system_prompt": request.system_prompt}},
        upsert=True
    )
    return {"status": "updated"}
