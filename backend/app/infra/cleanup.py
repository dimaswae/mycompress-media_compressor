"""Background cleanup of expired job data."""

import logging
from datetime import datetime, timezone

from sqlalchemy import text

from app.db.database import SessionLocal
from app.infra.storage import delete_job_files

logger = logging.getLogger(__name__)


def sweep_expired_jobs() -> int:
    """Find jobs whose ``expires_at`` is in the past, delete their files, and
    mark them as ``expired``.

    Returns the number of jobs swept.
    """
    from app.db.models import Job  # late import to avoid circular deps

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired_jobs = (
            db.query(Job)
            .filter(Job.expires_at < now, Job.status != "expired")
            .all()
        )

        for job in expired_jobs:
            delete_job_files(job.id)
            job.status = "expired"
            job.updated_at = now

        db.commit()

        for job in expired_jobs:
            logger.info("Swept expired job %s", job.id)

        return len(expired_jobs)
    finally:
        db.close()
