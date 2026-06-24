"""Repository functions for Metric CRUD operations."""

from sqlalchemy.orm import Session

from app.db.models import Metric


def add_metric(
    db: Session, job_id: str, metric_name: str, metric_value: float
) -> Metric:
    """Create and persist a Metric record, returning it."""
    metric = Metric(job_id=job_id, metric_name=metric_name, metric_value=metric_value)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def get_metrics_for_job(db: Session, job_id: str) -> list[Metric]:
    """Return all Metric rows for the given job_id."""
    return db.query(Metric).filter(Metric.job_id == job_id).all()
