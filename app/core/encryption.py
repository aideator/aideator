"""Encryption utilities for sensitive data."""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


def get_fernet_key() -> bytes:
    """Derive a Fernet key from the encryption key."""
    # Use PBKDF2 to derive a proper key from our encryption key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"aideator-salt",  # In production, use a proper salt
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.encryption_key.encode()))
    return key


def encrypt_token(token: str) -> str:
    """Encrypt a token for storage."""
    try:
        f = Fernet(get_fernet_key())
        encrypted = f.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error("Failed to encrypt token", error=str(e))
        raise ValueError("Failed to encrypt token") from e


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored token."""
    try:
        f = Fernet(get_fernet_key())
        decrypted = f.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error("Failed to decrypt token", error=str(e))
        raise ValueError("Failed to decrypt token") from e