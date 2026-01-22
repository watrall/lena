"""Fernet-based helpers for encrypting/decrypting stored PII."""

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
    """Return a Fernet instance when configured, otherwise None."""
    key = os.getenv(_ENCRYPTION_KEY_ENV)
    if not key:
        return None

    # Ensure key is valid Fernet key (32 url-safe base64-encoded bytes)
    try:
        return Fernet(key.encode())
    except Exception as exc:
        logger.error("Invalid encryption key format: %s", exc)
        return None


def encrypt_pii(plaintext: str) -> str:
    """Encrypt a PII value; require encryption to be configured."""
    fernet = _get_fernet()
    if fernet is None:
        raise RuntimeError(
            f"{_ENCRYPTION_KEY_ENV} is not set; refuse to store PII unencrypted. "
            "Generate a key: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    encrypted = fernet.encrypt(plaintext.encode("utf-8"))
    return f"ENC:{encrypted.decode('utf-8')}"


def decrypt_pii(ciphertext: str) -> str:
    """Decrypt a stored PII value, supporting legacy plaintext values."""
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
    """Return True when an encryption key is configured."""
    return _get_fernet() is not None
