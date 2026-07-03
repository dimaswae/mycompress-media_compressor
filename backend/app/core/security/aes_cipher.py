"""AES-GCM encryption utilities for secure message payload protection.

Uses PBKDF2HMAC with SHA-256 for key derivation and AES-GCM for authenticated
encryption. The nonce is generated per encryption and prepended to the ciphertext.
"""

import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from app.utils.exceptions import DecryptionError


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from *password* and *salt* using PBKDF2.

    Args:
        password: The passphrase to derive the key from.
        salt: 16-byte random salt for key derivation.

    Returns:
        32-byte key suitable for AES-256-GCM.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    """Encrypt *plaintext* using AES-GCM with *password*.

    Generates a fresh random salt and nonce for each encryption. The output format
    is: ``salt (16) || nonce (12) || ciphertext || tag (16)``.

    Args:
        plaintext: The bytes to encrypt.
        password: Passphrase for key derivation.

    Returns:
        Encrypted payload containing salt, nonce, ciphertext, and auth tag.
    """
    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext


def decrypt_bytes(encrypted_payload: bytes, password: str) -> bytes:
    """Decrypt *encrypted_payload* using AES-GCM with *password*.

    Expects the format: ``salt (16) || nonce (12) || ciphertext || tag (16)``.

    Args:
        encrypted_payload: The encrypted data from :func:`encrypt_bytes`.
        password: Passphrase used during encryption.

    Returns:
        The original plaintext bytes.

    Raises:
        DecryptionError: If decryption fails (wrong password, corrupt/tampered data).
    """
    if len(encrypted_payload) < 16 + 12 + 16 + 4:
        raise DecryptionError(
            "Encrypted payload too short to contain salt, nonce, and tag"
        )

    salt = encrypted_payload[:16]
    nonce = encrypted_payload[16:28]
    ciphertext = encrypted_payload[28:]

    try:
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e
