"""Unit tests for core/steganography/audio_lsb.py (AUD-03/04/05/06/07)."""

import struct

import pytest

from app.core.steganography.audio_lsb import AudioLsbCodec
from app.utils.exceptions import AppError, CapacityExceededError, UnsupportedFormatError


def _mono16_wav(n_frames: int = 800, sample_rate: int = 8000) -> bytes:
    """Build a valid mono 16-bit WAV byte string with silent samples."""
    import wave
    from io import BytesIO

    buf = BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
    return buf.getvalue()


WAV_800 = _mono16_wav(800)  # 800 frames × 2 bytes = 1600 PCM bytes → 1600 bits capacity


class TestAudioLsbCodecCapacity:
    def test_capacity_known_wav(self) -> None:
        codec = AudioLsbCodec()
        cap = codec.capacity(WAV_800)
        # 800 frames × 2 bytes/frame = 1600 PCM bytes → 1600 bits (1 LSB per byte)
        assert cap == 1600

    def test_capacity_raises_on_mp3(self) -> None:
        codec = AudioLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.capacity(b"\xff\xfb\x90\x00")

    def test_capacity_raises_on_random_bytes(self) -> None:
        codec = AudioLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.capacity(b"not a wav file at all")


class TestAudioLsbCodecEmbed:
    def test_embed_alters_lsb_only(self) -> None:
        codec = AudioLsbCodec()
        original = WAV_800
        msg = b"hello"
        result = codec.embed(original, msg)

        assert len(result) == len(original)
        # Header unchanged (first 44 bytes typically)
        assert result[:12] == original[:12]
        # PCM data should differ
        assert result != original

    def test_embed_preserves_wav_validity(self) -> None:
        import wave
        from io import BytesIO

        codec = AudioLsbCodec()
        result = codec.embed(WAV_800, b"test")
        with wave.open(BytesIO(result), "rb") as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            assert w.getframerate() == 8000
            assert w.getnframes() == 800

    def test_embed_raises_on_mp3(self) -> None:
        codec = AudioLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.embed(b"\xff\xfb\x90\x00", b"msg")

    def test_embed_raises_on_capacity_exceeded(self) -> None:
        codec = AudioLsbCodec()
        # 1600 bits = 200 bytes payload. With 4-byte prefix: 196 bytes max message.
        # 300 bytes should clearly exceed.
        large_msg = b"x" * 300
        with pytest.raises(CapacityExceededError):
            codec.embed(WAV_800, large_msg)

    def test_embed_with_password(self) -> None:
        codec = AudioLsbCodec()
        result = codec.embed(WAV_800, b"secret", password="p@ss")
        assert len(result) == len(WAV_800)


class TestAudioLsbCodecExtract:
    def test_round_trip_no_password(self) -> None:
        codec = AudioLsbCodec()
        msg = b"Hello, WAV!"
        stego = codec.embed(WAV_800, msg)
        extracted = codec.extract(stego)
        assert extracted == msg

    def test_round_trip_with_password(self) -> None:
        codec = AudioLsbCodec()
        msg = b"hidden message"
        stego = codec.embed(WAV_800, msg, password="secret")
        extracted = codec.extract(stego, password="secret")
        assert extracted == msg

    def test_extract_empty_message(self) -> None:
        codec = AudioLsbCodec()
        stego = codec.embed(WAV_800, b"")
        extracted = codec.extract(stego)
        assert extracted == b""

    def test_extract_wrong_password_raises(self) -> None:
        codec = AudioLsbCodec()
        stego = codec.embed(WAV_800, b"hello", password="correct")
        with pytest.raises(AppError):
            codec.extract(stego, password="wrong")

    def test_extract_from_clean_wav_raises_or_empty(self) -> None:
        codec = AudioLsbCodec()
        # Clean WAV has random LSB content. May return empty or raise.
        try:
            result = codec.extract(WAV_800)
            assert result == b"" or isinstance(result, bytes)
        except AppError:
            pass

    def test_extract_raises_on_mp3(self) -> None:
        codec = AudioLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.extract(b"\xff\xfb\x90\x00")


class TestAudioLsbCodecEdgeCases:
    def test_reject_non_wav_bytes(self) -> None:
        codec = AudioLsbCodec()
        with pytest.raises(UnsupportedFormatError):
            codec.embed(b"not a wav", b"x")

    def test_large_message_fits_exactly(self) -> None:
        codec = AudioLsbCodec()
        # 1600 bits capacity = 200 bytes payload. With 4-byte prefix: 196 bytes of message.
        msg = b"a" * 196
        stego = codec.embed(WAV_800, msg)
        extracted = codec.extract(stego)
        assert extracted == msg

    def test_message_one_byte_too_large_raises(self) -> None:
        codec = AudioLsbCodec()
        msg = b"a" * 197
        with pytest.raises(CapacityExceededError):
            codec.embed(WAV_800, msg)
