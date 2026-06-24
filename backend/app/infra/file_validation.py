"""File validation utilities: extension whitelist, magic-byte sniffing, size cap."""

import os
from pathlib import Path

from app.config import settings
from app.utils.exceptions import UnsupportedFormatError

EXTENSION_WHITELIST: set[str] = {".png", ".jpg", ".jpeg", ".wav", ".mp3", ".mp4"}

# Each format maps to a list of *alternative* signature groups.
# Each group is a list of (offset, bytes) pairs that ALL must match.
# If ANY group matches, the format is considered valid.
MAGIC_GROUPS: dict[str, list[list[tuple[int, bytes]]]] = {
    "png": [[(0, b"\x89PNG\r\n\x1a\n")]],
    "jpg": [[(0, b"\xff\xd8\xff")]],
    "jpeg": [[(0, b"\xff\xd8\xff")]],
    "wav": [[(0, b"RIFF"), (8, b"WAVE")]],
    "mp3": [
        [(0, b"\xff\xfb")],
        [(0, b"\xff\xf3")],
        [(0, b"\xff\xf2")],
        [(0, b"ID3")],
    ],
    "mp4": [
        [(0, b"\x00\x00\x00\x18ftypmp4")],
        [(4, b"ftyp")],
    ],
}

EXTENSION_TO_TYPE: dict[str, str] = {
    ".png": "png",
    ".jpg": "jpg",
    ".jpeg": "jpeg",
    ".wav": "wav",
    ".mp3": "mp3",
    ".mp4": "mp4",
}


def validate_extension(filename: str) -> str:
    """Check that the file extension is in the supported whitelist.

    Returns the normalized extension (lowercase, with dot).
    Raises ``UnsupportedFormatError`` if the extension is not allowed.
    """
    ext = Path(filename).suffix.lower()
    if ext not in EXTENSION_WHITELIST:
        raise UnsupportedFormatError(
            f"Unsupported extension '{ext}'. Allowed: {', '.join(sorted(EXTENSION_WHITELIST))}"
        )
    return ext


def validate_magic_bytes(data: bytes, extension: str) -> None:
    """Verify that the file's magic bytes match the declared extension.

    Each format may have multiple alternative signature groups (OR logic).
    Within a group, all (offset, pattern) pairs must match (AND logic).
    Raises ``UnsupportedFormatError`` on mismatch.
    """
    file_type = EXTENSION_TO_TYPE.get(extension.lower())
    if file_type is None:
        raise UnsupportedFormatError(f"No magic-byte signature known for extension '{extension}'")

    groups = MAGIC_GROUPS.get(file_type)
    if groups is None or len(groups) == 0:
        return

    for group in groups:
        if all(
            offset + len(magic) <= len(data) and data[offset : offset + len(magic)] == magic
            for offset, magic in group
        ):
            return

    raise UnsupportedFormatError(
        f"File content does not match expected signature for '{extension}'"
    )


def validate_size(data: bytes) -> None:
    """Check that the data size does not exceed the configured upload limit.

    Raises ``UnsupportedFormatError`` (semantically a validation error) when
    the payload exceeds ``settings.upload_max_size_mb``.
    """
    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise UnsupportedFormatError(
            f"File size {len(data)} bytes exceeds maximum of {max_bytes} bytes "
            f"({settings.upload_max_size_mb} MB)"
        )


def get_file_size(path: Path) -> int:
    """Return the total size of a file or directory in bytes."""
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        total = 0
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total
    return 0
