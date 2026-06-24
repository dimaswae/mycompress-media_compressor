"""Unit tests for core/compression/audio_bitrate.py (AUD-01, AUD-02)."""

from unittest.mock import patch

import pytest

from app.core.compression.audio_bitrate import AudioBitrateCodec
from app.utils.exceptions import AppError


class TestAudioBitrateCodec:
    def test_compress_calls_ffmpeg(self) -> None:
        codec = AudioBitrateCodec(bitrate="128k")
        with (
            patch("app.core.compression.audio_bitrate.run_ffmpeg") as mock_run,
            patch("app.core.compression.audio_bitrate.Path.exists", return_value=True),
            patch(
                "app.core.compression.audio_bitrate.Path.read_bytes",
                return_value=b"fake-mp3-data",
            ),
            patch("app.core.compression.audio_bitrate.Path.write_bytes"),
        ):
            result = codec.compress(b"fake-wav-data")
            assert result == b"fake-mp3-data"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "-b:a" in args
            assert "128k" in args

    def test_decompress_calls_ffmpeg(self) -> None:
        codec = AudioBitrateCodec()
        with (
            patch("app.core.compression.audio_bitrate.run_ffmpeg") as mock_run,
            patch("app.core.compression.audio_bitrate.Path.exists", return_value=True),
            patch(
                "app.core.compression.audio_bitrate.Path.read_bytes",
                return_value=b"fake-wav-data",
            ),
            patch("app.core.compression.audio_bitrate.Path.write_bytes"),
        ):
            result = codec.decompress(b"fake-mp3-data")
            assert result == b"fake-wav-data"
            mock_run.assert_called_once()

    def test_compress_ffmpeg_failure_raises_app_error(self) -> None:
        codec = AudioBitrateCodec()
        with patch(
            "app.core.compression.audio_bitrate.run_ffmpeg",
            side_effect=RuntimeError("ffmpeg not found"),
        ):
            with pytest.raises(AppError, match="AUDIO_COMPRESS_ERROR"):
                codec.compress(b"some-data")

    def test_decompress_ffmpeg_failure_raises_app_error(self) -> None:
        codec = AudioBitrateCodec()
        with patch(
            "app.core.compression.audio_bitrate.run_ffmpeg",
            side_effect=RuntimeError("ffmpeg not found"),
        ):
            with pytest.raises(AppError, match="AUDIO_DECOMPRESS_ERROR"):
                codec.decompress(b"some-data")

    def test_compress_missing_output_raises_app_error(self) -> None:
        codec = AudioBitrateCodec()
        with patch("app.core.compression.audio_bitrate.run_ffmpeg"):
            with patch(
                "app.core.compression.audio_bitrate.Path.exists",
                return_value=False,
            ):
                with pytest.raises(AppError, match="did not produce"):
                    codec.compress(b"some-data")

    def test_unknown_bitrate_still_forwards_to_ffmpeg(self) -> None:
        codec = AudioBitrateCodec(bitrate="999k")
        with (
            patch("app.core.compression.audio_bitrate.run_ffmpeg") as mock_run,
            patch("app.core.compression.audio_bitrate.Path.exists", return_value=True),
            patch(
                "app.core.compression.audio_bitrate.Path.read_bytes",
                return_value=b"data",
            ),
            patch("app.core.compression.audio_bitrate.Path.write_bytes"),
        ):
            codec.compress(b"data")
            args = mock_run.call_args[0][0]
            idx = args.index("-b:a")
            assert args[idx + 1] == "999k"
