"""Shared Pydantic models for API request/response contracts."""

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Envelope for a single error code and human-readable message."""

    code: str = Field(description="Machine-readable error category code (e.g., CAPACITY_EXCEEDED)")
    message: str = Field(description="Human-readable description of the error")


class ErrorResponse(BaseModel):
    """Standard error response body returned on non-2xx responses."""

    error: ErrorDetail = Field(description="Detailed error payload")


class JobStatusResponse(BaseModel):
    """Response model for a single job's current status and metadata.

    Maps the ORM ``Job.id`` to the API field ``job_id``.
    Accepts both ``id`` (from ORM) and ``job_id`` (Python name) on input.
    """

    model_config = {"from_attributes": True, "populate_by_name": True}

    job_id: str = Field(validation_alias="id", description="Unique identifier of the job")
    status: str = Field(description="Current status of the job (pending, processing, done, failed, deleted, expired)")
    media_type: str = Field(description="Type of media processed (image, audio, video)")
    operation: str = Field(description="Operation performed on the media (compress, decompress, embed, extract)")
    algorithm: str | None = Field(default=None, description="Algorithm or setting used (e.g., rle, huffman, lsb, bitrate, transcode)")
    encrypted: bool = Field(default=False, description="Whether the embedded payload was encrypted with AES")
    error_code: str | None = Field(default=None, description="ErrorCode if the job failed")
    error_message: str | None = Field(default=None, description="Detailed error message if the job failed")
    created_at: datetime = Field(description="Timestamp when the job was created")
    updated_at: datetime = Field(description="Timestamp when the job was last updated")
    expires_at: datetime = Field(description="Timestamp when the job and its files will expire and be swept")


class JobListResponse(BaseModel):
    """Paginated list of jobs returned by ``GET /jobs``."""

    jobs: list[JobStatusResponse] = Field(description="List of jobs in the current page")
    total: int = Field(description="Total number of jobs in the database")
    limit: int = Field(description="Maximum number of jobs returned in this page")
    offset: int = Field(description="Number of jobs skipped in this query")
