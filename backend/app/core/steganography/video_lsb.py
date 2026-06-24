"""Least-significant-bit (LSB) steganography for MP4 video.

Embeds a message into the LSB of each byte of the ``mdat`` box payload.
The message is prefixed with a 4-byte big-endian length.

If a *password* is provided, the payload is XOR-obfuscated with a key
derived from SHA-256 of the password (same scheme as ``audio_lsb``).
"""

import hashlib
import struct

from app.utils.exceptions import AppError, CapacityExceededError, UnsupportedFormatError


class _VideoLsbExtractError(AppError):
    """Raised when LSB extraction encounters corrupt or truncated data."""

    def __init__(self, message: str = "Failed to extract message from video") -> None:
        super().__init__(code="VIDEO_LSB_EXTRACT_ERROR", message=message)


def _xor_mask(password: str, length: int) -> bytes:
    """Generate *length* bytes of XOR key from *password* via SHA-256."""
    key = hashlib.sha256(password.encode("utf-8")).digest()
    repeats = (length // len(key)) + 1
    return (key * repeats)[:length]


def _is_mp4(data: bytes) -> bool:
    """Return True if *data* starts with a valid MP4 signature."""
    if len(data) < 8:
        return False
    if data[:4] == b"\x00\x00\x00\x18" and data[4:8] == b"ftyp":
        return True
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return True
    return False


def _find_mdat_payload(data: bytes) -> tuple[int, int]:
    """Locate the ``mdat`` box payload inside an MP4 container.

    Iterates over top-level boxes (size + type) until the ``mdat`` box is
    found.  Returns ``(payload_offset, payload_size)`` — the offset and
    byte count of the data *after* the 8-byte box header.

    Raises ``UnsupportedFormatError`` if the box is not found.
    """
    pos = 0
    while pos + 8 <= len(data):
        (box_size,) = struct.unpack_from(">I", data, pos)
        box_type = data[pos + 4 : pos + 8]
        if box_type == b"mdat":
            payload_offset = pos + 8
            if box_size == 0:
                box_size = len(data) - pos
            actual_payload = box_size - 8
            if payload_offset + actual_payload > len(data):
                actual_payload = len(data) - payload_offset
            return payload_offset, actual_payload
        if box_size == 0:
            break
        pos += box_size
    raise UnsupportedFormatError("MP4 file contains no mdat box")


class VideoLsbCodec:
    """LSB steganography codec for MP4 video (mdat payload bytes).

    Message format in the bitstream::

        [message_length : 4 bytes big-endian]
        [message_bytes  : ...]
    """

    def capacity(self, video_bytes: bytes) -> int:
        """Return the maximum number of payload bits that can be embedded.

        Each byte of the mdat payload provides exactly one LSB.
        """
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")
        _offset, size = _find_mdat_payload(video_bytes)
        return size

    def embed(
        self, video_bytes: bytes, message: bytes, password: str = ""
    ) -> bytes:
        """Embed *message* into *video_bytes* and return a new MP4 byte string.

        Raises:
            UnsupportedFormatError: If the input is not a valid MP4.
            CapacityExceededError: If the message exceeds available capacity.
        """
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")

        offset, data_size = _find_mdat_payload(video_bytes)
        total_bits = data_size

        length_bytes = len(message).to_bytes(4, "big")
        payload: bytes = length_bytes + message

        if password:
            payload = self._xor(payload, password)

        if len(payload) * 8 > total_bits:
            max_msg = (total_bits // 8) - 4
            raise CapacityExceededError(
                f"Message size {len(message)} bytes exceeds maximum of "
                f"{max_msg} bytes (mdat capacity = {total_bits} bits)"
            )

        header = video_bytes[:offset]
        mdat_payload = bytearray(video_bytes[offset : offset + data_size])

        for i, byte_val in enumerate(payload):
            for bit_idx in range(8):
                bit = (byte_val >> (7 - bit_idx)) & 1
                mdat_payload[i * 8 + bit_idx] = (mdat_payload[i * 8 + bit_idx] & 0xFE) | bit

        return bytes(header) + bytes(mdat_payload)

    def extract(self, video_bytes: bytes, password: str = "") -> bytes:
        """Extract a hidden message from *video_bytes*.

        Raises:
            UnsupportedFormatError: If the input is not a valid MP4.
            _VideoLsbExtractError: If the payload is corrupt or truncated.
        """
        if not _is_mp4(video_bytes):
            raise UnsupportedFormatError("Only MP4 files are supported for video steganography")

        offset, data_size = _find_mdat_payload(video_bytes)
        total_bits = data_size

        mdat_payload = video_bytes[offset : offset + data_size]

        all_bits = [int(b & 1) for b in mdat_payload]

        usable_bits = (total_bits // 8) * 8
        raw_bytes_list: list[int] = []
        for i in range(0, usable_bits, 8):
            chunk = all_bits[i : i + 8]
            if len(chunk) < 8:
                break
            byte_val = 0
            for b in chunk:
                byte_val = (byte_val << 1) | b
            raw_bytes_list.append(byte_val)
        raw_bytes = bytes(raw_bytes_list)

        if password:
            raw_bytes = self._xor(raw_bytes, password)

        if len(raw_bytes) < 4:
            raise _VideoLsbExtractError("Truncated payload: missing length prefix")

        msg_len = int.from_bytes(raw_bytes[:4], "big")

        if msg_len == 0:
            return b""

        if msg_len > data_size:
            raise _VideoLsbExtractError(
                f"Declared message length {msg_len} exceeds mdat data size — "
                f"possibly corrupt or wrong password"
            )

        if 4 + msg_len > len(raw_bytes):
            raise _VideoLsbExtractError(
                "Truncated payload: message body shorter than declared length"
            )

        return raw_bytes[4 : 4 + msg_len]

    @staticmethod
    def _xor(data: bytes, password: str) -> bytes:
        """XOR *data* with a key derived from *password*."""
        mask = _xor_mask(password, len(data))
        return bytes(a ^ b for a, b in zip(data, mask))
