"""Unit tests for ``core/metrics/image_metrics.py`` (IMG-14)."""

import numpy as np
import pytest

from app.core.metrics.image_metrics import mse, psnr, ssim


def _solid_image(value: int, size: tuple[int, int] = (8, 8)) -> np.ndarray:
    """Create an 8-bit RGB image filled with a single colour."""
    return np.full((*size, 3), value, dtype=np.uint8)


class TestPsnr:
    def test_identical_images_return_inf(self) -> None:
        img = _solid_image(128)
        assert np.isinf(psnr(img, img))

    def test_different_images_finite(self) -> None:
        a = _solid_image(0)
        b = _solid_image(1)  # single-step diff → PSNR ≈ 48 dB
        result = psnr(a, b)
        assert np.isfinite(result)
        assert result > 40.0


class TestSsim:
    def test_identical_images_return_one(self) -> None:
        img = _solid_image(100)
        assert ssim(img, img) == pytest.approx(1.0)

    def test_completely_different_images_lower(self) -> None:
        a = _solid_image(0)
        b = _solid_image(255)
        result = ssim(a, b)
        assert result < 1.0
        assert result >= -1.0  # SSIM is bounded in [-1, 1]


class TestMse:
    def test_identical_images_return_zero(self) -> None:
        img = _solid_image(128)
        assert mse(img, img) == pytest.approx(0.0)

    def test_different_images_positive(self) -> None:
        a = _solid_image(0)
        b = _solid_image(255)
        result = mse(a, b)
        assert result > 0
