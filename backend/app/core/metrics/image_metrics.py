"""Image-specific quality metrics: PSNR, SSIM, MSE.

Wraps ``scikit-image`` metric functions.  All functions accept two
``numpy.ndarray`` arrays of the same shape.
"""

import numpy as np
from skimage.metrics import (
    mean_squared_error as _sk_mse,
    peak_signal_noise_ratio as _sk_psnr,
    structural_similarity as _sk_ssim,
)


def psnr(original: np.ndarray, processed: np.ndarray) -> float:
    """Compute the Peak Signal-to-Noise Ratio between two images.

    Higher values indicate better quality.  Identical images produce ``inf``.
    """
    return float(_sk_psnr(original, processed))


def ssim(original: np.ndarray, processed: np.ndarray) -> float:
    """Compute the Structural Similarity Index between two images.

    Returns a value in [-1, 1], where 1.0 means identical.

    For multi-channel images the ``channel_axis`` parameter is set to ``-1``
    (assumes channels-last layout, i.e. ``(H, W, C)``).
    """
    if original.ndim == 3:
        return float(_sk_ssim(original, processed, channel_axis=-1))
    return float(_sk_ssim(original, processed))


def mse(original: np.ndarray, processed: np.ndarray) -> float:
    """Compute the Mean Squared Error between two images.

    Lower values indicate better quality.  Identical images produce ``0.0``.
    """
    return float(_sk_mse(original, processed))
