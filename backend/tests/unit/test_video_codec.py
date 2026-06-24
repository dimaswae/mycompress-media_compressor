"""Unit tests for core/compression/video_codec.py (VID-01/02)."""

from unittest.mock import patch

import pytest

from app.core.compression.video_codec import VideoCodec
from app.utils.exceptions import AppError


class TestVideoCodec:
    def test_compress_calls_ffmpeg(self) -> None:
        codec = VideoCodec(crf=28)
        with (
            patch("app.core.compression.video_codec.run_ffmpeg") as mock_run,
            patch("app.core.compression.video_codec.Path.exists", return_value=True),
            patch(
                "app.core.compression.video_codec.Path.read_bytes",
                return_value=b"fake-compressed",
            ),
            patch("app.core.compression.video_codec.Path.write_bytes"),
        ):
            result = codec.compress(b"fake-video-data")
            assert result == b"fake-compressed"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "-crf" in args
            assert "28" in args

    def test_decompress_calls_ffmpeg(self) -> None:
        codec = VideoCodec()
        with (
            patch("app.core.compression.video_codec.run_ffmpeg") as mock_run,
            patch("app.core.compression.video_codec.Path.exists", return_value=True),
            patch(
                "app.core.compression.video_codec.Path.read_bytes",
                return_value=b"fake-decompressed",
            ),
            patch("app.core.compression.video_codec.Path.write_bytes"),
        ):
            result = codec.decompress(b"fake-compressed")
            assert result == b"fake-decompressed"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "-crf" in args
            assert "18" in args  # decompress always uses CRF 18

    def test_compress_custom_crf(self) -> None:
        codec = VideoCodec(crf=35)
        with (
            patch("app.core.compression.video_codec.run_ffmpeg") as mock_run,
            patch("app.core.compression.video_codec.Path.exists", return_value=True),
            patch(
                "app.core.compression.video_codec.Path.read_bytes",
                return_value=b"data",
            ),
            patch("app.core.compression.video_codec.Path.write_bytes"),
        ):
            codec.compress(b"data")
            args = mock_run.call_args[0][0]
            idx = args.index("-crf")
            assert args[idx + 1] == "35"

    def test_compress_ffmpeg_failure_raises_app_error(self) -> None:
        codec = VideoCodec()
        with patch(
            "app.core.compression.video_codec.run_ffmpeg",
            side_effect=RuntimeError("ffmpeg not found"),
        ):
            with pytest.raises(AppError, match="VIDEO_COMPRESS_ERROR"):
                codec.compress(b"some-data")

    def test_decompress_ffmpeg_failure_raises_app_error(self) -> None:
        codec = VideoCodec()
        with patch(
            "app.core.compression.video_codec.run_ffmpeg",
            side_effect=RuntimeError("ffmpeg not found"),
        ):
            with pytest.raises(AppError, match="VIDEO_DECOMPRESS_ERROR"):
                codec.decompress(b"some-data")

    def test_compress_missing_output_raises_app_error(self) -> None:
        codec = VideoCodec()
        with patch("app.core.compression.video_codec.run_ffmpeg"):
            with patch(
                "app.core.compression.video_codec.Path.exists",
                return_value=False,
            ):
                with pytest.raises(AppError, match="did not produce"):
                    codec.compress(b"some-data")
