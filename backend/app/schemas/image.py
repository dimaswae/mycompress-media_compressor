"""Pydantic models for image endpoint request/response contracts."""

from pydantic import BaseModel, Field


class ImageJobResponse(BaseModel):
    """Response returned by compress, decompress, and embed endpoints."""

    job_id: str = Field(description="Unique identifier of the created processing job")
    status: str = Field(description="Current status of the job (e.g., pending, processing, done, failed)")
    metrics: dict[str, float] = Field(default_factory=dict, description="Metadata and performance metrics computed during the job execution")


class ImageExtractResponse(BaseModel):
    """Response returned by the extract endpoint."""

    job_id: str = Field(description="Unique identifier of the extract job")
    message: str = Field(description="The secret message extracted from the steganographic image")
    metrics: dict[str, float] = Field(default_factory=dict, description="Extraction performance metrics (e.g., processing time)")


class ImageCompareResponse(BaseModel):
    """Response returned by the compare endpoint."""

    job_id: str = Field(description="Unique identifier of the job being compared")
    original_size: int = Field(description="Size of the original uploaded image in bytes")
    result_size: int = Field(description="Size of the processed result image in bytes")
    metrics: dict[str, float] = Field(default_factory=dict, description="Detailed comparison and quality metrics (e.g., psnr, ssim, mse, compression_ratio)")
    original_url: str = Field(description="URL to download the original uploaded image")
    result_url: str = Field(description="URL to download the processed result image")
