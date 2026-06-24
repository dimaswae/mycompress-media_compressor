"""Media-agnostic metrics: compression ratio and processing time.

``compression_ratio`` is a pure calculation of ``original_size / compressed_size``.
``processing_time`` applies the ``@timed`` decorator to capture elapsed
wall-clock time of any callable.
"""

from collections.abc import Callable
from typing import Any

from app.utils.timing import timed


def compression_ratio(original_size: int, compressed_size: int) -> float:
    """Calculate the compression ratio.

    Returns ``original_size / compressed_size``.

    Raises:
        ZeroDivisionError: If *compressed_size* is zero.
    """
    return original_size / compressed_size


def processing_time(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Call *func* with the given arguments and measure elapsed time.

    The decorated function is wrapped with ``@timed`` so its return value is
    unchanged.  The elapsed time is the decorator's ``duration_ms`` attribute.

    Returns:
        ``(result, elapsed_ms)`` where *result* is whatever *func* returned
        and *elapsed_ms* is the wall-clock time in milliseconds.
    """
    timed_func = timed(func)
    result = timed_func(*args, **kwargs)
    return result, timed_func.duration_ms  # type: ignore[attr-defined]
