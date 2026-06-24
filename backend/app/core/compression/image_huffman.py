"""Canonical Huffman coding codec for image data.

Format (big-endian)::

    [original_size  : 4 bytes]
    [num_symbols    : 2 bytes]
    [sym_1          : 1 byte] [code_len_1 : 1 byte]
    [sym_2          : 1 byte] [code_len_2 : 1 byte]
    ...
    [padded bitstream ...]

The bitstream is packed MSB-first.  The decoder stops once *original_size*
bytes have been produced, discarding any trailing padding bits.
"""

import heapq
from collections import Counter
from itertools import count

from app.core.compression.base import CompressionCodec
from app.utils.exceptions import AppError


class _HuffmanDecodeError(AppError):
    """Raised when the Huffman bitstream is corrupt or malformed."""

    def __init__(self, message: str = "Corrupt Huffman compressed data") -> None:
        super().__init__(code="HUFFMAN_DECODE_ERROR", message=message)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_frequencies(data: bytes) -> Counter[int]:
    """Return a ``Counter`` mapping each byte value to its frequency."""
    return Counter(data)


def _build_tree(freqs: Counter[int]) -> tuple | int | None:
    """Build a Huffman tree using a min-heap.

    Returns the tree root node.  Leaf nodes are ``int`` symbol values.
    Internal nodes are ``(left, right)`` tuples.
    Returns ``None`` if *freqs* is empty.
    """
    if not freqs:
        return None

    heap: list[tuple[int, int, tuple | int]] = []
    tiebreaker = count()

    for sym, freq in freqs.items():
        heapq.heappush(heap, (freq, next(tiebreaker), sym))

    while len(heap) > 1:
        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)
        heapq.heappush(heap, (freq1 + freq2, next(tiebreaker), (left, right)))

    return heap[0][2]


def _code_lengths_from_tree(tree: tuple | int | None) -> dict[int, int]:
    """Walk the Huffman tree and return a ``{symbol: code_length}`` map.

    The minimum code length is 1 so that single-symbol inputs (tree is a bare
    int) are encoded as 1 bit per byte rather than 0 bits.
    """

    result: dict[int, int] = {}

    def _walk(node: tuple | int, depth: int) -> None:
        if isinstance(node, int):
            result[node] = max(depth, 1)  # minimum length = 1
        else:
            left, right = node
            _walk(left, depth + 1)
            _walk(right, depth + 1)

    if tree is None:
        return {}
    _walk(tree, 0)
    return result


def _canonical_codes(code_lengths: dict[int, int]) -> dict[int, int]:
    """Convert ``{symbol: code_length}`` to ``{symbol: canonical_code}``.

    Canonical codes are assigned by sorting symbols by (code_length, symbol)
    and then assigning sequential binary numbers at each length.
    """
    sorted_syms = sorted(code_lengths, key=lambda s: (code_lengths[s], s))
    code = 0
    prev_len = code_lengths[sorted_syms[0]]
    codes: dict[int, int] = {}
    for sym in sorted_syms:
        length = code_lengths[sym]
        if length > prev_len:
            code <<= length - prev_len
        codes[sym] = code
        code += 1
        prev_len = length
    return codes


def _build_decode_table(
    code_lengths: dict[int, int],
) -> dict[int, int]:
    """Build a ``{padded_code_with_length: symbol}`` lookup table.

    Each key is ``(code << 5) | length`` packed into a single int for fast
    bit-at-a-time decoding.
    """
    codes = _canonical_codes(code_lengths)
    table: dict[int, int] = {}
    for sym, canonical in codes.items():
        length = code_lengths[sym]
        table[(canonical << 5) | length] = sym
    return table


def _pack_bits(bits: list[int]) -> bytes:
    """Pack a list of bits (0/1) into bytes, MSB first, zero-padded."""
    result = bytearray()
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            result.append(byte)
            byte = 0
            count = 0
    if count:
        byte <<= 8 - count
        result.append(byte)
    return bytes(result)


def _unpack_bits(data: bytes, total_bits: int) -> list[int]:
    """Unpack *total_bits* bits from *data* (MSB first), discarding padding."""
    bits: list[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits[:total_bits]


def _build_header(code_lengths: dict[int, int], original_size: int) -> bytes:
    """Build the header byte string from a ``{symbol: code_length}`` map."""
    num_syms = len(code_lengths)
    parts = [original_size.to_bytes(4, "big"), num_syms.to_bytes(2, "big")]
    for sym in sorted(code_lengths):
        parts.append(bytes([sym, code_lengths[sym]]))
    return b"".join(parts)


def _parse_header(data: bytes, offset: int = 0) -> tuple[dict[int, int], int, int]:
    """Parse the header starting at *offset*.

    Returns ``(code_lengths, next_offset, original_size)``.
    """
    if offset + 6 > len(data):
        raise _HuffmanDecodeError("Truncated header: missing size + symbol count")
    original_size = int.from_bytes(data[offset : offset + 4], "big")
    offset += 4
    num_syms = int.from_bytes(data[offset : offset + 2], "big")
    offset += 2
    code_lengths: dict[int, int] = {}
    for _ in range(num_syms):
        if offset + 2 > len(data):
            raise _HuffmanDecodeError("Truncated header: missing symbol entry")
        sym = data[offset]
        length = data[offset + 1]
        if length == 0:
            raise _HuffmanDecodeError("Zero-length Huffman code")
        code_lengths[sym] = length
        offset += 2
    return code_lengths, offset, original_size


# ---------------------------------------------------------------------------
# Codec class
# ---------------------------------------------------------------------------


class HuffmanCodec(CompressionCodec):
    """Canonical Huffman coding codec.

    Compresses byte strings by building a frequency-optimised prefix code,
    encoding the symbol table in a header, and packing the encoded bitstream.
    """

    def compress(self, data: bytes) -> bytes:
        """Compress *data* with canonical Huffman coding.

        Edge cases:
        - Empty input → empty output.
        - Single unique byte → header with 1 symbol + zero-bit body.
        """
        if not data:
            return b""

        freqs = _build_frequencies(data)
        tree = _build_tree(freqs)
        code_lengths = _code_lengths_from_tree(tree)
        codes = _canonical_codes(code_lengths)

        header = _build_header(code_lengths, len(data))

        bits: list[int] = []
        for b in data:
            canonical = codes[b]
            length = code_lengths[b]
            for shift in range(length - 1, -1, -1):
                bits.append((canonical >> shift) & 1)

        body = _pack_bits(bits)
        return header + body

    def decompress(self, data: bytes) -> bytes:
        """Decompress a Huffman-compressed byte string.

        Stops decoding once *original_size* bytes have been produced, so
        trailing padding bits in the last byte are ignored.

        Raises:
            _HuffmanDecodeError: If the data is corrupt or truncated.
        """
        if not data:
            return b""

        code_lengths, offset, original_size = _parse_header(data, 0)
        body = data[offset:]
        if not code_lengths:
            return b""

        decode_table = _build_decode_table(code_lengths)

        result = bytearray()
        code = 0
        code_len = 0
        for byte in body:
            for shift in range(7, -1, -1):
                if len(result) >= original_size:
                    break
                code = (code << 1) | ((byte >> shift) & 1)
                code_len += 1
                key = (code << 5) | code_len
                sym = decode_table.get(key)
                if sym is not None:
                    result.append(sym)
                    code = 0
                    code_len = 0
            if len(result) >= original_size:
                break

        return bytes(result)
