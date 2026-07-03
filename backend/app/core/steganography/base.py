"""Abstract base class for all steganography codecs.

Every codec must implement ``capacity``, ``embed``, and ``extract``.
"""

from abc import ABC, abstractmethod

from PIL import Image


class StegoCodec(ABC):
    """Abstract steganography codec.

    Subclasses **must** override :meth:`capacity`, :meth:`embed`, and
    :meth:`extract`.
    """

    @abstractmethod
    def capacity(self, carrier: Image.Image | bytes) -> int:
        """Return the maximum number of bits that can be hidden."""
        ...

    @abstractmethod
    def embed(self, carrier: Image.Image | bytes, message: bytes) -> Image.Image | bytes:
        """Embed *message* into *carrier* and return a new carrier.

        The original *carrier* is not modified.

        Args:
            carrier: Carrier image (PIL ``Image``) or audio/video bytes.
            message: Bytes to hide.

        Returns:
            A new carrier containing the hidden message.
        """
        ...

    @abstractmethod
    def extract(self, carrier: Image.Image | bytes) -> bytes:
        """Extract a hidden message from *carrier*.

        Args:
            carrier: Stego carrier (PIL ``Image`` or bytes).

        Returns:
            The hidden message as bytes.
        """
        ...
