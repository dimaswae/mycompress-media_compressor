"""Pydantic models for audio endpoint request/response contracts."""

from pydantic import BaseModel, Field


class AudioJobResponse(BaseModel):
    """Response returned by compress, decompress, and embed endpoints."""

    job_id: str
    status: str
    metrics: dict[str, float] = Field(default_factory=dict)


class AudioExtractResponse(BaseModel):
    """Response returned by the audio extract endpoint."""

    job_id: str
    message: str
    metrics: dict[str, float] = Field(default_factory=dict)


class AudioCompareResponse(BaseModel):
    """Response returned by the audio compare endpoint."""

    job_id: str
    original_size: int
    result_size: int
    metrics: dict[str, float] = Field(default_factory=dict)
