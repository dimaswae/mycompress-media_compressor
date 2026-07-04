"""Least-significant-bit (LSB) steganography for RGB images.

Embeds a message into the LSB of each colour channel of every pixel.
The message is prefixed with a 4-byte big-endian length so the decoder knows
how many bytes to extract.

Note: Password-based obfuscation is now handled at the service layer via AES-GCM.
"""

from io import BytesIO
import numpy as np
from PIL import Image

from app.core.steganography.base import StegoCodec
from app.utils.exceptions import AppError, CapacityExceededError, InvalidImageError


class _LsbExtractError(AppError):
    """Raised when LSB extraction encounters corrupt or truncated data."""

    def __init__(self, message: str = "Failed to extract message from image") -> None:
        super().__init__(code="LSB_EXTRACT_ERROR", message=message)


def _to_pil_image(image: Image.Image | bytes) -> Image.Image:
    """Ensure the input is a valid PIL Image in RGB mode.

    If the input is bytes, attempts to open it. If it is already a PIL Image,
    it converts it to RGB if needed, and forces loading to catch decoding errors
    (e.g., from truncated or corrupt images).

    Raises:
        InvalidImageError: If the image cannot be opened, is corrupt, or fails conversion.
    """
    if isinstance(image, bytes):
        try:
            img = Image.open(BytesIO(image))
        except (Image.UnidentifiedImageError, OSError, ValueError, TypeError) as e:
            raise InvalidImageError(f"Invalid or corrupt image file: {str(e)}")
    elif isinstance(image, Image.Image):
        img = image
    else:
        raise InvalidImageError("Input must be a PIL Image or image bytes")

    try:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.load()  # Force PIL to load/decode the pixel data to catch any corrupt data/OSError
    except (Image.UnidentifiedImageError, OSError, ValueError, TypeError) as e:
        raise InvalidImageError(f"Invalid or corrupt image file: {str(e)}")

    return img


class LsbCodec(StegoCodec):
    """LSB steganography codec for RGB images.

    Message format in the bitstream::

        [message_length : 4 bytes big-endian]
        [message_bytes  : ...]
    """

    def capacity(self, image: Image.Image | bytes) -> int:
        """Return the maximum number of payload bits that can be embedded.

        This equals ``width × height × 3`` for RGB images (one bit per
        colour channel per pixel).  Non-RGB images are converted internally.
        """
        img = _to_pil_image(image)
        w, h = img.size
        return w * h * 3  # one LSB per channel per pixel

    def embed(self, image: Image.Image | bytes, message: bytes) -> Image.Image:
        """Embed *message* into *image* and return a new image.

        The original *image* is not modified.

        Raises:
            CapacityExceededError: If the message (plus 4-byte length prefix)
                exceeds the image's capacity.
            InvalidImageError: If the image is corrupt or invalid.
        """
        img = _to_pil_image(image)

        total_capacity_bits = self.capacity(img)

        # 4-byte big-endian length prefix
        length_bytes = len(message).to_bytes(4, "big")
        payload: bytes = length_bytes + message

        payload_bits_needed = len(payload) * 8
        if payload_bits_needed > total_capacity_bits:
            max_message_len = (total_capacity_bits // 8) - 4
            raise CapacityExceededError(
                f"Message size {len(message)} bytes exceeds maximum of "
                f"{max_message_len} bytes for this image "
                f"(image capacity = {total_capacity_bits} bits)"
            )

        try:
            arr = np.array(img, dtype=np.uint8)
            flat = arr.flatten()

            for i, byte_val in enumerate(payload):
                for bit_idx in range(8):
                    bit = (byte_val >> (7 - bit_idx)) & 1
                    flat[i * 8 + bit_idx] = (flat[i * 8 + bit_idx] & 0xFE) | bit

            result_arr = flat.reshape(arr.shape)
            return Image.fromarray(result_arr, mode="RGB")
        except (Image.UnidentifiedImageError, OSError, ValueError, TypeError) as e:
            raise InvalidImageError(f"Invalid or corrupt image file: {str(e)}")

    def extract(self, image: Image.Image | bytes) -> bytes:
        """Extract a hidden message from *image*.

        Reads the 4-byte length prefix, then extracts *length* message bytes.

        Raises:
            _LsbExtractError: If the extracted length is unreasonable or the
                image appears to contain no valid message.
            InvalidImageError: If the image is corrupt or invalid.
        """
        img = _to_pil_image(image)

        total_capacity_bits = self.capacity(img)
        try:
            arr = np.array(img, dtype=np.uint8)
            flat = arr.flatten()
        except (Image.UnidentifiedImageError, OSError, ValueError, TypeError) as e:
            raise InvalidImageError(f"Invalid or corrupt image file: {str(e)}")

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

