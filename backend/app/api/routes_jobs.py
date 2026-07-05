"""Generic job management endpoints (cross-media).

Supports status lookup, result download, deletion, and paginated listing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Job
from app.infra.storage import delete_job_files
from app.schemas.common import JobListResponse, JobStatusResponse
from app.services.job_service import get_job_status, update_job_status

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    """Return the current status and metadata for a single job."""
    job = get_job_status(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse.model_validate(job)


@router.get("/jobs/{job_id}/download")
async def download_job_result(
    job_id: str, db: Session = Depends(get_db)
) -> FileResponse:
    """Stream the processed result file for a completed job."""
    job = get_job_status(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.result_path is None:
        raise HTTPException(
            status_code=404, detail="No result file available for this job"
        )
    return FileResponse(job.result_path)


@router.get("/jobs/{job_id}/download/original")
async def download_job_original(
    job_id: str, db: Session = Depends(get_db)
) -> FileResponse:
    """Stream the original input file for a job."""
    job = get_job_status(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.original_path is None or job.original_path == "":
        raise HTTPException(
            status_code=404, detail="No original file available for this job"
        )
    return FileResponse(job.original_path)


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a job's files and mark it as deleted."""
    job = get_job_status(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    delete_job_files(job_id)
    update_job_status(db, job_id, status="deleted")


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Return a paginated list of all jobs."""
    total = db.query(Job).count()
    jobs = (
        db.query(Job)
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return JobListResponse(
        jobs=[JobStatusResponse.model_validate(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )
