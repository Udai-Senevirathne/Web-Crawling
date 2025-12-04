"""
Chat API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.services.chatbot_orchestrator import ChatbotOrchestrator

router = APIRouter()

# Initialize orchestrator (singleton pattern would be better for production)
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

    class Config:
        schema_extra = {
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

    class Config:
        schema_extra = {
            "example": {
                "response": "We offer three pricing plans: Basic ($9/mo), Pro ($29/mo), and Enterprise (custom).",
                "sources": [
                    {"url": "https://example.com/pricing", "title": "Pricing Page"}
                ],
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "context_used": True,
                "timestamp": "2025-11-24T10:30:00Z"
            }
        }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message and return AI-generated response.

    The chatbot uses RAG (Retrieval-Augmented Generation) to answer questions
    based on the website content that has been indexed.
    """
    try:
        # Get orchestrator
        orch = get_orchestrator()

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Process query
        result = await orch.process_query(
            query=request.message,
            session_id=session_id,
            conversation_history=history
        )

        # Add timestamp
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"

        return ChatResponse(**result)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/chat/stats")
async def get_stats():
    """
    Get chatbot statistics and information.
    """
    try:
        orch = get_orchestrator()
        stats = orch.get_stats()

        return {
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stats: {str(e)}"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.

    Note: This is a placeholder. In production, implement proper storage.
    """
    # TODO: Implement database storage for conversation history
    return {
        "session_id": session_id,
        "history": [],
        "message": "Chat history storage not yet implemented"
    }

