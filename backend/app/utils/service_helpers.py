"""Shared helper functions for media services."""

from sqlalchemy.orm import Session
from app.db.metric_repository import add_metric
from app.infra.file_validation import validate_size

_SENTINEL = 999.0

def sanitize_metrics(metrics: dict[str, float]) -> dict[str, float]:
    """Replace non-finite floats with sentinel values for JSON safety."""
    return {
        k: (
            _SENTINEL
            if v == float("inf")
            else -_SENTINEL if v == float("-inf") else 0.0 if v != v else v
        )
        for k, v in metrics.items()
    }

def store_job_metrics(db: Session, job_id: str, metrics: dict[str, float]) -> None:
    """Persist a sanitized dictionary of metric_name -> value."""
    for name, value in sanitize_metrics(metrics).items():
        add_metric(db, job_id, name, value)

def validate_size_only(file_bytes: bytes) -> None:
    """Validate only the file size (skip extension/magic checks)."""
    validate_size(file_bytes)
