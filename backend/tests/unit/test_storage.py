import pytest
from unittest.mock import patch, MagicMock
from app.infra.storage import check_quota
from app.services.image_service import compress_image
from app.utils.exceptions import StorageQuotaError

def test_check_quota_within_limit() -> None:
    with patch("app.infra.storage._storage_root") as mock_root, \
         patch("app.config.settings.storage_quota_gb", 5):
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.stat.return_value.st_size = 100 * 1024 * 1024  # 100 MB
        
        mock_path.rglob.return_value = [mock_file1]
        mock_root.return_value = mock_path
        
        usage = check_quota()
        assert usage == 100 * 1024 * 1024

def test_check_quota_exceeds_limit() -> None:
    with patch("app.infra.storage._storage_root") as mock_root, \
         patch("app.config.settings.storage_quota_gb", 1):
        
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.stat.return_value.st_size = 2 * 1024 * 1024 * 1024  # 2 GB
        
        mock_path.rglob.return_value = [mock_file1]
        mock_root.return_value = mock_path
        
        with pytest.raises(StorageQuotaError) as exc_info:
            check_quota()
        assert "exceeds quota" in str(exc_info.value)

def test_compress_image_quota_exceeded(db_session, sample_png_bytes) -> None:
    with patch("app.services.image_service.check_quota", side_effect=StorageQuotaError("Quota exceeded")):
        with pytest.raises(StorageQuotaError):
            compress_image(db_session, sample_png_bytes, "test.png", "rle")
