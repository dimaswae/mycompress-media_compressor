"""FFmpeg-based audio bitrate compression codec.

Compresses WAV to MP3 at a target bitrate; decompresses back to WAV.
"""

import tempfile
from pathlib import Path

from app.core.compression.base import CompressionCodec
from app.infra.ffmpeg_runner import run_ffmpeg
from app.utils.exceptions import AppError


class AudioBitrateCodec(CompressionCodec):
    """Compress/decompress audio via FFmpeg bitrate reduction.

    Args:
        bitrate: Target bitrate string (e.g. ``"128k"``, ``"64k"``).
    """

    def __init__(self, bitrate: str = "128k") -> None:
        self.bitrate = bitrate

    def compress(self, data: bytes) -> bytes:
        """Re-encode WAV bytes to MP3 at the configured bitrate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = Path(tmpdir) / "input.wav"
            out_path = Path(tmpdir) / "output.mp3"
            in_path.write_bytes(data)
            try:
                run_ffmpeg(
                    ["ffmpeg", "-y", "-i", str(in_path), "-b:a", self.bitrate, str(out_path)]
                )
            except Exception as exc:
                raise AppError(
                    code="AUDIO_COMPRESS_ERROR",
                    message=f"FFmpeg compression failed: {exc}",
                ) from exc
            if not out_path.exists():
                raise AppError(
                    code="AUDIO_COMPRESS_ERROR",
                    message="FFmpeg did not produce an output file",
                )
            return out_path.read_bytes()

    def decompress(self, data: bytes) -> bytes:
        """Decode MP3 bytes back to WAV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = Path(tmpdir) / "input.mp3"
            out_path = Path(tmpdir) / "output.wav"
            in_path.write_bytes(data)
            try:
                run_ffmpeg(
                    ["ffmpeg", "-y", "-i", str(in_path), str(out_path)]
                )
            except Exception as exc:
                raise AppError(
                    code="AUDIO_DECOMPRESS_ERROR",
                    message=f"FFmpeg decompression failed: {exc}",
                ) from exc
            if not out_path.exists():
                raise AppError(
                    code="AUDIO_DECOMPRESS_ERROR",
                    message="FFmpeg did not produce an output file",
                )
            return out_path.read_bytes()
