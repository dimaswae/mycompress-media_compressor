"""Unit tests for ``core/compression/image_rle.py`` (IMG-02, IMG-03, IMG-04)."""

import pytest

from app.core.compression.image_rle import RleCodec, _RleDecodeError


class TestRleCompress:
    def test_flat_color_compresses_smaller(self) -> None:
        """Compressing a flat-colour image (all same pixel) produces smaller output."""
        codec = RleCodec()
        # Simulate a flat-colour image: all bytes are 0x80
        flat = b"\x80" * 1024
        compressed = codec.compress(flat)
        assert len(compressed) < len(flat)

    def test_empty_input(self) -> None:
        codec = RleCodec()
        assert codec.compress(b"") == b""

    def test_no_duplicate_bytes(self) -> None:
        """All bytes in input are unique -> compressed may be larger (no runs)."""
        codec = RleCodec()
        data = bytes(range(256))
        compressed = codec.compress(data)
        # Each byte becomes a pair: (byte, 1) → 2 bytes each → 512 bytes
        assert len(compressed) == 512


class TestRleDecompress:
    def test_round_trip_on_sample_fixture(self) -> None:
        codec = RleCodec()
        original = b"\x00" * 500 + b"\xff" * 500
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original

    def test_round_trip_empty(self) -> None:
        codec = RleCodec()
        assert codec.decompress(b"") == b""

    def test_round_trip_no_runs(self) -> None:
        codec = RleCodec()
        original = bytes(range(10))
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original


class TestRleErrorHandling:
    def test_odd_length_data_raises(self) -> None:
        codec = RleCodec()
        with pytest.raises(_RleDecodeError, match="even"):
            codec.decompress(b"\x01")

    def test_zero_run_length_raises(self) -> None:
        codec = RleCodec()
        with pytest.raises(_RleDecodeError, match="zero"):
            codec.decompress(b"\x42\x00")

    def test_exception_is_app_error_subclass(self) -> None:
        from app.utils.exceptions import AppError

        codec = RleCodec()
        with pytest.raises(AppError):
            codec.decompress(b"\x01")

    def test_garbage_bytes_raises(self) -> None:
        codec = RleCodec()
        with pytest.raises(_RleDecodeError):
            codec.decompress(b"\xff\xfe\xfd")
