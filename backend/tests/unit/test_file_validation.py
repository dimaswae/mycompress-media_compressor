import pytest
from app.infra.file_validation import validate_size
from app.utils.exceptions import FileTooLargeError
from unittest.mock import patch

def test_validate_size_exceeds_limit() -> None:
    # Set limit to 1 MB for testing
    with patch("app.config.settings.upload_max_size_mb", 1):
        # 2 MB data
        large_data = b"x" * (2 * 1024 * 1024)
        with pytest.raises(FileTooLargeError) as exc_info:
            validate_size(large_data)
        assert "exceeds maximum" in str(exc_info.value)
        assert exc_info.value.code == "FILE_TOO_LARGE"

def test_validate_size_within_limit() -> None:
    with patch("app.config.settings.upload_max_size_mb", 1):
        # 0.5 MB data
        small_data = b"x" * (512 * 1024)
        # Should not raise any error
        validate_size(small_data)
