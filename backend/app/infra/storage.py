"""File storage utilities: save, load, delete, quota check."""

import shutil
from pathlib import Path

from app.config import settings
from app.utils.exceptions import StorageQuotaError


def _storage_root() -> Path:
    """Return the configured storage root directory."""
    return Path(settings.storage_dir)


def _job_dir(job_id: str) -> Path:
    """Return the storage path for a given job id."""
    return _storage_root() / job_id


def save_upload(job_id: str, filename: str, data: bytes) -> str:
    """Write an uploaded file to ``storage/{job_id}/original.{ext}``.

    Returns the absolute path of the saved file as a string.
    """
    ext = Path(filename).suffix
    job_path = _job_dir(job_id)
    job_path.mkdir(parents=True, exist_ok=True)
    dest = job_path / f"original{ext}"
    dest.write_bytes(data)
    return str(dest.resolve())


def save_result(job_id: str, ext: str, data: bytes) -> str:
    """Write a result file to ``storage/{job_id}/result.{ext}``.

    Returns the absolute path of the saved file as a string.
    """
    job_path = _job_dir(job_id)
    job_path.mkdir(parents=True, exist_ok=True)
    dest = job_path / f"result{ext}"
    dest.write_bytes(data)
    return str(dest.resolve())


def load_file(file_path: str) -> bytes:
    """Read a file from disk and return its contents as bytes.

    Raises ``FileNotFoundError`` if the path does not exist.
    """
    path = Path(file_path)
    return path.read_bytes()


def delete_job_files(job_id: str) -> None:
    """Recursively delete the storage directory for a job.

    Does nothing if the directory does not exist (no crash).
    """
    job_path = _job_dir(job_id)
    if job_path.exists():
        shutil.rmtree(str(job_path))


def check_quota() -> int:
    """Check whether the storage directory is below the configured quota.

    Returns the current storage usage in bytes.
    Raises ``StorageQuotaError`` if usage exceeds ``settings.storage_quota_gb``.
    """
    storage = _storage_root()
    if not storage.exists():
        storage.mkdir(parents=True, exist_ok=True)
        return 0

    total_bytes = sum(
        f.stat().st_size for f in storage.rglob("*") if f.is_file()
    )
    max_bytes = settings.storage_quota_gb * 1024**3

    if total_bytes >= max_bytes:
        raise StorageQuotaError(
            f"Storage usage {total_bytes} bytes exceeds quota of {max_bytes} bytes "
            f"({settings.storage_quota_gb} GB)"
        )
    return total_bytes
