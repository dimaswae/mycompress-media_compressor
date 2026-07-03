"""Unit tests for core/security/aes_cipher.py (SEC-01/SEC-02/SEC-03/SEC-04)."""

import pytest

from app.core.security.aes_cipher import decrypt_bytes, derive_key, encrypt_bytes
from app.utils.exceptions import DecryptionError


class TestDeriveKey:
    def test_same_inputs_same_key(self) -> None:
        """Same password and salt produce the same key."""
        salt = b"0" * 16
        key1 = derive_key("password", salt)
        key2 = derive_key("password", salt)
        assert key1 == key2

    def test_different_salt_different_key(self) -> None:
        """Different salt produces different key."""
        key1 = derive_key("password", b"0" * 16)
        key2 = derive_key("password", b"1" * 16)
        assert key1 != key2

    def test_different_password_different_key(self) -> None:
        """Different password produces different key."""
        salt = b"0" * 16
        key1 = derive_key("password1", salt)
        key2 = derive_key("password2", salt)
        assert key1 != key2


class TestEncryptBytes:
    def test_output_different_each_time(self) -> None:
        """Each encryption produces unique ciphertext (random nonce)."""
        ct1 = encrypt_bytes(b"message", "password")
        ct2 = encrypt_bytes(b"message", "password")
        assert ct1 != ct2

    def test_output_format(self) -> None:
        """Output contains salt (16) + nonce (12) + ciphertext + tag (16)."""
        ct = encrypt_bytes(b"message", "password")
        assert len(ct) >= 16 + 12 + 4 + 16  # salt + nonce + 4-byte msg + tag

    def test_plaintext_not_in_output(self) -> None:
        """Plaintext is not visible in ciphertext."""
        ct = encrypt_bytes(b"secret message", "password")
        assert b"secret message" not in ct


class TestDecryptBytes:
    def test_roundtrip(self) -> None:
        """Encrypt then decrypt returns original plaintext."""
        plaintext = b"Hello, World!"
        encrypted = encrypt_bytes(plaintext, "mypassword")
        decrypted = decrypt_bytes(encrypted, "mypassword")
        assert decrypted == plaintext

    def test_wrong_password_raises(self) -> None:
        """Wrong password raises DecryptionError."""
        encrypted = encrypt_bytes(b"secret", "correct")
        with pytest.raises(DecryptionError):
            decrypt_bytes(encrypted, "wrong")

    def test_tampered_data_raises(self) -> None:
        """Tampered ciphertext raises DecryptionError."""
        encrypted = encrypt_bytes(b"secret", "password")
        tampered = encrypted[:30] + bytes([encrypted[30] ^ 0xFF]) + encrypted[31:]
        with pytest.raises(DecryptionError):
            decrypt_bytes(tampered, "password")

    def test_short_payload_raises(self) -> None:
        """Payload shorter than minimum raises DecryptionError."""
        with pytest.raises(DecryptionError, match="too short"):
            decrypt_bytes(b"short", "password")