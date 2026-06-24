"""Abstract base class for all compression codecs.

Every codec must implement ``compress`` and ``decompress``, both accepting and
returning ``bytes``.  Subclasses that omit either method will fail to
instantiate with a ``TypeError`` at class-creation time.
"""

from abc import ABC, abstractmethod


class CompressionCodec(ABC):
    """Abstract compression codec.

    Subclasses **must** override both :meth:`compress` and :meth:`decompress`.
    """

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compress *data* and return the compressed byte string."""
        ...

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompress *data* and return the original byte string."""
        ...
