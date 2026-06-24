"""FFmpeg-based video compression codec.

Compresses MP4 to MP4 at a target CRF value; decompresses back to a higher-quality MP4.
"""

import tempfile
from pathlib import Path

from app.core.compression.base import CompressionCodec
from app.infra.ffmpeg_runner import run_ffmpeg
from app.utils.exceptions import AppError


class VideoCodec(CompressionCodec):
    """Compress/decompress video via FFmpeg CRF-based re-encoding.

    Args:
        crf: Constant Rate Factor (0–51). Lower = better quality, larger file.
            Default 23 is the x264 default. 28 is a good compression value.
    """

    def __init__(self, crf: int = 28) -> None:
        self.crf = crf

    def compress(self, data: bytes) -> bytes:
        """Re-encode MP4 bytes at the configured CRF (lower quality, smaller size)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = Path(tmpdir) / "input.mp4"
            out_path = Path(tmpdir) / "output.mp4"
            in_path.write_bytes(data)
            try:
                run_ffmpeg(
                    [
                        "ffmpeg", "-y",
                        "-i", str(in_path),
                        "-c:v", "libx264",
                        "-crf", str(self.crf),
                        "-preset", "fast",
                        "-c:a", "aac",
                        str(out_path),
                    ]
                )
            except Exception as exc:
                raise AppError(
                    code="VIDEO_COMPRESS_ERROR",
                    message=f"FFmpeg compression failed: {exc}",
                ) from exc
            if not out_path.exists():
                raise AppError(
                    code="VIDEO_COMPRESS_ERROR",
                    message="FFmpeg did not produce an output file",
                )
            return out_path.read_bytes()

    def decompress(self, data: bytes) -> bytes:
        """Re-encode MP4 bytes at a higher quality (CRF 18)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = Path(tmpdir) / "input.mp4"
            out_path = Path(tmpdir) / "output.mp4"
            in_path.write_bytes(data)
            try:
                run_ffmpeg(
                    [
                        "ffmpeg", "-y",
                        "-i", str(in_path),
                        "-c:v", "libx264",
                        "-crf", "18",
                        "-preset", "fast",
                        "-c:a", "aac",
                        str(out_path),
                    ]
                )
            except Exception as exc:
                raise AppError(
                    code="VIDEO_DECOMPRESS_ERROR",
                    message=f"FFmpeg decompression failed: {exc}",
                ) from exc
            if not out_path.exists():
                raise AppError(
                    code="VIDEO_DECOMPRESS_ERROR",
                    message="FFmpeg did not produce an output file",
                )
            return out_path.read_bytes()
