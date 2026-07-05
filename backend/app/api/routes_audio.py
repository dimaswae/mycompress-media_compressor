"""Audio-specific endpoints for compression, steganography, and comparison."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.audio import AudioCompareResponse, AudioExtractResponse, AudioJobResponse
from app.services.audio_service import (
    compare_audio_job,
    compress_audio,
    decompress_audio,
    embed_message,
    extract_message,
)

router = APIRouter()


@router.post("/audio/compress", response_model=AudioJobResponse)
async def compress_audio_endpoint(
    file: UploadFile = File(...),
    bitrate: str = Form("128k"),
    db: Session = Depends(get_db),
) -> AudioJobResponse:
    """Upload a WAV file and compress it to MP3 at the specified bitrate."""
    file_bytes = await file.read()
    result = compress_audio(db, file_bytes, file.filename or "audio.wav", bitrate=bitrate)
    return AudioJobResponse(**result)


@router.post("/audio/decompress", response_model=AudioJobResponse)
async def decompress_audio_endpoint(
    file: UploadFile = File(...),
    bitrate: str = Form("128k"),
    db: Session = Depends(get_db),
) -> AudioJobResponse:
    """Upload an MP3 file and decompress it back to WAV."""
    file_bytes = await file.read()
    result = decompress_audio(db, file_bytes, file.filename or "audio.mp3", bitrate=bitrate)
    return AudioJobResponse(**result)


@router.post("/audio/embed", response_model=AudioJobResponse)
async def embed_message_endpoint(
    file: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
) -> AudioJobResponse:
    """Embed a secret message into a WAV audio file."""
    file_bytes = await file.read()
    result = embed_message(
        db, file_bytes, file.filename or "audio.wav", message, password=password,
    )
    return AudioJobResponse(**result)


@router.post("/audio/extract", response_model=AudioExtractResponse)
async def extract_message_endpoint(
    file: UploadFile = File(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
) -> AudioExtractResponse:
    """Extract a hidden message from a stego WAV file."""
    file_bytes = await file.read()
    result = extract_message(
        db, file_bytes, file.filename or "audio.wav", password=password,
    )
    return AudioExtractResponse(**result)


@router.get("/audio/{job_id}/compare", response_model=AudioCompareResponse)
async def compare_audio_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
) -> AudioCompareResponse:
    """Compare original and processed audio for a completed job."""
    result = compare_audio_job(db, job_id)
    result["original_url"] = f"/api/v1/jobs/{job_id}/download/original"
    result["result_url"] = f"/api/v1/jobs/{job_id}/download"
    return AudioCompareResponse(**result)
