"""Unit tests for ``core/compression/image_huffman.py`` (IMG-05, IMG-06, IMG-07)."""

import pytest

from app.core.compression.image_huffman import (
    HuffmanCodec,
    _HuffmanDecodeError,
    _build_frequencies,
    _build_tree,
    _canonical_codes,
    _code_lengths_from_tree,
)


class TestHuffmanInternalHelpers:
    def test_build_frequencies(self) -> None:
        freqs = _build_frequencies(b"aabbbc")
        assert freqs[97] == 2  # ord('a')
        assert freqs[98] == 3  # ord('b')
        assert freqs[99] == 1  # ord('c')

    def test_tree_and_code_lengths(self) -> None:
        freqs = _build_frequencies(b"aabbbc")
        tree = _build_tree(freqs)
        code_lengths = _code_lengths_from_tree(tree)

        assert len(code_lengths) == 3
        for sym, length in code_lengths.items():
            assert 1 <= length <= 3  # reasonable for 3 symbols

    def test_canonical_codes_are_prefix_free(self) -> None:
        code_lengths = {97: 1, 98: 2, 99: 3}
        codes = _canonical_codes(code_lengths)
        # Validate prefix-freeness: no code should be a prefix of another
        code_strs = [
            bin(codes[sym])[2:].zfill(code_lengths[sym]) for sym in code_lengths
        ]
        for i, c1 in enumerate(code_strs):
            for j, c2 in enumerate(code_strs):
                if i != j:
                    assert not c2.startswith(c1), f"{c2} is a prefix of {c1}"


class TestHuffmanEncodeDecode:
    def test_round_trip_on_sample(self) -> None:
        codec = HuffmanCodec()
        original = b"hello world, this is a huffman test!"
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original

    def test_round_trip_on_binary_data(self) -> None:
        codec = HuffmanCodec()
        original = bytes(range(256)) * 4  # all byte values, repeated
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original

    def test_round_trip_large_repeating(self) -> None:
        codec = HuffmanCodec()
        original = b"\x00" * 1024 + b"\xff" * 1024
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original

    def test_produces_header_and_body(self) -> None:
        codec = HuffmanCodec()
        data = b"hello"
        compressed = codec.compress(data)
        # Header is at least 2 bytes (num_symbols)
        assert len(compressed) > 2
        # Compressed output should contain symbol table and bitstream


class TestHuffmanEdgeCases:
    def test_empty_input(self) -> None:
        codec = HuffmanCodec()
        assert codec.compress(b"") == b""
        assert codec.decompress(b"") == b""

    def test_single_unique_byte_value(self) -> None:
        codec = HuffmanCodec()
        original = b"\xab" * 100
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original
        # For a single symbol, each byte becomes 1 bit
        # Expected size = 4 (orig_size) + 2 (num_syms) + 2 (sym + len) + ceil(100/8)
        expected_header = 8
        expected_body = 13  # ceil(100/8)
        assert len(compressed) == expected_header + expected_body

    def test_two_unique_bytes(self) -> None:
        codec = HuffmanCodec()
        original = b"\x00\x01" * 50  # 100 bytes, 2 values
        compressed = codec.compress(original)
        decompressed = codec.decompress(compressed)
        assert decompressed == original


class TestHuffmanErrorHandling:
    def test_truncated_header_raises(self) -> None:
        codec = HuffmanCodec()
        with pytest.raises(_HuffmanDecodeError):
            codec.decompress(b"\x00\x01\xff")  # says 1 symbol but only 1 byte of data

    def test_corrupt_bitstream_does_not_crash(self) -> None:
        """Decoding random garbage should not raise unexpected exceptions."""
        codec = HuffmanCodec()
        result = codec.decompress(b"\x00\x00\x00\x04\x00\x01\x00\x01\xff")
        # May return empty or wrong data, but should not crash
        assert isinstance(result, bytes)

    def test_exception_is_app_error_subclass(self) -> None:
        from app.utils.exceptions import AppError

        codec = HuffmanCodec()
        with pytest.raises(AppError):
            codec.decompress(b"\x00\x01\xff")
