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
        mock_proc = MagicMock(spec=subprocess.CompletedProcess)
        mock_proc.returncode = 0
        mock_proc.stdout = "640,480\n"

        with patch(
            "app.core.metrics.video_metrics.subprocess.run", return_value=mock_proc
        ):
            result = _probe_video_dimensions("/fake/path.mp4")
            assert result == (640, 480)

    def test_probe_failure_returncode(self) -> None:
        mock_proc = MagicMock(spec=subprocess.CompletedProcess)
        mock_proc.returncode = 1

        with patch(
            "app.core.metrics.video_metrics.subprocess.run", return_value=mock_proc
        ):
            assert _probe_video_dimensions("/fake/path.mp4") is None

    def test_probe_timeout_returns_none(self) -> None:
        with patch(
            "app.core.metrics.video_metrics.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="ffprobe", timeout=30),
        ):
            assert _probe_video_dimensions("/fake/path.mp4") is None


class TestExtractFrames:
    def test_extract_success(self) -> None:
        width, height = 4, 4
        frame_bytes = width * height * 3
        num_frames = 3
        fake_raw = b"\x80" * frame_bytes * num_frames

        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(width, height),
            ),
            patch("app.core.metrics.video_metrics.subprocess.run") as mock_run,
            patch("app.core.metrics.video_metrics.os.unlink"),
        ):
            mock_proc = MagicMock(spec=subprocess.CompletedProcess)
            mock_proc.returncode = 0
            mock_proc.stdout = fake_raw
            mock_run.return_value = mock_proc

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
            patch("app.core.metrics.video_metrics.subprocess.run") as mock_run,
            patch("app.core.metrics.video_metrics.os.unlink"),
        ):
            mock_proc = MagicMock(spec=subprocess.CompletedProcess)
            mock_proc.returncode = 1
            mock_run.return_value = mock_proc

            frames = extract_frames(b"fake-mp4")
            assert frames == []

    def test_extract_partial_frames(self) -> None:
        width, height = 4, 4
        frame_bytes = width * height * 3
        fake_raw = b"\x80" * frame_bytes * 2  # only 2 complete frames

        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(width, height),
            ),
            patch("app.core.metrics.video_metrics.subprocess.run") as mock_run,
            patch("app.core.metrics.video_metrics.os.unlink"),
        ):
            mock_proc = MagicMock(spec=subprocess.CompletedProcess)
            mock_proc.returncode = 0
            mock_proc.stdout = fake_raw
            mock_run.return_value = mock_proc

            frames = extract_frames(b"fake-mp4", max_frames=10)
            assert len(frames) == 2

    def test_extract_timeout_returns_empty(self) -> None:
        with (
            patch(
                "app.core.metrics.video_metrics._probe_video_dimensions",
                return_value=(4, 4),
            ),
            patch(
                "app.core.metrics.video_metrics.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=120),
            ),
            patch("app.core.metrics.video_metrics.os.unlink"),
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
