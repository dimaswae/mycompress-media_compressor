"""Unit tests for ``core/steganography/image_lsb.py`` (IMG-10, IMG-11, IMG-12, IMG-13)."""

import numpy as np
import pytest
from PIL import Image

from app.core.steganography.image_lsb import LsbCodec
from app.utils.exceptions import AppError, CapacityExceededError


def _small_rgb(size: tuple[int, int] = (4, 4)) -> Image.Image:
    """Return a small RGB image (default 4×4) filled with a known pattern."""
    arr = np.zeros((*size, 3), dtype=np.uint8)
    for y in range(size[1]):
        for x in range(size[0]):
            arr[y, x] = [x * 60 % 256, y * 60 % 256, (x + y) * 40 % 256]
    return Image.fromarray(arr, mode="RGB")


class TestLsbCapacity:
    def test_capacity_known_image_size(self) -> None:
        """4×4 RGB image → 4 × 4 × 3 = 48 bits."""
        codec = LsbCodec()
        img = _small_rgb((4, 4))
        assert codec.capacity(img) == 48

    def test_capacity_larger_image(self) -> None:
        codec = LsbCodec()
        img = _small_rgb((10, 10))
        assert codec.capacity(img) == 300  # 10 * 10 * 3


class TestLsbEmbed:
    def test_embed_alters_only_lsb(self) -> None:
        """Pixel diffs between original and stego are ≤1 per channel."""
        codec = LsbCodec()
        original = _small_rgb((8, 8))
        orig_arr = np.array(original)

        message = b"hi!"
        stego = codec.embed(original, message)
        stego_arr = np.array(stego)

        diff = np.abs(stego_arr.astype(np.int16) - orig_arr.astype(np.int16))
        assert diff.max() <= 1
        assert stego.size == original.size

    def test_embed_preserves_dimensions(self) -> None:
        codec = LsbCodec()
        original = _small_rgb((16, 16))
        stego = codec.embed(original, b"hello")
        assert stego.size == original.size
        assert stego.mode == original.mode

    def test_embed_with_password(self) -> None:
        codec = LsbCodec()
        original = _small_rgb((16, 16))
        stego = codec.embed(original, b"secret", password="pass123")
        assert stego.size == original.size


class TestLsbExtract:
    def test_round_trip_no_password(self) -> None:
        codec = LsbCodec()
        original = _small_rgb((16, 16))
        message = b"Hello, LSB!"
        stego = codec.embed(original, message)
        extracted = codec.extract(stego)
        assert extracted == message

    def test_round_trip_with_password(self) -> None:
        codec = LsbCodec()
        original = _small_rgb((16, 16))
        message = b"Password-protected message"
        stego = codec.embed(original, message, password="s3cret!")
        extracted = codec.extract(stego, password="s3cret!")
        assert extracted == message

    def test_extract_empty_message(self) -> None:
        codec = LsbCodec()
        original = _small_rgb((4, 4))
        stego = codec.embed(original, b"")
        extracted = codec.extract(stego)
        assert extracted == b""

    def test_extract_wrong_password_raises_error(self) -> None:
        """Wrong password causes extract to raise an ``AppError``."""
        codec = LsbCodec()
        original = _small_rgb((16, 16))
        message = b"secret data"
        stego = codec.embed(original, message, password="correct")
        with pytest.raises(AppError):
            codec.extract(stego, password="wrong")


class TestLsbCapacityExceeded:
    def test_oversized_message_raises_before_corrupting(self) -> None:
        codec = LsbCodec()
        img = _small_rgb((4, 4))  # 48 bit capacity → max message = 2 bytes (6 - 4 = 2)

        # Save original pixels to verify no corruption occurred
        orig_arr = np.array(img).copy()

        with pytest.raises(CapacityExceededError, match="exceeds"):
            codec.embed(img, b"this message is way too long for a 4x4 image")

        # Verify image was not corrupted
        assert np.array_equal(np.array(img), orig_arr)

    def test_exception_is_app_error_subclass(self) -> None:
        from app.utils.exceptions import AppError

        codec = LsbCodec()
        img = _small_rgb((4, 4))
        with pytest.raises(AppError):
            codec.embed(img, b"x" * 100)
