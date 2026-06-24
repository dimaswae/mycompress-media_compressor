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
    def capacity(self, image: Image.Image) -> int:
        """Return the maximum number of bits that can be hidden in *image*."""
        ...

    @abstractmethod
    def embed(self, image: Image.Image, message: bytes, password: str = "") -> Image.Image:
        """Embed *message* into *image* and return a new image.

        The original *image* is not modified.

        Args:
            image: Carrier image (PIL ``Image``).
            message: Bytes to hide.
            password: Optional passphrase for basic obfuscation.

        Returns:
            A new ``Image`` containing the hidden message.
        """
        ...

    @abstractmethod
    def extract(self, image: Image.Image, password: str = "") -> bytes:
        """Extract a hidden message from *image*.

        Args:
            image: Stego image (PIL ``Image``).
            password: Passphrase used during embedding.

        Returns:
            The hidden message as bytes.
        """
        ...
