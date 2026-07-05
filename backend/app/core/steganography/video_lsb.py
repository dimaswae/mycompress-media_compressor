import os
import subprocess
import tempfile
import cv2
import numpy as np

import logging
from app.utils.exceptions import AppError, CapacityExceededError, UnsupportedFormatError, VideoProcessingError


class _VideoLsbExtractError(AppError):
    """Raised when LSB extraction encounters corrupt or truncated data."""

    def __init__(self, message: str = "Failed to extract message from video") -> None:
        super().__init__(code="VIDEO_LSB_EXTRACT_ERROR", message=message)


def _is_mp4(data: bytes) -> bool:
    """Return True if *data* starts with a valid MP4 signature."""
    if len(data) < 8:
        return False
    if data[:4] == b"\x00\x00\x00\x18" and data[4:8] == b"ftyp":
        return True
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return True
    return False




def _get_iframe_indices(video_path: str) -> list[int]:
    """Use ffprobe to identify the indices of all I-frames in the video."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "frame=pict_type",
        "-of", "csv=p=0",
        video_path
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    frame_types = proc.stdout.strip().splitlines()
    return [i for i, t in enumerate(frame_types) if t.strip() == "I"]


def _extract_raw_frames(video_path: str) -> tuple[list[np.ndarray], float, int, int]:
    """Extract all frames of a video and return (frames, fps, width, height)."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise AppError(code="DECODE_ERROR", message="Failed to decode video frames")
    return frames, fps, w, h


def _embed_bits(
    frames: list[np.ndarray],
    iframe_indices: list[int],
    payload: bytes
) -> list[np.ndarray]:
    """Embed the raw payload bytes into the LSBs of the I-frames."""
    payload_bits = []
    for byte in payload:
        for bit_idx in range(8):
            payload_bits.append((byte >> (7 - bit_idx)) & 1)
            
    bit_idx = 0
    total_bits = len(payload_bits)
    modified = [f.copy() for f in frames]
    
    for iframe_idx in iframe_indices:
        if bit_idx >= total_bits:
            break
        
        # Convert to RGB for embedding consistency
        frame_rgb = cv2.cvtColor(modified[iframe_idx], cv2.COLOR_BGR2RGB)
        flat = frame_rgb.flatten()
        
        n_bits = min(total_bits - bit_idx, len(flat))
        for i in range(n_bits):
            flat[i] = (flat[i] & 0xFE) | payload_bits[bit_idx]
            bit_idx += 1
            
        modified[iframe_idx] = cv2.cvtColor(flat.reshape(frame_rgb.shape), cv2.COLOR_RGB2BGR)
        
    return modified


def _extract_bits(frames: list[np.ndarray], iframe_indices: list[int]) -> bytes:
    """Extract payload bits from the LSBs of the I-frames and convert to bytes."""
    all_bits = []
    for iframe_idx in iframe_indices:
        if iframe_idx >= len(frames):
            break
        frame_rgb = cv2.cvtColor(frames[iframe_idx], cv2.COLOR_BGR2RGB)
        flat = frame_rgb.flatten()
        all_bits.extend([int(p & 1) for p in flat])
        
    min_bits = 8 * 4
    if len(all_bits) < min_bits:
        raise _VideoLsbExtractError("Video does not contain enough bits for length prefix")
        
    raw_bytes_list = []
    for i in range(0, (len(all_bits) // 8) * 8, 8):
        chunk = all_bits[i : i + 8]
        byte_val = 0
        for b in chunk:
            byte_val = (byte_val << 1) | b
        raw_bytes_list.append(byte_val)
    raw_bytes = bytes(raw_bytes_list)
    
    if len(raw_bytes) < 4:
        raise _VideoLsbExtractError("Truncated payload: missing length prefix")
        
    msg_len = int.from_bytes(raw_bytes[:4], "big")
    if msg_len == 0:
        return b""
    if msg_len > len(raw_bytes) - 4:
        raise _VideoLsbExtractError(
            f"Declared message length {msg_len} exceeds video capacity — "
            f"possibly corrupt or wrong password"
        )
        
    return raw_bytes[4 : 4 + msg_len]


def _reencode_video(
    frames: list[np.ndarray],
    in_path: str,
    fps: float,
    iframe_indices: list[int],
    out_path: str
) -> None:
    """Write frames to a temp directory as PNG and run FFmpeg to re-encode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, frame in enumerate(frames):
            frame_name = os.path.join(tmpdir, f"frame_{i:08d}.png")
            cv2.imwrite(frame_name, frame)
            
        expr = "+".join(f"eq(n,{idx})" for idx in iframe_indices)
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "image2",
            "-framerate", str(fps),
            "-i", os.path.join(tmpdir, "frame_%08d.png"),
            "-i", in_path,
            "-map", "0:v",
            "-map", "1:a?",
            "-c:v", "libx264rgb",
            "-crf", "0",
            "-preset", "ultrafast",
            "-g", "999999",
            "-keyint_min", "999999",
            "-sc_threshold", "0",
            "-force_key_frames", f"expr:{expr}",
            "-c:a", "copy",
            out_path
        ]
        from app.infra.ffmpeg_runner import run_ffmpeg
        run_ffmpeg(ffmpeg_cmd)


class VideoLsbCodec:
    """LSB steganography codec for MP4 video (I-frame pixels or fallback to mdat payload bytes).

    Message format in the bitstream::

        [message_length : 4 bytes big-endian]
        [message_bytes  : ...]
    """

    def capacity(self, video_bytes: bytes) -> int:
        """Return the maximum number of payload bits that can be embedded."""
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = os.path.join(tmpdir, "temp.mp4")
                with open(video_path, "wb") as f:
                    f.write(video_bytes)
                
                iframe_indices = _get_iframe_indices(video_path)
                if not iframe_indices:
                    raise AppError(code="NO_IFRAMES", message="No I-frames found in video")
                
                cap = cv2.VideoCapture(video_path)
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                if w <= 0 or h <= 0:
                    raise AppError(code="INVALID_VIDEO_DIMENSIONS", message="Could not read video dimensions")
                
                return len(iframe_indices) * w * h * 3
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("Failed to calculate video capacity: %s", exc, exc_info=True)
            raise VideoProcessingError(f"Failed to calculate video capacity: {exc}") from exc

    def embed(self, video_bytes: bytes, message: bytes) -> bytes:
        """Embed *message* into *video_bytes* and return a new MP4 byte string."""
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                in_path = os.path.join(tmpdir, "input.mp4")
                out_path = os.path.join(tmpdir, "output.mp4")
                with open(in_path, "wb") as f:
                    f.write(video_bytes)
                
                iframe_indices = _get_iframe_indices(in_path)
                if not iframe_indices:
                    raise AppError(code="NO_IFRAMES", message="No I-frames found in video")
                
                frames, fps, w, h = _extract_raw_frames(in_path)
                
                total_capacity = len(iframe_indices) * w * h * 3
                length_bytes = len(message).to_bytes(4, "big")
                payload = length_bytes + message
                
                if len(payload) * 8 > total_capacity:
                    max_msg = (total_capacity // 8) - 4
                    raise CapacityExceededError(
                        f"Message size {len(message)} bytes exceeds maximum of "
                        f"{max_msg} bytes (I-frame capacity = {total_capacity} bits)"
                    )
                
                stego_frames = _embed_bits(frames, iframe_indices, payload)
                _reencode_video(stego_frames, in_path, fps, iframe_indices, out_path)
                
                if not os.path.exists(out_path):
                    raise AppError(code="ENCODE_ERROR", message="FFmpeg re-encoding failed")
                    
                with open(out_path, "rb") as f:
                    return f.read()
        except CapacityExceededError:
            raise
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("Failed to embed message into video: %s", exc, exc_info=True)
            raise VideoProcessingError(f"Failed to embed message into video: {exc}") from exc

    def extract(self, video_bytes: bytes) -> bytes:
        """Extract a hidden message from *video_bytes*."""
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                in_path = os.path.join(tmpdir, "input.mp4")
                with open(in_path, "wb") as f:
                    f.write(video_bytes)
                
                iframe_indices = _get_iframe_indices(in_path)
                if not iframe_indices:
                    raise _VideoLsbExtractError("No I-frames found in video")
                
                frames, _, _, _ = _extract_raw_frames(in_path)
                return _extract_bits(frames, iframe_indices)
        except _VideoLsbExtractError:
            raise
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("Failed to extract message from video: %s", exc, exc_info=True)
            raise VideoProcessingError(f"Failed to extract message from video: {exc}") from exc