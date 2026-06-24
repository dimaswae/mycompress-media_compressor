"""Pydantic models for video endpoint request/response contracts."""

from pydantic import BaseModel, Field


class VideoJobResponse(BaseModel):
    """Response returned by compress, decompress, and embed endpoints."""

    job_id: str
    status: str
    metrics: dict[str, float] = Field(default_factory=dict)


class VideoExtractResponse(BaseModel):
    """Response returned by the video extract endpoint."""

    job_id: str
    message: str
    metrics: dict[str, float] = Field(default_factory=dict)


class VideoCompareResponse(BaseModel):
    """Response returned by the video compare endpoint."""

    job_id: str
    original_size: int
    result_size: int
    metrics: dict[str, float] = Field(default_factory=dict)
