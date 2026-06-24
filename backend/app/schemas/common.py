"""Shared Pydantic models for API request/response contracts."""

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Envelope for a single error code and human-readable message."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response body returned on non-2xx responses."""

    error: ErrorDetail


class JobStatusResponse(BaseModel):
    """Response model for a single job's current status and metadata.

    Maps the ORM ``Job.id`` to the API field ``job_id``.
    Accepts both ``id`` (from ORM) and ``job_id`` (Python name) on input.
    """

    model_config = {"from_attributes": True, "populate_by_name": True}

    job_id: str = Field(validation_alias="id")
    status: str
    media_type: str
    operation: str
    algorithm: str | None = None
    encrypted: bool = False
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class JobListResponse(BaseModel):
    """Paginated list of jobs returned by ``GET /jobs``."""

    jobs: list[JobStatusResponse]
    total: int
    limit: int
    offset: int
