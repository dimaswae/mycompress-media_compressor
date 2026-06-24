"""Custom exception hierarchy for application errors."""


class AppError(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class UnsupportedFormatError(AppError):
    """Raised when a file format is not supported."""

    def __init__(self, message: str = "Unsupported file format") -> None:
        super().__init__(code="UNSUPPORTED_FORMAT", message=message)


class CapacityExceededError(AppError):
    """Raised when a message exceeds embedding capacity."""

    def __init__(self, message: str = "Message exceeds available capacity") -> None:
        super().__init__(code="CAPACITY_EXCEEDED", message=message)


class FFmpegTimeoutError(AppError):
    """Raised when an FFmpeg subprocess times out."""

    def __init__(self, message: str = "FFmpeg process timed out") -> None:
        super().__init__(code="FFMPEG_TIMEOUT", message=message)


class DecryptionError(AppError):
    """Raised when decryption fails (wrong password, corrupt data)."""

    def __init__(self, message: str = "Decryption failed") -> None:
        super().__init__(code="DECRYPTION_FAILED", message=message)


class StorageQuotaError(AppError):
    """Raised when storage quota is exceeded."""

    def __init__(self, message: str = "Storage quota exceeded") -> None:
        super().__init__(code="STORAGE_QUOTA_EXCEEDED", message=message)
