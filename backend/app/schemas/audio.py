"""Pydantic models for audio endpoint request/response contracts."""

from pydantic import BaseModel, Field


class AudioJobResponse(BaseModel):
    """Response returned by compress, decompress, and embed endpoints."""

    job_id: str = Field(description="Unique identifier of the created processing job")
    status: str = Field(description="Current status of the job (e.g., pending, processing, done, failed)")
    metrics: dict[str, float] = Field(default_factory=dict, description="Metadata and performance metrics computed during the job execution")


class AudioExtractResponse(BaseModel):
    """Response returned by the audio extract endpoint."""

    job_id: str = Field(description="Unique identifier of the extract job")
    message: str = Field(description="The secret message extracted from the steganographic audio")
    metrics: dict[str, float] = Field(default_factory=dict, description="Extraction performance metrics (e.g., processing time)")


class AudioCompareResponse(BaseModel):
    """Response returned by the audio compare endpoint."""

    job_id: str = Field(description="Unique identifier of the job being compared")
    original_size: int = Field(description="Size of the original uploaded audio in bytes")
    result_size: int = Field(description="Size of the processed result audio in bytes")
    metrics: dict[str, float] = Field(default_factory=dict, description="Detailed comparison and quality metrics (e.g., compression_ratio, processing_time_ms, hidden_capacity_bits)")
    original_url: str = Field(description="URL to download the original uploaded audio file")
    result_url: str = Field(description="URL to download the processed result audio file")
