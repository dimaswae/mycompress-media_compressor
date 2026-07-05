"""Tests for infra/storage.py."""

from pathlib import Path

import pytest

from app.config import settings
from app.utils.exceptions import StorageQuotaError


class TestSaveUpload:
    """INF-04: save_upload()."""

    def test_save_upload_creates_file(self, tmp_storage: Path, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_upload

        job_id = "test-upload-job"
        data = b"image data here"
        path = save_upload(job_id, "photo.png", data)

        saved = Path(path)
        assert saved.exists()
        assert saved.read_bytes() == data
        assert saved.name == "original.png"
        assert str(tmp_storage / job_id) in path

    def test_save_upload_returns_absolute_path(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_upload

        path = save_upload("job-2", "clip.mp4", b"video data")
        assert Path(path).is_absolute()


class TestSaveResult:
    """INF-05: save_result()."""

    def test_save_result_creates_file(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_result

        job_id = "test-result-job"
        data = b"compressed data"
        path = save_result(job_id, ".bin", data)

        saved = Path(path)
        assert saved.exists()
        assert saved.read_bytes() == data
        assert saved.name == "result.bin"

    def test_save_result_different_extension(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_result

        path = save_result("job-3", ".png", b"result image")
        assert Path(path).name == "result.png"


class TestLoadFile:
    """INF-06: load_file()."""

    def test_load_existing_file(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_upload, load_file

        path = save_upload("load-test", "doc.png", b"hello bytes")
        loaded = load_file(path)
        assert loaded == b"hello bytes"

    def test_load_nonexistent_file_raises(self) -> None:
        from app.infra.storage import load_file

        with pytest.raises(FileNotFoundError):
            load_file(r"C:\nonexistent\path\file.txt")


class TestDeleteJobFiles:
    """INF-06: delete_job_files()."""

    def test_delete_existing_directory(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_upload, delete_job_files

        save_upload("del-test", "file.png", b"data")
        job_dir = tmp_storage / "del-test"
        assert job_dir.exists()

        delete_job_files("del-test")
        assert not job_dir.exists()

    def test_delete_nonexistent_job_does_not_crash(self) -> None:
        from app.infra.storage import delete_job_files

        delete_job_files("nonexistent-job")

    def test_delete_removes_nested_files(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_upload, save_result, delete_job_files

        save_upload("nested", "a.png", b"original")
        save_result("nested", ".png", b"result")
        assert (tmp_storage / "nested").exists()

        delete_job_files("nested")
        assert not (tmp_storage / "nested").exists()


class TestCheckQuota:
    """INF-10: check_quota()."""

    def test_empty_storage_under_quota(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import check_quota

        usage = check_quota()
        assert isinstance(usage, int)
        assert usage == 0

    def test_small_files_under_quota(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        from app.infra.storage import save_upload, check_quota

        save_upload("q-test", "f.png", b"x" * 1024)
        usage = check_quota()
        assert usage >= 1024

    def test_quota_exceeded_raises(self, tmp_storage, monkeypatch) -> None:
        monkeypatch.setattr(settings, "storage_dir", str(tmp_storage))
        monkeypatch.setattr(settings, "storage_quota_gb", 0)
        from app.infra.storage import save_upload, check_quota

        save_upload("big", "f.png", b"hello")
        with pytest.raises(StorageQuotaError) as exc:
            check_quota()
        assert "STORAGE_QUOTA_EXCEEDED" in str(exc.value)
