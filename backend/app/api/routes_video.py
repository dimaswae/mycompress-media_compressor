"""Video-specific endpoints for compression, steganography, and comparison."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.video import VideoCompareResponse, VideoExtractResponse, VideoJobResponse
from app.services.video_service import (
    compare_video_job,
    compress_video,
    decompress_video,
    embed_message,
    extract_message,
)

router = APIRouter()


@router.post("/video/compress", response_model=VideoJobResponse)
async def compress_video_endpoint(
    file: UploadFile = File(...),
    crf: int = Form(28),
    db: Session = Depends(get_db),
) -> VideoJobResponse:
    """Upload an MP4 file and compress it at the specified CRF value."""
    file_bytes = await file.read()
    result = compress_video(db, file_bytes, file.filename or "video.mp4", crf=crf)
    return VideoJobResponse(**result)


@router.post("/video/decompress", response_model=VideoJobResponse)
async def decompress_video_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> VideoJobResponse:
    """Upload a compressed MP4 file and decompress it (re-encode at higher quality)."""
    file_bytes = await file.read()
    result = decompress_video(db, file_bytes, file.filename or "video.mp4")
    return VideoJobResponse(**result)


@router.post("/video/embed", response_model=VideoJobResponse)
async def embed_message_endpoint(
    file: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
) -> VideoJobResponse:
    """Embed a secret message into an MP4 video file."""
    file_bytes = await file.read()
    result = embed_message(
        db, file_bytes, file.filename or "video.mp4", message, password=password,
    )
    return VideoJobResponse(**result)


@router.post("/video/extract", response_model=VideoExtractResponse)
async def extract_message_endpoint(
    file: UploadFile = File(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
) -> VideoExtractResponse:
    """Extract a hidden message from a stego MP4 file."""
    file_bytes = await file.read()
    result = extract_message(
        db, file_bytes, file.filename or "video.mp4", password=password,
    )
    return VideoExtractResponse(**result)


@router.get("/video/{job_id}/compare", response_model=VideoCompareResponse)
async def compare_video_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
) -> VideoCompareResponse:
    """Compare original and processed video for a completed job."""
    result = compare_video_job(db, job_id)
    result["original_url"] = f"/api/v1/jobs/{job_id}/download/original"
    result["result_url"] = f"/api/v1/jobs/{job_id}/download"
    return VideoCompareResponse(**result)