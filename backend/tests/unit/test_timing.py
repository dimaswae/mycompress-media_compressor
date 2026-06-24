"""Unit tests for ``utils/timing.py`` — ``@timed`` decorator (IMG-16)."""

import time

from app.utils.timing import timed


class TestTimedDecorator:
    def test_return_value_unchanged(self) -> None:
        @timed
        def add(a: int, b: int) -> int:
            return a + b

        result = add(3, 5)
        assert result == 8

    def test_records_elapsed_ms(self) -> None:
        @timed
        def snooze(seconds: float) -> str:
            time.sleep(seconds)
            return "done"

        result = snooze(0.015)
        assert result == "done"
        assert snooze.duration_ms >= 12.0  # allow some tolerance
