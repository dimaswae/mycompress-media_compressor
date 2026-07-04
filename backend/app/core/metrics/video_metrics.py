"""Video-specific quality metrics: PSNR, SSIM, MSE via frame extraction.

Extracts frames from MP4 videos via FFmpeg rawvideo pipe and compares
them frame-by-frame using scikit-image metric functions.
"""

import os
import tempfile
from collections.abc import Callable, Sequence

import numpy as np

from app.config import settings
from app.infra.ffmpeg_runner import run_ffmpeg

_FFMPEG_TIMEOUT = settings.ffmpeg_timeout_seconds
_MAX_FRAMES = 30


def _probe_video_dimensions(video_path: str) -> tuple[int, int] | None:
    """Get video width and height via ffprobe.

    Returns ``(width, height)`` or ``None`` if probing fails.
    """
    try:
        stdout = run_ffmpeg(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                video_path,
            ],
            timeout=30,
        )
        parts = stdout.strip().split(",")
        if len(parts) < 2:
            return None
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def extract_frames(
    video_bytes: bytes,
    max_frames: int = _MAX_FRAMES,
) -> list[np.ndarray]:
    """Decode up to *max_frames* from MP4 bytes as RGB ``numpy.ndarray``.

    Each frame is returned as a ``(H, W, 3)`` uint8 array in RGB order.

    Args:
        video_bytes: Raw MP4 file bytes.
        max_frames: Maximum number of frames to extract (default 30).

    Returns:
        List of RGB frame arrays. May be empty if decoding fails.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input.mp4")
        raw_bin_path = os.path.join(tmpdir, "output.bin")

        with open(video_path, "wb") as f:
            f.write(video_bytes)

        try:
            dims = _probe_video_dimensions(video_path)
            if dims is None:
                return []
            width, height = dims

            run_ffmpeg(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    video_path,
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "rgb24",
                    "-vframes",
                    str(max_frames),
                    "-s",
                    f"{width}x{height}",
                    raw_bin_path,
                ],
                timeout=_FFMPEG_TIMEOUT,
            )

            if not os.path.exists(raw_bin_path):
                return []

            with open(raw_bin_path, "rb") as f:
                raw_data = f.read()

            frame_bytes = width * height * 3
            frames: list[np.ndarray] = []
            for i in range(max_frames):
                offset = i * frame_bytes
                if offset + frame_bytes > len(raw_data):
                    break
                frame = np.frombuffer(
                    raw_data[offset : offset + frame_bytes], dtype=np.uint8
                )
                frame = frame.reshape((height, width, 3))
                frames.append(frame)

            return frames

        except Exception:
            return []


def _average_metric(
    original_frames: Sequence[np.ndarray],
    processed_frames: Sequence[np.ndarray],
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
) -> float:
    """Compute the average of *metric_fn* across corresponding frame pairs.

    Handles different-length frame lists by comparing only up to
    ``min(len(original_frames), len(processed_frames))`` frames.
    Returns ``inf`` if all computed values are infinite.
    """
    n = min(len(original_frames), len(processed_frames))
    if n == 0:
        return 0.0
    for i in range(n):
        if original_frames[i].shape != processed_frames[i].shape:
            raise ValueError("Original and processed frames must have the same shape")
    values: list[float] = []
    for i in range(n):
        try:
            val = metric_fn(original_frames[i], processed_frames[i])
            values.append(float(val))
        except Exception:
            continue
    if not values:
        return 0.0
    inf_values = [v for v in values if np.isinf(v)]
    if len(inf_values) == len(values) and inf_values and inf_values[0] > 0:
        return float("inf")
    finite_values = [v for v in values if np.isfinite(v)]
    return float(np.mean(finite_values)) if finite_values else 0.0


def psnr(
    original_frames: Sequence[np.ndarray],
    processed_frames: Sequence[np.ndarray],
) -> float:
    """Average Peak Signal-to-Noise Ratio across corresponding video frames."""
    from skimage.metrics import peak_signal_noise_ratio

    return _average_metric(original_frames, processed_frames, peak_signal_noise_ratio)


def ssim(
    original_frames: Sequence[np.ndarray],
    processed_frames: Sequence[np.ndarray],
) -> float:
    """Average Structural Similarity Index across corresponding video frames."""
    from skimage.metrics import structural_similarity

    def _ssim_pair(a: np.ndarray, b: np.ndarray) -> float:
        min_side = min(a.shape[0], a.shape[1])
        win_size = min(7, min_side if min_side % 2 == 1 else min_side - 1)
        if a.ndim == 3 and a.shape[2] == 3:
            return float(
                structural_similarity(
                    a, b, channel_axis=-1, data_range=255, win_size=win_size
                )
            )
        return float(structural_similarity(a, b, data_range=255, win_size=win_size))

    return _average_metric(original_frames, processed_frames, _ssim_pair)


def mse(
    original_frames: Sequence[np.ndarray],
    processed_frames: Sequence[np.ndarray],
) -> float:
    """Average Mean Squared Error across corresponding video frames."""
    from skimage.metrics import mean_squared_error

    return _average_metric(original_frames, processed_frames, mean_squared_error)
