"""
Ingestion API endpoints - allows dynamic website ingestion.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from datetime import datetime
import uuid
import logging

from backend.data_ingestion.pipeline import IngestionPipeline
from backend.services.db import get_db
import os

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_BASE = os.getenv("UPLOAD_BASE", "./data/uploads")

# In-memory cache for quick lookup
ingestion_jobs = {}


class IngestionRequest(BaseModel):
    url: str = Field(..., description="Website URL to scrape and index")
    max_pages: Optional[int] = Field(50, description="Maximum pages to crawl", ge=1, le=500)
    max_depth: Optional[int] = Field(3, description="Maximum crawl depth", ge=1, le=10)
    reset: Optional[bool] = Field(False, description="Reset existing collection")
    client_id: Optional[str] = Field(None, description="Client ID for tenant isolation (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://docs.python.org",
                "max_pages": 50,
                "max_depth": 3,
                "reset": False
            }
        }


class IngestionResponse(BaseModel):
    job_id: str
    status: str
    message: str
    url: Optional[str] = None
    timestamp: str


class IngestionStatusResponse(BaseModel):
    job_id: str
    status: str
    url: Optional[str] = None
    progress: dict
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


def run_ingestion_task_sync(job_id: str, url: str, max_pages: int, max_depth: int, reset: bool, client_id: str | None = None, files: list[str] | None = None):
    """Synchronous wrapper that creates a new event loop with Windows policy."""
    import asyncio
    import sys
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(_run_ingestion_async(job_id, url, max_pages, max_depth, reset, client_id, files))
    finally:
        loop.close()


async def _run_ingestion_async(job_id: str, url: str, max_pages: int, max_depth: int, reset: bool, client_id: str | None = None, files: list[str] | None = None):
    """Actual async ingestion logic."""
    try:
        # Mark running in DB
        db = get_db()
        db.ingestion_jobs.update_one({"job_id": job_id}, {"$set": {"status": "running", "started_at": datetime.utcnow()}})

        pipeline = IngestionPipeline(url or "", max_pages=max_pages, max_depth=max_depth, client_id=client_id, job_id=job_id)
        await pipeline.run(reset=reset, files=files)

        # Mark completed
        db.ingestion_jobs.update_one({"job_id": job_id}, {"$set": {"status": "completed", "completed_at": datetime.utcnow()}})
        
        # Update cache
        job_doc = db.ingestion_jobs.find_one({"job_id": job_id})
        if job_doc:
            ingestion_jobs[job_id] = job_doc

    except Exception as e:
        db = get_db()
        db.ingestion_jobs.update_one({"job_id": job_id}, {"$set": {"status": "failed", "error": str(e), "completed_at": datetime.utcnow()}})
        job_doc = db.ingestion_jobs.find_one({"job_id": job_id})
        if job_doc:
            ingestion_jobs[job_id] = job_doc
        logger.error("Ingestion job %s failed: %s", job_id, e, exc_info=True)


@router.post("/ingest", response_model=IngestionResponse)
async def start_ingestion(request: IngestionRequest, background_tasks: BackgroundTasks):
    """
    Start ingestion of a website.

    This endpoint starts a background job to scrape and index the specified website.
    Use the job_id to check the status of the ingestion process.
    """
    try:
        # Validate URL format
        url = request.url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Use provided client_id or default to None
        client_id = request.client_id

        # Create job in DB
        db = get_db()
        job_id = str(uuid.uuid4())
        job_doc = {
            "job_id": job_id,
            "status": "pending",
            "url": url,
            "max_pages": request.max_pages,
            "max_depth": request.max_depth,
            "client_id": client_id,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "progress": {"message": "Ingestion job queued"},
            "type": "crawl",
        }
        db.ingestion_jobs.insert_one(job_doc)
        ingestion_jobs[job_id] = job_doc

        # Start background task
        background_tasks.add_task(
            run_ingestion_task_sync,
            job_id,
            url,
            request.max_pages,
            request.max_depth,
            request.reset,
            client_id,
            None
        )

        return IngestionResponse(
            job_id=job_id,
            status="pending",
            message="Ingestion job started",
            url=url,
            timestamp=job_doc["created_at"].isoformat() + "Z"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ingestion: {str(e)}"
        )


@router.get("/ingest/{job_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(job_id: str):
    """
    Get the status of an ingestion job.
    """
    # Try cache first
    if job_id in ingestion_jobs:
        job = ingestion_jobs[job_id]
    else:
        db = get_db()
        job = db.ingestion_jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    started_at = job.get("started_at")
    completed_at = job.get("completed_at")

    return IngestionStatusResponse(
        job_id=job_id,
        status=job.get("status", "unknown"),
        url=job.get("url", ""),
        progress=job.get("progress", {}),
        started_at=started_at.isoformat() + "Z" if started_at else None,
        completed_at=completed_at.isoformat() + "Z" if completed_at else None,
        error=job.get("error")
    )


@router.get("/ingest")
async def list_ingestion_jobs():
    """
    List all ingestion jobs.
    """
    db = get_db()
    jobs = list(db.ingestion_jobs.find().sort("created_at", -1).limit(50))
    return {
        "jobs": [
            {
                "job_id": j.get("job_id"),
                "url": j.get("url"),
                "status": j.get("status"),
                "started_at": j.get("started_at").isoformat() + "Z" if j.get("started_at") else None
            }
            for j in jobs
        ],
        "total": len(jobs)
    }


@router.delete("/ingest/{job_id}", status_code=204)
async def delete_ingestion_job(job_id: str):
    """Delete an ingestion job and its indexed content."""
    db = get_db()
    
    # Check if job exists
    job = db.ingestion_jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Delete from vector store
    try:
        from backend.services.vector_store import VectorStore
        vs = VectorStore()
        # Delete using job_id metadata
        vs.delete_documents(where={"job_id": job_id})
    except Exception as e:
        logger.warning("Error deleting vectors for job %s: %s", job_id, e)
        # Continue with DB deletion even if vectors fail
        
    # Delete upload directory if exists
    upload_dir = Path(UPLOAD_BASE) / job_id
    if upload_dir.exists():
        import shutil
        try:
            shutil.rmtree(upload_dir)
        except Exception as e:
            logger.warning("Error deleting upload dir %s: %s", upload_dir, e)

    # Delete from DB
    db.ingestion_jobs.delete_one({"job_id": job_id})
    
    # Remove from cache
    if job_id in ingestion_jobs:
        del ingestion_jobs[job_id]
        
    return None


@router.post("/ingest/reset", status_code=200)
async def reset_database():
    """Reset the entire vector database and clear all jobs."""
    try:
        # Reset vector store
        from backend.services.vector_store import VectorStore
        vs = VectorStore()
        vs.reset_collection()
        
        # Invalidate the chat orchestrator singleton so it picks up the new collection
        from backend.api.routes import chat as chat_module
        chat_module.orchestrator = None
        
        # Clear uploads
        import shutil
        if os.path.exists(UPLOAD_BASE):
            shutil.rmtree(UPLOAD_BASE)
            os.makedirs(UPLOAD_BASE)
            
        # Clear DB jobs
        db = get_db()
        db.ingestion_jobs.delete_many({})
        ingestion_jobs.clear()
        
        return {"message": "Database reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {e}")


@router.post("/ingest/upload", response_model=IngestionResponse)
async def upload_and_ingest(
    files: list[UploadFile] = File(...),
    max_pages: int = Form(50),
    max_depth: int = Form(3),
    reset: bool = Form(False),
    client_id: str = Form(None),
    background_tasks: BackgroundTasks = None
):
    """Upload files (PDF, text) and start ingestion job."""
    try:
        db = get_db()
        job_id = str(uuid.uuid4())

        # Create upload dir
        upload_dir = Path(UPLOAD_BASE) / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for up in files:
            dest = upload_dir / up.filename
            with open(dest, "wb") as f:
                f.write(await up.read())
            saved_files.append(str(dest))

        job_doc = {
            "job_id": job_id,
            "status": "pending",
            "url": None,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "client_id": client_id,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "progress": {"message": "Upload queued"},
            "type": "upload",
            "files": saved_files,
        }

        db.ingestion_jobs.insert_one(job_doc)
        ingestion_jobs[job_id] = job_doc

        # Schedule background task
        background_tasks.add_task(run_ingestion_task_sync, job_id, None, max_pages, max_depth, reset, client_id, saved_files)

        return IngestionResponse(
            job_id=job_id,
            status="pending",
            message="Upload queued and ingestion started",
            url="",
            timestamp=job_doc["created_at"].isoformat() + "Z"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload and start ingestion: {str(e)}")
