"""Unit tests for ``core/compression/registry.py`` (IMG-08)."""

import pytest

from app.core.compression.image_huffman import HuffmanCodec
from app.core.compression.image_rle import RleCodec
from app.core.compression.registry import get_codec
from app.utils.exceptions import UnsupportedFormatError


class TestRegistry:
    def test_get_codec_rle(self) -> None:
        codec = get_codec("rle")
        assert isinstance(codec, RleCodec)

    def test_get_codec_huffman(self) -> None:
        codec = get_codec("huffman")
        assert isinstance(codec, HuffmanCodec)

    def test_get_codec_unknown_key_raises(self) -> None:
        with pytest.raises(UnsupportedFormatError, match="unknown"):
            get_codec("unknown")

    def test_get_codec_returns_same_instance(self) -> None:
        assert get_codec("rle") is get_codec("rle")
        assert get_codec("huffman") is get_codec("huffman")
