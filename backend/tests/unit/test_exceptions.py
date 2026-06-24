"""Unit tests for ``utils/exceptions.py`` (API-02).

Verifies every custom exception class exists, subclasses ``AppError``, and
carries ``code`` + ``message`` attributes.
"""

from app.utils.exceptions import (
    AppError,
    CapacityExceededError,
    DecryptionError,
    FFmpegTimeoutError,
    StorageQuotaError,
    UnsupportedFormatError,
)


def _assert_exc_attrs(exc: AppError, expected_code: str, expected_message: str) -> None:
    assert isinstance(exc, AppError)
    assert exc.code == expected_code
    assert exc.message == expected_message


class TestUnsupportedFormatError:
    def test_default_message(self) -> None:
        exc = UnsupportedFormatError()
        _assert_exc_attrs(exc, "UNSUPPORTED_FORMAT", "Unsupported file format")

    def test_custom_message(self) -> None:
        exc = UnsupportedFormatError("Custom message")
        _assert_exc_attrs(exc, "UNSUPPORTED_FORMAT", "Custom message")


class TestCapacityExceededError:
    def test_default_message(self) -> None:
        exc = CapacityExceededError()
        _assert_exc_attrs(exc, "CAPACITY_EXCEEDED", "Message exceeds available capacity")


class TestFFmpegTimeoutError:
    def test_default_message(self) -> None:
        exc = FFmpegTimeoutError()
        _assert_exc_attrs(exc, "FFMPEG_TIMEOUT", "FFmpeg process timed out")


class TestDecryptionError:
    def test_default_message(self) -> None:
        exc = DecryptionError()
        _assert_exc_attrs(exc, "DECRYPTION_FAILED", "Decryption failed")


class TestStorageQuotaError:
    def test_default_message(self) -> None:
        exc = StorageQuotaError()
        _assert_exc_attrs(exc, "STORAGE_QUOTA_EXCEEDED", "Storage quota exceeded")
