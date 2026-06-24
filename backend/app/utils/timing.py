"""``@timed`` decorator for measuring function execution time.

The decorator stores the last elapsed wall-clock time in milliseconds on
``wrapper.duration_ms`` so callers can inspect it after invocation.
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def timed(func: F) -> F:
    """Decorator that records elapsed wall-clock time on ``wrapper.duration_ms``.

    The decorated function's return value is unchanged.  After calling, read
    ``func.duration_ms`` (or equivalently ``wrapper.duration_ms``) to get the
    last execution time in milliseconds.

    Example::

        @timed
        def work(n: int) -> int:
            return sum(range(n))

        result = work(10_000_000)
        elapsed = work.duration_ms  # milliseconds
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        wrapper.duration_ms = (time.perf_counter() - start) * 1000.0  # type: ignore[attr-defined]
        return result

    wrapper.duration_ms = 0.0  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]
