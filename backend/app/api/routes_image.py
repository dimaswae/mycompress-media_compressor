"""Image-specific endpoints for compression, steganography, and comparison."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.image import ImageCompareResponse, ImageExtractResponse, ImageJobResponse
from app.services.image_service import (
    compare_image_job,
    compress_image,
    decompress_image,
    embed_message,
    extract_message,
)

router = APIRouter()


@router.post("/image/compress", response_model=ImageJobResponse)
async def compress_image_endpoint(
    file: UploadFile = File(...),
    algorithm: str = Form(...),
    db: Session = Depends(get_db),
) -> ImageJobResponse:
    """Upload an image and compress it using the specified algorithm."""
    file_bytes = await file.read()
    result = compress_image(db, file_bytes, file.filename or "image.png", algorithm)
    return ImageJobResponse(**result)


@router.post("/image/decompress", response_model=ImageJobResponse)
async def decompress_image_endpoint(
    file: UploadFile = File(...),
    algorithm: str = Form(...),
    db: Session = Depends(get_db),
) -> ImageJobResponse:
    """Upload a compressed image and decompress it."""
    file_bytes = await file.read()
    result = decompress_image(db, file_bytes, file.filename or "data.bin", algorithm)
    return ImageJobResponse(**result)


@router.post("/image/embed", response_model=ImageJobResponse)
async def embed_message_endpoint(
    file: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(""),
    algorithm: str | None = Form(None),
    db: Session = Depends(get_db),
) -> ImageJobResponse:
    """Embed a secret message into an image."""
    file_bytes = await file.read()
    result = embed_message(
        db, file_bytes, file.filename or "image.png", message,
        password=password, algorithm=algorithm,
    )
    return ImageJobResponse(**result)


@router.post("/image/extract", response_model=ImageExtractResponse)
async def extract_message_endpoint(
    file: UploadFile = File(...),
    password: str = Form(""),
    algorithm: str | None = Form(None),
    db: Session = Depends(get_db),
) -> ImageExtractResponse:
    """Extract a hidden message from a stego image."""
    file_bytes = await file.read()
    result = extract_message(
        db, file_bytes, file.filename or "image.png",
        password=password, algorithm=algorithm,
    )
    return ImageExtractResponse(**result)


@router.get("/image/{job_id}/compare", response_model=ImageCompareResponse)
async def compare_image_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
) -> ImageCompareResponse:
    """Compare original and processed image for a completed job."""
    result = compare_image_job(db, job_id)
    return ImageCompareResponse(**result)
