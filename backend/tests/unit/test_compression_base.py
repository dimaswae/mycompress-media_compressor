"""Unit tests for ``core/compression/base.py`` — ``CompressionCodec`` ABC (IMG-01)."""

import pytest

from app.core.compression.base import CompressionCodec


class TestCompressionCodec:
    def test_cannot_instantiate_abc_directly(self) -> None:
        with pytest.raises(TypeError):
            CompressionCodec()  # type: ignore[abstract]

    def test_subclass_without_implementing_raises_typeerror(self) -> None:
        with pytest.raises(TypeError):
            class Incomplete(CompressionCodec):  # type: ignore[abstract]
                pass

            Incomplete()
