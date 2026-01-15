"""Cryptographic utilities for PII protection.

Provides symmetric encryption for sensitive data at rest using Fernet.
The encryption key should be set via LENA_ENCRYPTION_KEY environment variable.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Environment variable for encryption key
_ENCRYPTION_KEY_ENV = "LENA_ENCRYPTION_KEY"


@lru_cache(maxsize=1)
def _get_fernet() -> Optional[Fernet]:
    """Get the Fernet cipher instance, or None if encryption is disabled.

    The key is derived from the LENA_ENCRYPTION_KEY environment variable.
    If not set, encryption is disabled and a warning is logged.

    Returns:
        A Fernet instance for encryption/decryption, or None if disabled.
    """
    key = os.getenv(_ENCRYPTION_KEY_ENV)
    if not key:
        logger.warning(
            "%s not set - PII will be stored in plaintext. "
            "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
            _ENCRYPTION_KEY_ENV,
        )
        return None

    # Ensure key is valid Fernet key (32 url-safe base64-encoded bytes)
    try:
        return Fernet(key.encode())
    except Exception as exc:
        logger.error("Invalid encryption key format: %s", exc)
        return None


def encrypt_pii(plaintext: str) -> str:
    """Encrypt sensitive PII data.

    If encryption is not configured, returns the plaintext with a marker prefix.

    Args:
        plaintext: The sensitive data to encrypt.

    Returns:
        Encrypted data as a base64 string, or original text if encryption disabled.
    """
    fernet = _get_fernet()
    if fernet is None:
        return plaintext

    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return f"ENC:{encrypted.decode('utf-8')}"


def decrypt_pii(ciphertext: str) -> str:
    """Decrypt sensitive PII data.

    Handles both encrypted (ENC: prefix) and plaintext data for backwards
    compatibility with existing unencrypted records.

    Args:
        ciphertext: The encrypted data or plaintext.

    Returns:
        The decrypted plaintext.
    """
    # Handle unencrypted legacy data
    if not ciphertext.startswith("ENC:"):
        return ciphertext

    fernet = _get_fernet()
    if fernet is None:
        logger.warning("Cannot decrypt - encryption key not configured")
        return "[ENCRYPTED - KEY NOT AVAILABLE]"

    try:
        encrypted_data = ciphertext[4:]  # Remove "ENC:" prefix
        decrypted = fernet.decrypt(encrypted_data.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt PII - invalid token or wrong key")
        return "[DECRYPTION FAILED]"
    except Exception as exc:
        logger.error("Decryption error: %s", exc)
        return "[DECRYPTION ERROR]"


def is_encryption_enabled() -> bool:
    """Check if PII encryption is configured and enabled.

    Returns:
        True if encryption is available, False otherwise.
    """
    return _get_fernet() is not None
