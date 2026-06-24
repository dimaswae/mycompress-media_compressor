"""Least-significant-bit (LSB) steganography for WAV audio.

Embeds a message into the LSB of each byte of the PCM sample data.
The message is prefixed with a 4-byte big-endian length.

If a *password* is provided, the payload is XOR-obfuscated with a key
derived from SHA-256 of the password (same scheme as ``image_lsb``).
"""

import hashlib
import struct

from app.utils.exceptions import AppError, CapacityExceededError, UnsupportedFormatError


class _AudioLsbExtractError(AppError):
    """Raised when LSB extraction encounters corrupt or truncated data."""

    def __init__(self, message: str = "Failed to extract message from audio") -> None:
        super().__init__(code="AUDIO_LSB_EXTRACT_ERROR", message=message)


def _xor_mask(password: str, length: int) -> bytes:
    """Generate *length* bytes of XOR key from *password* via SHA-256."""
    key = hashlib.sha256(password.encode("utf-8")).digest()
    repeats = (length // len(key)) + 1
    return (key * repeats)[:length]


def _is_wav(data: bytes) -> bool:
    """Return True if *data* starts with a valid RIFF/WAVE signature."""
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"


def _find_data_chunk(data: bytes) -> tuple[int, int]:
    """Locate the ``data`` chunk payload inside a RIFF/WAVE container.

    Returns ``(payload_offset, payload_size)``.
    Raises ``UnsupportedFormatError`` if the chunk is not found.
    """
    pos = 12
    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        (chunk_size,) = struct.unpack_from("<I", data, pos + 4)
        if chunk_id == b"data":
            payload_offset = pos + 8
            if payload_offset + chunk_size > len(data):
                chunk_size = len(data) - payload_offset
            return payload_offset, chunk_size
        pos += 8 + chunk_size
        if chunk_size % 2:
            pos += 1
    raise UnsupportedFormatError("WAV file contains no data chunk")


class AudioLsbCodec:
    """LSB steganography codec for WAV audio (PCM samples).

    Message format in the bitstream::

        [message_length : 4 bytes big-endian]
        [message_bytes  : ...]
    """

    def capacity(self, wav_bytes: bytes) -> int:
        """Return the maximum number of payload bits that can be embedded.

        Each PCM byte provides exactly one LSB, so capacity equals the number
        of PCM data bytes.
        """
        if not _is_wav(wav_bytes):
            raise UnsupportedFormatError("Only WAV files are supported for audio steganography")
        _offset, size = _find_data_chunk(wav_bytes)
        return size

    def embed(
        self, wav_bytes: bytes, message: bytes, password: str = ""
    ) -> bytes:
        """Embed *message* into *wav_bytes* and return a new WAV byte string.

        Raises:
            UnsupportedFormatError: If the input is not a valid WAV.
            CapacityExceededError: If the message exceeds available capacity.
        """
        if not _is_wav(wav_bytes):
            raise UnsupportedFormatError("Only WAV files are supported for audio steganography")

        offset, data_size = _find_data_chunk(wav_bytes)
        total_bits = data_size

        length_bytes = len(message).to_bytes(4, "big")
        payload: bytes = length_bytes + message

        if password:
            payload = self._xor(payload, password)

        if len(payload) * 8 > total_bits:
            max_msg = (total_bits // 8) - 4
            raise CapacityExceededError(
                f"Message size {len(message)} bytes exceeds maximum of "
                f"{max_msg} bytes (PCM capacity = {total_bits} bits)"
            )

        header = wav_bytes[:offset]
        pcm = bytearray(wav_bytes[offset : offset + data_size])

        for i, byte_val in enumerate(payload):
            for bit_idx in range(8):
                bit = (byte_val >> (7 - bit_idx)) & 1
                pcm[i * 8 + bit_idx] = (pcm[i * 8 + bit_idx] & 0xFE) | bit

        return bytes(header) + bytes(pcm)

    def extract(self, wav_bytes: bytes, password: str = "") -> bytes:
        """Extract a hidden message from *wav_bytes*.

        Raises:
            UnsupportedFormatError: If the input is not a valid WAV.
            _AudioLsbExtractError: If the payload is corrupt or truncated.
        """
        if not _is_wav(wav_bytes):
            raise UnsupportedFormatError("Only WAV files are supported for audio steganography")

        offset, data_size = _find_data_chunk(wav_bytes)
        total_bits = data_size

        pcm = wav_bytes[offset : offset + data_size]

        all_bits = [int(b & 1) for b in pcm]

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
            raise _AudioLsbExtractError("Truncated payload: missing length prefix")

        msg_len = int.from_bytes(raw_bytes[:4], "big")

        if msg_len == 0:
            return b""

        pcm_bytes = data_size
        if msg_len > pcm_bytes:
            raise _AudioLsbExtractError(
                f"Declared message length {msg_len} exceeds PCM data size — "
                f"possibly corrupt or wrong password"
            )

        if 4 + msg_len > len(raw_bytes):
            raise _AudioLsbExtractError(
                "Truncated payload: message body shorter than declared length"
            )

        return raw_bytes[4 : 4 + msg_len]

    @staticmethod
    def _xor(data: bytes, password: str) -> bytes:
        """XOR *data* with a key derived from *password*."""
        mask = _xor_mask(password, len(data))
        return bytes(a ^ b for a, b in zip(data, mask))
