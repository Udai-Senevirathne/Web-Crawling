"""
FastAPI application entry point.
"""
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat, health, ingestion
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    # --- Startup ---
    logger = logging.getLogger("uvicorn")
    logger.info("%s", "=" * 60)
    logger.info("Starting Web Crawler Chatbot API")
    logger.info("Environment: %s", os.getenv('ENVIRONMENT', 'development'))
    logger.info("API Docs: http://localhost:%s/docs", os.getenv('API_PORT', '8000'))
    logger.info("Vector Store: %s", os.getenv('VECTOR_STORE_TYPE', 'chroma'))
    logger.info("LLM Provider: %s", os.getenv('LLM_PROVIDER', 'groq'))

    # Try to connect to database (optional)
    try:
        from backend.services.db import get_db, use_fake_db
        if use_fake_db():
            logger.info("Database: In-memory (USE_FAKE_DB=1)")
        else:
            db = get_db()
            logger.info("Database: MongoDB connected")
    except Exception as e:
        logger.warning("Database not available: %s (using in-memory)", e)

    logger.info("%s", "=" * 60)

    yield  # App is running

    # --- Shutdown ---
    logger.info("Shutting down chatbot API...")


app = FastAPI(
    title="Web Crawler Chatbot API",
    description="RAG-based chatbot for crawled website content",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://localhost:5173")
origins = [o.strip() for o in _cors_env.split(",")]
_allow_all_origins = "*" in origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all_origins else origins,
    allow_credentials=False if _allow_all_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(ingestion.router, prefix="/api", tags=["ingestion"])

# Optional: Include auth and clients routers if auth is enabled
try:
    from .routes import auth, clients
    app.include_router(auth.router, prefix="/api", tags=["auth"])
    app.include_router(clients.router, prefix="/api", tags=["clients"])
except ImportError:
    pass


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Web Crawler Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("RELOAD", "False").lower() == "true"
    )
