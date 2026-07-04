"""Service-layer orchestration for image compression and steganography."""

from io import BytesIO
from pathlib import Path

from typing import TypedDict

import numpy as np

class ImageJobDict(TypedDict):
    job_id: str
    status: str
    metrics: dict[str, float]

class ImageExtractDict(TypedDict):
    job_id: str
    message: str
    metrics: dict[str, float]

class ImageCompareDict(TypedDict):
    job_id: str
    original_size: int
    result_size: int
    metrics: dict[str, float]
from PIL import Image
from sqlalchemy.orm import Session

from app.core.compression.registry import get_codec
from app.core.metrics.common_metrics import compression_ratio, processing_time
from app.core.metrics.image_metrics import mse, psnr, ssim
from app.core.steganography.image_lsb import LsbCodec
from app.db.metric_repository import add_metric, get_metrics_for_job
from app.infra.file_validation import (
    validate_extension,
    validate_magic_bytes,
    validate_size,
)
from app.infra.storage import load_file, save_result, save_upload, check_quota
from app.services.job_service import create_job, get_job_status, update_job_status
from app.utils.exceptions import AppError, NotFoundError
from app.utils.service_helpers import sanitize_metrics, store_job_metrics, validate_size_only




def _validate_image_file(file_bytes: bytes, filename: str) -> str:
    """Validate extension, magic bytes, and size. Returns the extension."""
    ext = validate_extension(filename)
    validate_magic_bytes(file_bytes, ext)
    validate_size(file_bytes)
    return ext



def _compute_image_metrics(
    original_bytes: bytes, result_bytes: bytes
) -> dict[str, float]:
    """Compute PSNR, SSIM, MSE between two image byte buffers."""
    try:
        original_img = Image.open(BytesIO(original_bytes)).convert("RGB")
        original_img.load()
        result_img = Image.open(BytesIO(result_bytes)).convert("RGB")
        result_img.load()
    except (Image.UnidentifiedImageError, OSError, ValueError, TypeError) as e:
        from app.utils.exceptions import InvalidImageError
        raise InvalidImageError(f"Invalid or corrupt image data for comparison: {str(e)}")

    orig_arr = np.array(original_img, dtype=np.uint8)
    res_arr = np.array(result_img, dtype=np.uint8)
    raw = {
        "psnr": psnr(orig_arr, res_arr),
        "ssim": ssim(orig_arr, res_arr),
        "mse": mse(orig_arr, res_arr),
    }
    return sanitize_metrics(raw)


def compress_image(
    db: Session,
    file_bytes: bytes,
    filename: str,
    algorithm: str,
) -> ImageJobDict:
    """Compress an image file, create a job, and compute metrics."""
    ext = _validate_image_file(file_bytes, filename)

    job = create_job(
        db=db,
        media_type="image",
        operation="compress",
        original_filename=filename,
        original_path="",
        algorithm=algorithm,
        status="processing",
    )
    job_id = job.id

    try:
        check_quota()
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        codec = get_codec(algorithm)
        compressed_bytes, compress_ms = processing_time(codec.compress, file_bytes)

        result_ext = ".cmp"
        result_path = save_result(job_id, result_ext, compressed_bytes)
        update_job_status(db, job_id, status="done", result_path=result_path)

        ratio = compression_ratio(len(file_bytes), len(compressed_bytes))

        decompressed_bytes = codec.decompress(compressed_bytes)
        img_metrics = _compute_image_metrics(file_bytes, decompressed_bytes)

        raw_metrics: dict[str, float] = {
            "compression_ratio": ratio,
            "processing_time_ms": compress_ms,
            **img_metrics,
        }
        metrics = sanitize_metrics(raw_metrics)
        store_job_metrics(db, job_id, metrics)

        return {"job_id": job_id, "status": "done", "metrics": metrics}

    except Exception:
        update_job_status(
            db,
            job_id,
            status="failed",
            error_code="COMPRESS_ERROR",
            error_message="Image compression failed",
        )
        raise


def decompress_image(
    db: Session,
    file_bytes: bytes,
    filename: str,
    algorithm: str,
) -> ImageJobDict:
    """Decompress a previously compressed image file."""
    validate_size_only(file_bytes)

    job = create_job(
        db=db,
        media_type="image",
        operation="decompress",
        original_filename=filename,
        original_path="",
        algorithm=algorithm,
        status="processing",
    )
    job_id = job.id

    try:
        check_quota()
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        codec = get_codec(algorithm)
        decompressed_bytes, decompress_ms = processing_time(
            codec.decompress, file_bytes
        )

        result_ext = ".bin"
        result_path = save_result(job_id, result_ext, decompressed_bytes)
        update_job_status(db, job_id, status="done", result_path=result_path)

        raw_metrics: dict[str, float] = {"processing_time_ms": decompress_ms}
        metrics = sanitize_metrics(raw_metrics)
        store_job_metrics(db, job_id, metrics)

        return {"job_id": job_id, "status": "done", "metrics": metrics}

    except Exception:
        update_job_status(
            db,
            job_id,
            status="failed",
            error_code="DECOMPRESS_ERROR",
            error_message="Image decompression failed",
        )
        raise


def embed_message(
    db: Session,
    file_bytes: bytes,
    filename: str,
    message: str,
    password: str = "",
    algorithm: str | None = None,
) -> ImageJobDict:
    """Embed a secret message into an image, optionally pre-compressing.

    If a password is provided, the message is encrypted with AES-GCM before
    being embedded via LSB. The salt is stored in the job record.
    """
    _validate_image_file(file_bytes, filename)

    job = create_job(
        db=db,
        media_type="image",
        operation="embed",
        original_filename=filename,
        original_path="",
        algorithm=algorithm,
        encrypted=bool(password),
        status="processing",
    )
    job_id = job.id

    try:
        check_quota()
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        message_bytes = message.encode("utf-8")

        if algorithm:
            codec = get_codec(algorithm)
            message_bytes, compress_ms = processing_time(codec.compress, message_bytes)
        else:
            compress_ms = 0.0

        salt_hex: str | None = None
        if password:
            from app.core.security.aes_cipher import encrypt_bytes

            encrypted = encrypt_bytes(message_bytes, password)
            # Salt is the first 16 bytes of the encrypted payload (for auditing)
            salt_hex = encrypted[:16].hex()
            message_bytes = encrypted

        lsb = LsbCodec()
        result_img, embed_ms = processing_time(lsb.embed, file_bytes, message_bytes)

        buf = BytesIO()
        result_img.save(buf, format="PNG")
        result_bytes = buf.getvalue()

        result_path = save_result(job_id, ".png", result_bytes)
        if salt_hex:
            update_job_status(
                db, job_id, status="done", result_path=result_path, salt=salt_hex
            )
        else:
            update_job_status(db, job_id, status="done", result_path=result_path)

        total_time = compress_ms + embed_ms
        raw_metrics: dict[str, float] = {
            "processing_time_ms": total_time,
            "hidden_capacity_bits": float(lsb.capacity(result_img)),
        }
        metrics = sanitize_metrics(raw_metrics)
        store_job_metrics(db, job_id, metrics)

        return {"job_id": job_id, "status": "done", "metrics": metrics}

    except Exception:
        update_job_status(
            db,
            job_id,
            status="failed",
            error_code="EMBED_ERROR",
            error_message="Message embedding failed",
        )
        raise


def extract_message(
    db: Session,
    file_bytes: bytes,
    filename: str,
    password: str = "",
    algorithm: str | None = None,
) -> ImageExtractDict:
    """Extract a hidden message from a stego image.

    If a password was used during embedding, the extracted payload is decrypted
    using AES-GCM (salt and nonce are embedded in the payload).
    """
    _validate_image_file(file_bytes, filename)

    job = create_job(
        db=db,
        media_type="image",
        operation="extract",
        original_filename=filename,
        original_path="",
        algorithm=algorithm,
        encrypted=bool(password),
        status="processing",
    )
    job_id = job.id

    try:
        check_quota()
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        lsb = LsbCodec()
        extracted_bytes, extract_ms = processing_time(lsb.extract, file_bytes)

        if password:
            from app.core.security.aes_cipher import decrypt_bytes

            extracted_bytes = decrypt_bytes(extracted_bytes, password)

        if algorithm:
            codec = get_codec(algorithm)
            extracted_bytes, decompress_ms = processing_time(
                codec.decompress, extracted_bytes
            )
        else:
            decompress_ms = 0.0

        total_time = extract_ms + decompress_ms
        message_str = extracted_bytes.decode("utf-8", errors="replace")

        update_job_status(db, job_id, status="done")

        raw_metrics: dict[str, float] = {
            "processing_time_ms": total_time,
            "extracted_message_size_bytes": float(len(extracted_bytes)),
        }
        metrics = sanitize_metrics(raw_metrics)
        store_job_metrics(db, job_id, metrics)

        return {
            "job_id": job_id,
            "message": message_str,
            "metrics": metrics,
        }

    except Exception:
        update_job_status(
            db,
            job_id,
            status="failed",
            error_code="EXTRACT_ERROR",
            error_message="Message extraction failed",
        )
        raise


def compare_image_job(db: Session, job_id: str) -> ImageCompareDict:
    """Return comparison metrics for a completed image job."""
    job = get_job_status(db, job_id)
    if job is None:
        raise NotFoundError("Job not found")
    if job.status != "done":
        raise AppError(code="JOB_NOT_DONE", message="Job is not yet completed")
    if job.original_path is None or job.result_path is None:
        raise AppError(code="MISSING_FILES", message="Original or result file missing")

    original_bytes = load_file(job.original_path)
    result_bytes = load_file(job.result_path)

    if job.operation == "compress" and job.algorithm:
        codec = get_codec(job.algorithm)
        compare_bytes = codec.decompress(result_bytes)
    else:
        compare_bytes = result_bytes

    img_metrics = _compute_image_metrics(original_bytes, compare_bytes)

    stored_records = get_metrics_for_job(db, job_id)
    stored = {m.metric_name: m.metric_value for m in stored_records}

    return {
        "job_id": job_id,
        "original_size": len(original_bytes),
        "result_size": len(result_bytes),
        "metrics": {**stored, **img_metrics},
    }
