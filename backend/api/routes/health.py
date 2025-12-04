"""
Health check endpoints.
"""
from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "chatbot-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@router.get("/status")
async def status():
    """Detailed status endpoint."""
    from ...services.chatbot_orchestrator import ChatbotOrchestrator

    try:
        orchestrator = ChatbotOrchestrator()
        stats = orchestrator.get_stats()

        return {
            "status": "operational",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

