"""Unit tests for core/metrics/video_metrics.py (VID-11/12)."""

import subprocess
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.metrics.video_metrics import (
    _average_metric,
    _probe_video_dimensions,
    extract_frames,
    mse,
    psnr,
    ssim,
)


class TestProbeVideoDimensions:
    def test_probe_success(self) -> None:
        with patch(
            "app.core.metrics.video_metrics.run_ffmpeg", return_value="640,480\n"
        ):
            result = _probe_video_dimensions("/fake/path.mp4")
            assert result == (640, 480)

    def test_probe_failure_returncode(self) -> None:
        with patch(
            "app.core.metrics.video_metrics.run_ffmpeg", side_effect=Exception("Failed")
        ):
            assert _probe_video_dimensions("/fake/path.mp4") is None

    def test_probe_timeout_returns_none(self) -> None:
        from app.utils.exceptions import FFmpegTimeoutError
        with patch(
            "app.core.metrics.video_metrics.run_ffmpeg",
            side_effect=FFmpegTimeoutError("Timeout"),
        ):
            assert _probe_video_dimensions("/fake/path.mp4") is None


class TestExtractFrames:
    def test_extract_success(self) -> None:
        width, height = 4, 4
        frame_bytes = width * height * 3
        num_frames = 3
        fake_raw = b"\x80" * frame_bytes * num_frames

        def mock_run_ffmpeg(args, timeout=None):
            out_path = args[-1]
            with open(out_path, "wb") as f:
                f.write(fake_raw)
            return ""

        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(width, height),
            ),
            patch("app.core.metrics.video_metrics.run_ffmpeg", side_effect=mock_run_ffmpeg),
        ):
            frames = extract_frames(b"fake-mp4", max_frames=num_frames)
            assert len(frames) == num_frames
            for frame in frames:
                assert frame.shape == (height, width, 3)
                assert frame.dtype == np.uint8

    def test_extract_probe_failure_returns_empty(self) -> None:
        with patch(
            "app.core.metrics.video_metrics._probe_video_dimensions",
            return_value=None,
        ):
            frames = extract_frames(b"fake-mp4")
            assert frames == []

    def test_extract_ffmpeg_failure_returns_empty(self) -> None:
        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(4, 4),
            ),
            patch("app.core.metrics.video_metrics.run_ffmpeg", side_effect=Exception("Error")),
        ):
            frames = extract_frames(b"fake-mp4")
            assert frames == []

    def test_extract_partial_frames(self) -> None:
        width, height = 4, 4
        frame_bytes = width * height * 3
        fake_raw = b"\x80" * frame_bytes * 2  # only 2 complete frames

        def mock_run_ffmpeg(args, timeout=None):
            out_path = args[-1]
            with open(out_path, "wb") as f:
                f.write(fake_raw)
            return ""

        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(width, height),
            ),
            patch("app.core.metrics.video_metrics.run_ffmpeg", side_effect=mock_run_ffmpeg),
        ):
            frames = extract_frames(b"fake-mp4", max_frames=10)
            assert len(frames) == 2

    def test_extract_timeout_returns_empty(self) -> None:
        from app.utils.exceptions import FFmpegTimeoutError
        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(4, 4),
            ),
            patch(
                "app.core.metrics.video_metrics.run_ffmpeg",
                side_effect=FFmpegTimeoutError("Timeout"),
            ),
        ):
            frames = extract_frames(b"fake-mp4")
            assert frames == []


class TestAverageMetric:
    def test_identical_frames(self) -> None:
        a = np.full((8, 8, 3), 128, dtype=np.uint8)
        b = a.copy()
        assert psnr([a], [b]) == pytest.approx(float("inf"))
        assert ssim([a], [b]) == pytest.approx(1.0, abs=1e-6)
        assert mse([a], [b]) == pytest.approx(0.0)

    def test_different_frames(self) -> None:
        a = np.zeros((8, 8, 3), dtype=np.uint8)
        b = np.full((8, 8, 3), 255, dtype=np.uint8)
        p = psnr([a], [b])
        assert p >= 0.0
        s = ssim([a], [b])
        assert -1 <= s <= 1
        m = mse([a], [b])
        assert m > 0

    def test_empty_frames_returns_zero(self) -> None:
        assert psnr([], []) == 0.0
        assert ssim([], []) == 0.0
        assert mse([], []) == 0.0

    def test_different_lengths(self) -> None:
        a = np.full((2, 2, 3), 100, dtype=np.uint8)
        b = np.full((2, 2, 3), 200, dtype=np.uint8)
        val = psnr([a, a, a], [b, b])
        assert val > 0

    def test_non_finite_values_skipped(self) -> None:
        a = np.full((2, 2, 3), 100, dtype=np.uint8)

        def _return_nan(_x: np.ndarray, _y: np.ndarray) -> float:
            return float("nan")

        result = _average_metric([a], [a], _return_nan)
        assert result == 0.0

    def test_single_channel_frames(self) -> None:
        a = np.zeros((2, 2), dtype=np.uint8)
        b = np.full((2, 2), 128, dtype=np.uint8)
        p = psnr([a], [b])
        assert p > 0
        s = ssim([a], [b])
        assert -1 <= s <= 1
        m = mse([a], [b])
        assert m > 0

    def test_mismatched_frame_shapes_raises_value_error(self) -> None:
        a = np.zeros((8, 8, 3), dtype=np.uint8)
        b = np.zeros((4, 4, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            psnr([a], [b])

