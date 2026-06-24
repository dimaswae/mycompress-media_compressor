"""Repository functions for Job CRUD operations."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Job


def create_job(db: Session, job: Job) -> Job:
    """Persist a new Job record and return it."""
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    """Retrieve a Job by its id, or None if not found."""
    return db.query(Job).filter(Job.id == job_id).first()


def update_job_status(
    db: Session,
    job_id: str,
    status: str,
    error_code: str | None = None,
    error_message: str | None = None,
    result_path: str | None = None,
) -> Job | None:
    """Update a Job's status and optional error/result fields. Returns the updated Job or None."""
    job = get_job(db, job_id)
    if job is None:
        return None
    job.status = status
    job.updated_at = datetime.now(timezone.utc)
    if error_code is not None:
        job.error_code = error_code
    if error_message is not None:
        job.error_message = error_message
    if result_path is not None:
        job.result_path = result_path
    db.commit()
    db.refresh(job)
    return job
