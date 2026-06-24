"""Least-significant-bit (LSB) steganography for RGB images.

Embeds a message into the LSB of each colour channel of every pixel.
The message is prefixed with a 4-byte big-endian length so the decoder knows
how many bytes to extract.

If a *password* is provided, the payload is XOR-obfuscated with a key derived
from SHA-256 of the password before embedding (and XOR-ed again on extraction).
"""

import hashlib

import numpy as np
from PIL import Image

from app.core.steganography.base import StegoCodec
from app.utils.exceptions import AppError, CapacityExceededError


class _LsbExtractError(AppError):
    """Raised when LSB extraction encounters corrupt or truncated data."""

    def __init__(self, message: str = "Failed to extract message from image") -> None:
        super().__init__(code="LSB_EXTRACT_ERROR", message=message)


def _xor_mask(password: str, length: int) -> bytes:
    """Generate *length* bytes of XOR key from *password* via SHA-256."""
    key = hashlib.sha256(password.encode("utf-8")).digest()
    repeats = (length // len(key)) + 1
    return (key * repeats)[:length]


class LsbCodec(StegoCodec):
    """LSB steganography codec for RGB images.

    Message format in the bitstream::

        [message_length : 4 bytes big-endian]
        [message_bytes  : ...]
    """

    def capacity(self, image: Image.Image) -> int:
        """Return the maximum number of payload bits that can be embedded.

        This equals ``width × height × 3`` for RGB images (one bit per
        colour channel per pixel).  Non-RGB images are converted internally.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")
        w, h = image.size
        return w * h * 3  # one LSB per channel per pixel

    def embed(self, image: Image.Image, message: bytes, password: str = "") -> Image.Image:
        """Embed *message* into *image* and return a new image.

        The original *image* is not modified.

        Raises:
            CapacityExceededError: If the message (plus 4-byte length prefix
                and optional XOR overhead) exceeds the image's capacity.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        total_capacity_bits = self.capacity(image)

        # 4-byte big-endian length prefix
        length_bytes = len(message).to_bytes(4, "big")
        payload: bytes = length_bytes + message

        if password:
            payload = self._xor(payload, password)

        payload_bits_needed = len(payload) * 8
        if payload_bits_needed > total_capacity_bits:
            max_message_len = (total_capacity_bits // 8) - 4
            raise CapacityExceededError(
                f"Message size {len(message)} bytes exceeds maximum of "
                f"{max_message_len} bytes for this image "
                f"(image capacity = {total_capacity_bits} bits)"
            )

        arr = np.array(image, dtype=np.uint8)
        flat = arr.flatten()

        for i, byte_val in enumerate(payload):
            for bit_idx in range(8):
                bit = (byte_val >> (7 - bit_idx)) & 1
                flat[i * 8 + bit_idx] = (flat[i * 8 + bit_idx] & 0xFE) | bit

        result_arr = flat.reshape(arr.shape)
        return Image.fromarray(result_arr, mode="RGB")

    def extract(self, image: Image.Image, password: str = "") -> bytes:
        """Extract a hidden message from *image*.

        Reads the 4-byte length prefix, then extracts *length* message bytes.

        Raises:
            _LsbExtractError: If the extracted length is unreasonable or the
                image appears to contain no valid message.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        total_capacity_bits = self.capacity(image)
        arr = np.array(image, dtype=np.uint8)
        flat = arr.flatten()

        # Collect all LSBs from the image into a bit list
        all_bits = [int(p & 1) for p in flat]

        min_bits = 8 * 4  # we need at least the 4-byte length prefix
        if len(all_bits) < min_bits:
            raise _LsbExtractError("Image too small to contain a message length prefix")

        def _bits_to_bytes(bits: list[int]) -> bytes:
            result = bytearray()
            for i in range(0, len(bits), 8):
                chunk = bits[i : i + 8]
                if len(chunk) < 8:
                    break
                byte_val = 0
                for b in chunk:
                    byte_val = (byte_val << 1) | b
                result.append(byte_val)
            return bytes(result)

        # The number of payload bits we actually read is unknown at the start.
        # Strategy: read as many full bytes as the capacity allows, then use
        # the length prefix to know where to stop.
        usable_bits = (total_capacity_bits // 8) * 8  # round down to byte boundary
        raw_bytes = _bits_to_bytes(all_bits[:usable_bits])

        # First 4 bytes are the length (possibly XOR-obfuscated)
        # We'll extract all payload bytes and then process the length prefix
        # after de-obfuscation.
        # But de-obfuscation requires the full payload.  So extract all that
        # we can, de-obfuscate, then check the length.
        if password:
            raw_bytes = self._xor(raw_bytes, password)

        if len(raw_bytes) < 4:
            raise _LsbExtractError("Truncated payload: missing length prefix")

        msg_len = int.from_bytes(raw_bytes[:4], "big")

        if msg_len == 0:
            return b""

        if msg_len > total_capacity_bits // 8:
            raise _LsbExtractError(
                f"Declared message length {msg_len} exceeds image capacity — "
                f"possibly corrupt or wrong password"
            )

        if 4 + msg_len > len(raw_bytes):
            raise _LsbExtractError("Truncated payload: message body shorter than declared length")

        return raw_bytes[4 : 4 + msg_len]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _xor(data: bytes, password: str) -> bytes:
        """XOR *data* with a key derived from *password*."""
        mask = _xor_mask(password, len(data))
        return bytes(a ^ b for a, b in zip(data, mask))
