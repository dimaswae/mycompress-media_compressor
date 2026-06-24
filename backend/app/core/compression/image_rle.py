"""Byte-level RLE (run-length encoding) codec for image data.

Each run of identical bytes is encoded as **two bytes**: the byte value
followed by the run length (1–255).  This means data with no runs will
**expand** (roughly 2×), while data with long runs (e.g. flat-colour images)
will compress significantly.
"""

from app.core.compression.base import CompressionCodec
from app.utils.exceptions import AppError


class _RleDecodeError(AppError):
    """Raised when the RLE bitstream is malformed or corrupt."""

    def __init__(self, message: str = "Corrupt RLE compressed data") -> None:
        super().__init__(code="RLE_DECODE_ERROR", message=message)


class RleCodec(CompressionCodec):
    """Run-length encoding codec.

    Format::

        [byte_1] [run_len_1] [byte_2] [run_len_2] ...

    Each ``run_len`` is a single byte (0–255) so the maximum representable run
    is 255 repetitions of a single byte value.
    """

    def compress(self, data: bytes) -> bytes:
        """Compress *data* with byte-level RLE."""
        if not data:
            return b""

        result = bytearray()
        prev = data[0]
        count = 1

        for b in data[1:]:
            if b == prev and count < 255:
                count += 1
            else:
                result.append(prev)
                result.append(count)
                prev = b
                count = 1

        result.append(prev)
        result.append(count)
        return bytes(result)

    def decompress(self, data: bytes) -> bytes:
        """Decompress an RLE-encoded byte string.

        Raises:
            _RleDecodeError: If the data ends on an odd byte (incomplete pair)
                or a run has zero length.
        """
        if not data:
            return b""

        if len(data) % 2 != 0:
            raise _RleDecodeError(
                "RLE data length must be even (pairs of byte+count)"
            )

        result = bytearray()
        i = 0
        while i < len(data):
            byte_val = data[i]
            count = data[i + 1]
            if count == 0:
                raise _RleDecodeError("RLE run length must not be zero")
            result.extend([byte_val] * count)
            i += 2

        return bytes(result)
