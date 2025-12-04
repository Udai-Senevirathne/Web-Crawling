"""
Ingestion API endpoints - allows dynamic website ingestion.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import sys
from pathlib import Path
from datetime import datetime
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.data_ingestion.pipeline import IngestionPipeline

router = APIRouter()

# Track ingestion jobs
ingestion_jobs = {}


class IngestionRequest(BaseModel):
    url: str = Field(..., description="Website URL to scrape and index")
    max_pages: Optional[int] = Field(50, description="Maximum pages to crawl", ge=1, le=500)
    max_depth: Optional[int] = Field(3, description="Maximum crawl depth", ge=1, le=10)
    reset: Optional[bool] = Field(False, description="Reset existing collection")

    class Config:
        schema_extra = {
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
    url: str
    timestamp: str


class IngestionStatusResponse(BaseModel):
    job_id: str
    status: str
    url: str
    progress: dict
    started_at: str
    completed_at: Optional[str]
    error: Optional[str]


async def run_ingestion_task(job_id: str, url: str, max_pages: int, max_depth: int, reset: bool):
    """Background task to run ingestion pipeline."""
    try:
        ingestion_jobs[job_id]["status"] = "running"

        pipeline = IngestionPipeline(url, max_pages=max_pages, max_depth=max_depth)
        await pipeline.run(reset=reset)

        ingestion_jobs[job_id]["status"] = "completed"
        ingestion_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
        ingestion_jobs[job_id]["progress"]["message"] = "Ingestion completed successfully"

    except Exception as e:
        ingestion_jobs[job_id]["status"] = "failed"
        ingestion_jobs[job_id]["error"] = str(e)
        ingestion_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
        print(f"Ingestion job {job_id} failed: {e}")


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

        # Create job
        job_id = str(uuid.uuid4())
        ingestion_jobs[job_id] = {
            "status": "pending",
            "url": url,
            "max_pages": request.max_pages,
            "max_depth": request.max_depth,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "error": None,
            "progress": {
                "message": "Ingestion job queued"
            }
        }

        # Start background task
        background_tasks.add_task(
            run_ingestion_task,
            job_id,
            url,
            request.max_pages,
            request.max_depth,
            request.reset
        )

        return IngestionResponse(
            job_id=job_id,
            status="pending",
            message="Ingestion job started",
            url=url,
            timestamp=ingestion_jobs[job_id]["started_at"]
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
    if job_id not in ingestion_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    job = ingestion_jobs[job_id]

    return IngestionStatusResponse(
        job_id=job_id,
        status=job["status"],
        url=job["url"],
        progress=job["progress"],
        started_at=job["started_at"],
        completed_at=job.get("completed_at"),
        error=job.get("error")
    )


@router.get("/ingest")
async def list_ingestion_jobs():
    """
    List all ingestion jobs.
    """
    return {
        "jobs": [
            {
                "job_id": job_id,
                "url": job["url"],
                "status": job["status"],
                "started_at": job["started_at"]
            }
            for job_id, job in ingestion_jobs.items()
        ],
        "total": len(ingestion_jobs)
    }

