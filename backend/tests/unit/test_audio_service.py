"""Unit tests for services/audio_service.py (AUD-09, AUD-10, AUD-14, AUD-15)."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.db.models import Job
from app.services.audio_service import (
    compare_audio_job,
    compress_audio,
    decompress_audio,
    embed_message,
    extract_message,
)
from app.utils.exceptions import AppError, NotFoundError, UnsupportedFormatError


class TestCompressAudio:
    def test_compress_wav_success(self, db_session: Session, sample_wav_bytes: bytes) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-mp3-data"

            result = compress_audio(db_session, sample_wav_bytes, "test.wav", bitrate="128k")
            assert result["status"] == "done"
            assert "job_id" in result
            assert "metrics" in result
            assert result["metrics"]["compression_ratio"] > 0
            assert "processing_time_ms" in result["metrics"]

    def test_compress_invalid_extension_raises(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        with pytest.raises(UnsupportedFormatError):
            compress_audio(db_session, sample_wav_bytes, "test.txt", bitrate="128k")

    def test_compress_ffmpeg_failure_marks_job_failed(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.compress.side_effect = AppError(
                code="AUDIO_COMPRESS_ERROR", message="fail"
            )

            with pytest.raises(AppError):
                compress_audio(db_session, sample_wav_bytes, "test.wav")

            failed_job = (
                db_session.query(Job)
                .filter(Job.status == "failed")
                .first()
            )
            assert failed_job is not None
            assert failed_job.error_code == "COMPRESS_ERROR"

    def test_compress_mp3_input_is_accepted(self, db_session: Session, sample_mp3_bytes: bytes) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"fake-mp3-data"

            result = compress_audio(db_session, sample_mp3_bytes, "test.mp3", bitrate="128k")
            assert result["status"] == "done"


class TestDecompressAudio:
    def test_decompress_success(self, db_session: Session) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.return_value = b"fake-wav-data"

            result = decompress_audio(
                db_session, b"fake-mp3-data", "audio.mp3", bitrate="128k"
            )
            assert result["status"] == "done"
            assert "processing_time_ms" in result["metrics"]

    def test_decompress_ffmpeg_failure_raises(
        self, db_session: Session
    ) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.decompress.side_effect = AppError(
                code="AUDIO_DECOMPRESS_ERROR", message="fail"
            )

            with pytest.raises(AppError):
                decompress_audio(db_session, b"bad-data", "audio.mp3")


class TestEmbedMessage:
    def test_embed_success(self, db_session: Session, sample_wav_bytes: bytes) -> None:
        result = embed_message(db_session, sample_wav_bytes, "test.wav", "hello")
        assert result["status"] == "done"
        assert "job_id" in result
        assert "hidden_capacity_bits" in result["metrics"]

    def test_embed_with_password(self, db_session: Session, sample_wav_bytes: bytes) -> None:
        result = embed_message(db_session, sample_wav_bytes, "test.wav", "secret", password="p@ss")
        assert result["status"] == "done"

    def test_embed_invalid_extension_raises(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        with pytest.raises(UnsupportedFormatError):
            embed_message(db_session, sample_wav_bytes, "test.txt", "msg")


class TestExtractMessage:
    def test_extract_roundtrip(self, db_session: Session, sample_wav_bytes: bytes) -> None:
        msg = "Hello WAV!"
        emb_result = embed_message(db_session, sample_wav_bytes, "test.wav", msg)
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        ext_result = extract_message(db_session, stego_bytes, "stego.wav")
        assert ext_result["message"] == msg

    def test_extract_with_password(self, db_session: Session, sample_wav_bytes: bytes) -> None:
        password = "correct"
        emb_result = embed_message(
            db_session, sample_wav_bytes, "test.wav", "hidden", password=password
        )
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        ext_result = extract_message(db_session, stego_bytes, "stego.wav", password=password)
        assert ext_result["message"] == "hidden"

    def test_extract_wrong_password_raises(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        emb_result = embed_message(
            db_session, sample_wav_bytes, "test.wav", "secret", password="correct"
        )
        job_id = emb_result["job_id"]

        from app.infra.storage import load_file
        from app.services.job_service import get_job_status
        job = get_job_status(db_session, job_id)
        stego_bytes = load_file(job.result_path)

        with pytest.raises(AppError):
            extract_message(db_session, stego_bytes, "stego.wav", password="wrong")

    def test_extract_invalid_extension_raises(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        with pytest.raises(UnsupportedFormatError):
            extract_message(db_session, sample_wav_bytes, "test.txt")


class TestCompareAudioJob:
    def test_compare_completed_job(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.compress.return_value = b"compressed"

            result = compress_audio(db_session, sample_wav_bytes, "test.wav")
            job_id = result["job_id"]

            compare = compare_audio_job(db_session, job_id)
            assert compare["job_id"] == job_id
            assert "compression_ratio" in compare["metrics"]
            assert "processing_time_ms" in compare["metrics"]

    def test_compare_nonexistent_job_raises(self, db_session: Session) -> None:
        with pytest.raises(NotFoundError):
            compare_audio_job(db_session, "no-such-job")

    def test_compare_incomplete_job_raises(
        self, db_session: Session, sample_wav_bytes: bytes
    ) -> None:
        with patch(
            "app.services.audio_service.AudioBitrateCodec"
        ) as MockCodec:
            instance = MockCodec.return_value
            instance.compress.side_effect = AppError(
                code="AUDIO_COMPRESS_ERROR", message="fail"
            )

            with pytest.raises(AppError):
                compress_audio(db_session, sample_wav_bytes, "test.wav")
