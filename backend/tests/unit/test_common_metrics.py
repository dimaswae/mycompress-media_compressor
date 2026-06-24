"""Unit tests for ``core/metrics/common_metrics.py`` (IMG-15)."""

import time

import pytest

from app.core.metrics.common_metrics import compression_ratio, processing_time


class TestCompressionRatio:
    def test_known_byte_sizes(self) -> None:
        assert compression_ratio(100, 50) == 2.0
        assert compression_ratio(1000, 100) == 10.0
        assert compression_ratio(0, 100) == 0.0

    def test_ratio_less_than_one_for_expansion(self) -> None:
        assert compression_ratio(50, 100) == 0.5

    def test_zero_compressed_size_raises(self) -> None:
        with pytest.raises(ZeroDivisionError):
            compression_ratio(100, 0)


class TestProcessingTime:
    def test_timing_on_sleep_dummy(self) -> None:
        def dummy() -> None:
            time.sleep(0.01)

        result, elapsed_ms = processing_time(dummy)
        assert result is None
        assert elapsed_ms >= 8.0  # allow tolerance

    def test_preserves_return_value(self) -> None:
        def add(a: int, b: int) -> int:
            time.sleep(0.005)
            return a + b

        result, elapsed_ms = processing_time(add, 3, 7)
        assert result == 10
        assert elapsed_ms >= 3.0
