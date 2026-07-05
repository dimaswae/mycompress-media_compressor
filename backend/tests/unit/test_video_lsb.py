"""Unit tests for core/steganography/video_lsb.py (VID-03/04)."""

import struct

import pytest

from app.core.steganography.video_lsb import VideoLsbCodec
from app.utils.exceptions import CapacityExceededError, UnsupportedFormatError


def _make_mp4(mdat_payload_size: int = 200) -> bytes:
    """Generate a minimal MP4 byte string with ftyp + mdat boxes."""
    ftyp_content = b"mp42\x00\x00\x00\x00mp42mp41"
    ftyp_size = 8 + len(ftyp_content)
    ftyp = struct.pack(">I", ftyp_size) + b"ftyp" + ftyp_content

    mdat_payload = b"\x00" * mdat_payload_size
    mdat_size = 8 + len(mdat_payload)
    mdat = struct.pack(">I", mdat_size) + b"mdat" + mdat_payload

    return ftyp + mdat


MP4_200 = _make_mp4(200)


class TestVideoLsbCodecCapacity:
    def test_capacity_known_mp4(self) -> None:
        codec = VideoLsbCodec()
        cap = codec.capacity(MP4_200)
        assert cap == 200

    def test_capacity_raises_on_random_bytes(self) -> None:
        codec = VideoLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.capacity(b"not an mp4 file")


class TestVideoLsbCodecEmbed:
    def test_embed_alters_mdat_only(self) -> None:
        codec = VideoLsbCodec()
        original = MP4_200
        msg = b"hello"
        result = codec.embed(original, msg)

        assert len(result) == len(original)
        # ftyp box header unchanged
        assert result[:8] == original[:8]
        assert result != original

    def test_embed_raises_on_random_bytes(self) -> None:
        codec = VideoLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.embed(b"not an mp4", b"msg")

    def test_embed_raises_on_capacity_exceeded(self) -> None:
        codec = VideoLsbCodec()
        # 200 bits = 25 bytes payload - 4 byte prefix = 21 bytes max message
        large_msg = b"x" * 100
        with pytest.raises(CapacityExceededError):
            codec.embed(MP4_200, large_msg)


class TestVideoLsbCodecExtract:
    def test_round_trip_no_password(self) -> None:
        codec = VideoLsbCodec()
        msg = b"Hello, MP4!"
        stego = codec.embed(MP4_200, msg)
        extracted = codec.extract(stego)
        assert extracted == msg

    def test_extract_empty_message(self) -> None:
        codec = VideoLsbCodec()
        stego = codec.embed(MP4_200, b"")
        extracted = codec.extract(stego)
        assert extracted == b""

    def test_extract_raises_on_random_bytes(self) -> None:
        codec = VideoLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.extract(b"not an mp4")


class TestVideoLsbCodecEdgeCases:
    def test_large_message_fits_exactly(self) -> None:
        codec = VideoLsbCodec()
        # 200 bits = 25 bytes payload. With 4-byte prefix: 21 bytes of message.
        msg = b"a" * 21
        stego = codec.embed(MP4_200, msg)
        extracted = codec.extract(stego)
        assert extracted == msg

    def test_message_one_byte_too_large_raises(self) -> None:
        codec = VideoLsbCodec()
        msg = b"a" * 22
        with pytest.raises(CapacityExceededError):
            codec.embed(MP4_200, msg)


class TestVideoLsbCodecRealVideo:
    def test_real_video_roundtrip_and_decodability(
        self, sample_video_fixture_bytes: bytes
    ) -> None:
        import os
        import tempfile
        import subprocess
        import cv2
        import numpy as np

        codec = VideoLsbCodec()
        
        # Calculate dynamic capacity
        cap = codec.capacity(sample_video_fixture_bytes)
        
        # Check if it is the real video (capacity should be large)
        is_real = len(sample_video_fixture_bytes) > 20000
        
        msg = b"Real video stego test!"
        stego = codec.embed(sample_video_fixture_bytes, msg)
        extracted = codec.extract(stego)
        assert extracted == msg
        
        if is_real:
            # Check if stego video can be decoded by FFmpeg without error
            with tempfile.TemporaryDirectory() as tmpdir:
                path = os.path.join(tmpdir, "stego.mp4")
                with open(path, "wb") as f:
                    f.write(stego)
                
                cmd = ["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"]
                res = subprocess.run(cmd, capture_output=True, text=True)
                assert res.returncode == 0, f"FFmpeg decoding failed: {res.stderr}"
                
                # Check PSNR of I-frames
                orig_path = os.path.join(tmpdir, "orig.mp4")
                with open(orig_path, "wb") as f:
                    f.write(sample_video_fixture_bytes)
                    
                from app.core.steganography.video_lsb import _get_iframe_indices, _extract_raw_frames
                iframe_indices = _get_iframe_indices(orig_path)
                
                orig_frames, _, _, _ = _extract_raw_frames(orig_path)
                stego_frames, _, _, _ = _extract_raw_frames(path)
                
                psnrs = []
                for idx in iframe_indices:
                    orig_f = orig_frames[idx].astype(np.float64)
                    stego_f = stego_frames[idx].astype(np.float64)
                    mse = np.mean((orig_f - stego_f) ** 2)
                    if mse == 0:
                        psnr = float("inf")
                    else:
                        psnr = 20 * np.log10(255.0 / np.sqrt(mse))
                    psnrs.append(psnr)
                
                print(f"\n[TEST PSNR REPORT] Baseline PSNR for I-frames: {psnrs}")
                for psnr in psnrs:
                    assert psnr > 50.0 or psnr == float("inf")


class TestVideoLsbCodecFailure:
    def test_embed_corrupt_mp4_raises_video_processing_error(self) -> None:
        codec = VideoLsbCodec()
        # Passes _is_mp4 but fails ffprobe/cv2, triggering fallback-turned-error
        corrupt_mp4 = b"\x00\x00\x00\x18ftyp" + b"x" * 1000
        from app.utils.exceptions import VideoProcessingError
        with pytest.raises(VideoProcessingError) as exc_info:
            codec.embed(corrupt_mp4, b"test")
        assert "Failed to embed" in str(exc_info.value.message)

    def test_extract_corrupt_mp4_raises_video_processing_error(self) -> None:
        codec = VideoLsbCodec()
        corrupt_mp4 = b"\x00\x00\x00\x18ftyp" + b"x" * 1000
        from app.utils.exceptions import VideoProcessingError
        with pytest.raises(VideoProcessingError) as exc_info:
            codec.extract(corrupt_mp4)
        assert "Failed to extract" in str(exc_info.value.message)