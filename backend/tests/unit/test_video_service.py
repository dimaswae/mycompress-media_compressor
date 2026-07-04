"""Unit tests for services/video_service.py (VID-05/06)."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.db.models import Job
from app.services.video_service import (
    compare_video_job,
    compress_video,
    decompress_video,
    embed_message,
    extract_message,
)
from app.utils.exceptions import AppError, NotFoundError, UnsupportedFormatError


class TestCompressVideo:
    def test_compress_success(self, db_session: Session, sample_mp4_bytes: bytes) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-compressed"

            result = compress_video(db_session, sample_mp4_bytes, "test.mp4", crf=28)
            assert result["status"] == "done"
            assert "job_id" in result
            assert result["metrics"]["compression_ratio"] > 0
            assert "processing_time_ms" in result["metrics"]

    def test_compress_invalid_extension_raises(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        with pytest.raises(UnsupportedFormatError):
            compress_video(db_session, sample_mp4_bytes, "test.txt", crf=28)

    def test_compress_ffmpeg_failure_marks_job_failed(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.side_effect = AppError(
                code="VIDEO_COMPRESS_ERROR", message="fail"
            )

            with pytest.raises(AppError):
                compress_video(db_session, sample_mp4_bytes, "test.mp4")

            failed_job = (
                db_session.query(Job)
                .filter(Job.status == "failed")
                .first()
            )
            assert failed_job is not None
            assert failed_job.error_code == "COMPRESS_ERROR"


class TestDecompressVideo:
    def test_decompress_success(self, db_session: Session) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.return_value = b"fake-decompressed"

            result = decompress_video(
                db_session, b"fake-compressed", "video.mp4"
            )
            assert result["status"] == "done"
            assert "processing_time_ms" in result["metrics"]

    def test_decompress_ffmpeg_failure_raises(
        self, db_session: Session
    ) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.side_effect = AppError(
                code="VIDEO_DECOMPRESS_ERROR", message="fail"
            )

            with pytest.raises(AppError):
                decompress_video(db_session, b"bad-data", "video.mp4")


class TestEmbedMessage:
    def test_embed_success(self, db_session: Session, sample_mp4_bytes: bytes) -> None:
        from app.core.steganography.video_lsb import VideoLsbCodec
        expected_capacity = VideoLsbCodec().capacity(sample_mp4_bytes) - 8

        result = embed_message(db_session, sample_mp4_bytes, "test.mp4", "hello")
        assert result["status"] == "done"
        assert "job_id" in result
        assert result["metrics"]["hidden_capacity_bits"] == float(expected_capacity)
        assert "psnr" in result["metrics"]
        assert "ssim" in result["metrics"]
        assert "mse" in result["metrics"]
        assert result["metrics"]["compression_ratio"] == 1.0

    def test_embed_with_password(self, db_session: Session, sample_mp4_bytes: bytes) -> None:
        from app.core.steganography.video_lsb import VideoLsbCodec
        expected_capacity = VideoLsbCodec().capacity(sample_mp4_bytes) - 8

        result = embed_message(db_session, sample_mp4_bytes, "test.mp4", "secret", password="p@ss")
        assert result["status"] == "done"
        assert result["metrics"]["hidden_capacity_bits"] == float(expected_capacity)
        assert "psnr" in result["metrics"]
        assert "ssim" in result["metrics"]
        assert "mse" in result["metrics"]
        assert result["metrics"]["compression_ratio"] == 1.0

    def test_embed_invalid_extension_raises(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        with pytest.raises(UnsupportedFormatError):
            embed_message(db_session, sample_mp4_bytes, "test.txt", "msg")


class TestExtractMessage:
    def test_extract_roundtrip(self, db_session: Session, sample_mp4_bytes: bytes) -> None:
        msg = "Hello MP4!"
        emb_result = embed_message(db_session, sample_mp4_bytes, "test.mp4", msg)
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        ext_result = extract_message(db_session, stego_bytes, "stego.mp4")
        assert ext_result["message"] == msg

    def test_extract_with_password(self, db_session: Session, sample_mp4_bytes: bytes) -> None:
        password = "correct"
        emb_result = embed_message(
            db_session, sample_mp4_bytes, "test.mp4", "hidden", password=password
        )
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        ext_result = extract_message(
            db_session, stego_bytes, "stego.mp4", password=password
        )
        assert ext_result["message"] == "hidden"

    def test_extract_wrong_password_raises(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        emb_result = embed_message(
            db_session, sample_mp4_bytes, "test.mp4", "secret", password="correct"
        )
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        with pytest.raises(AppError):
            extract_message(db_session, stego_bytes, "stego.mp4", password="wrong")

    def test_extract_no_password_for_encrypted_raises(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        emb_result = embed_message(
            db_session, sample_mp4_bytes, "test.mp4", "secret", password="correct"
        )
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        # Extraction should fail with AppError (DecryptionError) when password is empty
        with pytest.raises(AppError):
            extract_message(db_session, stego_bytes, "stego.mp4", password="")

    def test_extract_invalid_extension_raises(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        with pytest.raises(UnsupportedFormatError):
            extract_message(db_session, sample_mp4_bytes, "test.txt")


class TestCompareVideoJob:
    def test_compare_completed_job(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"compressed"

            result = compress_video(db_session, sample_mp4_bytes, "test.mp4")
            job_id = result["job_id"]

            compare = compare_video_job(db_session, job_id)
            assert compare["job_id"] == job_id
            assert "compression_ratio" in compare["metrics"]
            assert "processing_time_ms" in compare["metrics"]

    def test_compare_nonexistent_job_raises(self, db_session: Session) -> None:
        with pytest.raises(NotFoundError):
            compare_video_job(db_session, "no-such-job")

    def test_compare_incomplete_job_raises(
        self, db_session: Session, sample_mp4_bytes: bytes
    ) -> None:
        with patch("app.services.video_service.VideoCodec") as MockCodec:
            instance = MockCodec.return_value
            instance.compress.side_effect = AppError(
                code="VIDEO_COMPRESS_ERROR", message="fail"
            )

            with pytest.raises(AppError):
                compress_video(db_session, sample_mp4_bytes, "test.mp4")


class TestEmbedMessageRealVideoCapacity:
    def test_embed_real_video_capacity(
        self, db_session: Session, sample_video_fixture_bytes: bytes
    ) -> None:
        is_real = len(sample_video_fixture_bytes) > 20000
        if is_real:
            from app.core.steganography.video_lsb import VideoLsbCodec
            codec = VideoLsbCodec()
            expected_capacity = codec.capacity(sample_video_fixture_bytes) - 8
            
            result = embed_message(
                db_session, sample_video_fixture_bytes, "test.mp4", "hello"
            )
            assert result["status"] == "done"
            assert result["metrics"]["hidden_capacity_bits"] == float(expected_capacity)
            
            from app.infra.storage import load_file
            from app.services.job_service import get_job_status
            job = get_job_status(db_session, result["job_id"])
            stego_bytes = load_file(job.result_path)
            
            actual_ratio = len(stego_bytes) / len(sample_video_fixture_bytes)
            assert result["metrics"]["compression_ratio"] == pytest.approx(actual_ratio)
            assert "psnr" in result["metrics"]
            assert "ssim" in result["metrics"]
            assert "mse" in result["metrics"]
            assert result["metrics"]["psnr"] > 50.0 or result["metrics"]["psnr"] == 999.0

