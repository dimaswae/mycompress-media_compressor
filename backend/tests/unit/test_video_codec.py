"""Unit tests for core/compression/video_codec.py (VID-01/02)."""

from unittest.mock import patch, mock_open

import pytest

from app.core.compression.video_codec import VideoCodec
from app.utils.exceptions import AppError


class TestVideoCodec:
    def test_compress_calls_ffmpeg(self) -> None:
        codec = VideoCodec(crf=28)
        with (
            patch("app.core.compression.video_codec.run_ffmpeg") as mock_run,
            patch("app.core.compression.video_codec.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=b"fake-compressed")),
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
            patch("builtins.open", mock_open(read_data=b"fake-decompressed")),
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
            patch("builtins.open", mock_open(read_data=b"data")),
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

    def test_compress_chunked_read_write(self) -> None:
        codec = VideoCodec(crf=28)
        
        # 150 KB input data
        input_data = b"x" * (150 * 1024)
        
        # Prepare mock open that returns 100 KB data
        m_open = mock_open(read_data=b"y" * (100 * 1024))
        
        with (
            patch("app.core.compression.video_codec.run_ffmpeg"),
            patch("app.core.compression.video_codec.Path.exists", return_value=True),
            patch("builtins.open", m_open),
        ):
            result = codec.compress(input_data)
            
            # Verify result output
            assert result == b"y" * (100 * 1024)
            
            # Verify writing was chunked (64KB chunks)
            # We expect 3 write calls for 150KB: 64KB, 64KB, 22KB
            write_mock = m_open().write
            assert write_mock.call_count == 3
            write_mock.assert_any_call(b"x" * (64 * 1024))
            write_mock.assert_any_call(b"x" * (22 * 1024))

            # Verify reading was chunked (64KB chunks)
            read_mock = m_open().read
            # mock_open's read behavior: returns the whole read_data if read() is called,
            # but if read(size) is called, it returns chunk by chunk if configured or mock_open handles it.
            # We assert read_mock was called with 64KB.
            read_mock.assert_any_call(64 * 1024)

