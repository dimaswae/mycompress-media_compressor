"""Service-layer orchestration for video compression and steganography."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.compression.video_codec import VideoCodec
from app.core.metrics.common_metrics import compression_ratio, processing_time
from app.core.steganography.video_lsb import VideoLsbCodec
from app.infra.file_validation import validate_extension, validate_magic_bytes, validate_size
from app.infra.storage import load_file, save_result, save_upload
from app.services.job_service import create_job, get_job_status, update_job_status
from app.utils.exceptions import AppError, NotFoundError

_SENTINEL = 999.0


def _sanitize(metrics: dict[str, float]) -> dict[str, float]:
    """Replace non-finite floats with sentinel values for JSON safety."""
    return {
        k: _SENTINEL if v == float("inf") else
           -_SENTINEL if v == float("-inf") else
           0.0 if v != v else v
        for k, v in metrics.items()
    }


def _validate_video_file(file_bytes: bytes, filename: str) -> str:
    """Validate extension, magic bytes, and size. Returns the extension."""
    ext = validate_extension(filename)
    validate_magic_bytes(file_bytes, ext)
    validate_size(file_bytes)
    return ext


def _validate_size_only(file_bytes: bytes) -> None:
    """Validate only the file size (skip extension/magic checks)."""
    validate_size(file_bytes)


def _store_metrics(db: Session, job_id: str, metrics: dict[str, float]) -> None:
    """Persist a sanitized dictionary of metric_name → value."""
    from app.db.metric_repository import add_metric

    for name, value in _sanitize(metrics).items():
        add_metric(db, job_id, name, value)


def compress_video(
    db: Session,
    file_bytes: bytes,
    filename: str,
    crf: int = 28,
) -> dict:
    """Compress a video file via CRF-based re-encoding and create a job."""
    _validate_video_file(file_bytes, filename)

    job = create_job(
        db=db,
        media_type="video",
        operation="compress",
        original_filename=filename,
        original_path="",
        algorithm=str(crf),
        status="processing",
    )
    job_id = job.id

    try:
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        codec = VideoCodec(crf=crf)
        compressed_bytes, compress_ms = processing_time(codec.compress, file_bytes)

        result_ext = ".mp4"
        result_path = save_result(job_id, result_ext, compressed_bytes)
        update_job_status(db, job_id, status="done", result_path=result_path)

        ratio = compression_ratio(len(file_bytes), len(compressed_bytes))

        raw_metrics: dict[str, float] = {
            "compression_ratio": ratio,
            "processing_time_ms": compress_ms,
        }
        metrics = _sanitize(raw_metrics)
        _store_metrics(db, job_id, metrics)

        return {"job_id": job_id, "status": "done", "metrics": metrics}

    except Exception:
        update_job_status(
            db,
            job_id,
            status="failed",
            error_code="COMPRESS_ERROR",
            error_message="Video compression failed",
        )
        raise


def decompress_video(
    db: Session,
    file_bytes: bytes,
    filename: str,
) -> dict:
    """Decompress a video file (re-encode at higher quality)."""
    _validate_size_only(file_bytes)

    job = create_job(
        db=db,
        media_type="video",
        operation="decompress",
        original_filename=filename,
        original_path="",
        algorithm=None,
        status="processing",
    )
    job_id = job.id

    try:
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        codec = VideoCodec()
        decompressed_bytes, decompress_ms = processing_time(codec.decompress, file_bytes)

        result_ext = ".mp4"
        result_path = save_result(job_id, result_ext, decompressed_bytes)
        update_job_status(db, job_id, status="done", result_path=result_path)

        raw_metrics: dict[str, float] = {"processing_time_ms": decompress_ms}
        metrics = _sanitize(raw_metrics)
        _store_metrics(db, job_id, metrics)

        return {"job_id": job_id, "status": "done", "metrics": metrics}

    except Exception:
        update_job_status(
            db,
            job_id,
            status="failed",
            error_code="DECOMPRESS_ERROR",
            error_message="Video decompression failed",
        )
        raise


def embed_message(
    db: Session,
    file_bytes: bytes,
    filename: str,
    message: str,
    password: str = "",
) -> dict:
    """Embed a secret message into an MP4 video file."""
    _validate_video_file(file_bytes, filename)

    job = create_job(
        db=db,
        media_type="video",
        operation="embed",
        original_filename=filename,
        original_path="",
        algorithm=None,
        encrypted=bool(password),
        status="processing",
    )
    job_id = job.id

    try:
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        message_bytes = message.encode("utf-8")
        codec = VideoLsbCodec()
        result_bytes, embed_ms = processing_time(
            codec.embed, file_bytes, message_bytes, password=password
        )
        capacity = codec.capacity(file_bytes)

        result_path = save_result(job_id, ".mp4", result_bytes)
        update_job_status(db, job_id, status="done", result_path=result_path)

        raw_metrics: dict[str, float] = {
            "processing_time_ms": embed_ms,
            "hidden_capacity_bits": float(capacity),
        }
        metrics = _sanitize(raw_metrics)
        _store_metrics(db, job_id, metrics)

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
) -> dict:
    """Extract a hidden message from a stego MP4 file."""
    _validate_video_file(file_bytes, filename)

    job = create_job(
        db=db,
        media_type="video",
        operation="extract",
        original_filename=filename,
        original_path="",
        algorithm=None,
        encrypted=bool(password),
        status="processing",
    )
    job_id = job.id

    try:
        original_path = save_upload(job_id, filename, file_bytes)
        job = get_job_status(db, job_id)
        job.original_path = original_path
        db.commit()

        codec = VideoLsbCodec()
        message_bytes, extract_ms = processing_time(
            codec.extract, file_bytes, password=password
        )
        message_str = message_bytes.decode("utf-8", errors="replace")

        update_job_status(db, job_id, status="done")

        raw_metrics: dict[str, float] = {
            "processing_time_ms": extract_ms,
            "extracted_message_size_bytes": float(len(message_bytes)),
        }
        metrics = _sanitize(raw_metrics)
        _store_metrics(db, job_id, metrics)

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


def compare_video_job(db: Session, job_id: str) -> dict:
    """Return comparison metrics for a completed video job."""
    job = get_job_status(db, job_id)
    if job is None:
        raise NotFoundError("Job not found")
    if job.status != "done":
        raise AppError(code="JOB_NOT_DONE", message="Job is not yet completed")
    if job.original_path is None or job.result_path is None:
        raise AppError(code="MISSING_FILES", message="Original or result file missing")

    original_bytes = load_file(job.original_path)
    result_bytes = load_file(job.result_path)

    from app.db.metric_repository import get_metrics_for_job

    stored_records = get_metrics_for_job(db, job_id)
    stored = {m.metric_name: m.metric_value for m in stored_records}

    return {
        "job_id": job_id,
        "original_size": len(original_bytes),
        "result_size": len(result_bytes),
        "metrics": {**stored},
    }
