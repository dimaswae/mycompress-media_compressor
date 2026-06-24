"""Codec registry — maps string identifiers to ``CompressionCodec`` instances.

Usage::

    codec = get_codec("rle")       # → RleCodec()
    codec = get_codec("huffman")   # → HuffmanCodec()
    codec = get_codec("unknown")   # → raises UnsupportedFormatError
"""

from app.core.compression.base import CompressionCodec
from app.core.compression.image_huffman import HuffmanCodec
from app.core.compression.image_rle import RleCodec
from app.utils.exceptions import UnsupportedFormatError

_REGISTRY: dict[str, CompressionCodec] = {
    "rle": RleCodec(),
    "huffman": HuffmanCodec(),
}


def get_codec(algorithm: str) -> CompressionCodec:
    """Return a ``CompressionCodec`` instance for *algorithm*.

    Args:
        algorithm: One of ``"rle"`` or ``"huffman"`` (case-sensitive).

    Returns:
        A singleton codec instance.

    Raises:
        UnsupportedFormatError: If *algorithm* is not recognised.
    """
    codec = _REGISTRY.get(algorithm)
    if codec is None:
        raise UnsupportedFormatError(
            f"Unsupported compression algorithm '{algorithm}'. "
            f"Available: {', '.join(sorted(_REGISTRY))}"
        )
    return codec
