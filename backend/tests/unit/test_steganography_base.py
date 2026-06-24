"""Unit tests for ``core/steganography/base.py`` — ``StegoCodec`` ABC (IMG-09)."""

import pytest

from app.core.steganography.base import StegoCodec


class TestStegoCodec:
    def test_cannot_instantiate_abc_directly(self) -> None:
        with pytest.raises(TypeError):
            StegoCodec()  # type: ignore[abstract]

    def test_subclass_without_implementing_raises_typeerror(self) -> None:
        with pytest.raises(TypeError):
            class Incomplete(StegoCodec):  # type: ignore[abstract]
                pass

            Incomplete()
