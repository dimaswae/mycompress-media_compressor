"""Pydantic models for image endpoint request/response contracts."""

from pydantic import BaseModel, Field


class ImageJobResponse(BaseModel):
    """Response returned by compress, decompress, and embed endpoints."""

    job_id: str
    status: str
    metrics: dict[str, float] = Field(default_factory=dict)


class ImageExtractResponse(BaseModel):
    """Response returned by the extract endpoint."""

    job_id: str
    message: str
    metrics: dict[str, float] = Field(default_factory=dict)


class ImageCompareResponse(BaseModel):
    """Response returned by the compare endpoint."""

    job_id: str
    original_size: int
    result_size: int
    metrics: dict[str, float] = Field(default_factory=dict)
