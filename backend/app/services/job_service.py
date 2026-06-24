"""Service-layer functions wrapping job repository operations.

This module contains no FastAPI imports, keeping it testable without a
running server.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.job_repository import (
    create_job as repo_create_job,
    get_job as repo_get_job,
    update_job_status as repo_update_job_status,
)
from app.db.models import Job


def create_job(
    db: Session,
    media_type: str,
    operation: str,
    original_filename: str,
    original_path: str,
    algorithm: str | None = None,
    encrypted: bool = False,
    salt: str | None = None,
    status: str = "pending",
) -> Job:
    """Create a new job record and persist it.

    Returns:
        The newly created ``Job`` ORM instance.
    """
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    job = Job.new(
        job_id=job_id,
        media_type=media_type,
        operation=operation,
        original_filename=original_filename,
        original_path=original_path,
        algorithm=algorithm,
        encrypted=encrypted,
        salt=salt,
        status=status,
    )
    return repo_create_job(db, job)


def get_job_status(db: Session, job_id: str) -> Job | None:
    """Retrieve a job by its id.

    Returns:
        The ``Job`` instance, or ``None`` if not found.
    """
    return repo_get_job(db, job_id)


def update_job_status(
    db: Session,
    job_id: str,
    status: str,
    error_code: str | None = None,
    error_message: str | None = None,
    result_path: str | None = None,
) -> Job | None:
    """Update a job's status and optional fields.

    Returns:
        The updated ``Job`` instance, or ``None`` if not found.
    """
    return repo_update_job_status(
        db,
        job_id=job_id,
        status=status,
        error_code=error_code,
        error_message=error_message,
        result_path=result_path,
    )
