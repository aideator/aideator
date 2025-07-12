"""
Encryption service for secure API key storage.

Uses Fernet symmetric encryption with key derivation from a master key.
"""

import base64
import os
from typing import cast

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, master_key: str | None = None):
        """Initialize encryption service with master key.

        Args:
            master_key: Base64-encoded master key. If not provided, uses ENCRYPTION_KEY env var.
        """
        from app.core.config import get_settings
        settings = get_settings()
        
        # In development mode, create a dummy cipher if encryption is disabled
        if not settings.require_per_user_keys or settings.simple_dev_mode:
            # Create a simple cipher for development (not actually secure)
            self._cipher_suite = self._create_dev_cipher()
            self._dev_mode = True
            return
            
        if master_key is None:
            master_key = os.getenv("ENCRYPTION_KEY")
            if not master_key:
                raise ValueError("ENCRYPTION_KEY environment variable must be set")

        # Derive encryption key from master key using PBKDF2
        self._cipher_suite = self._create_cipher(master_key)
        self._dev_mode = False

    def _create_cipher(self, master_key: str) -> Fernet:
        """Create Fernet cipher from master key.

        Uses PBKDF2 to derive a proper encryption key from the master key.
        """
        # Use a fixed salt for deterministic key derivation
        # In production, you might want per-user salts for additional security
        salt = b"aideator-provider-keys-v1"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Derive key from master key
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return Fernet(key)
    
    def _create_dev_cipher(self) -> Fernet:
        """Create a simple cipher for development mode."""
        # Use a fixed key for development (not secure, but consistent)
        dev_key = base64.urlsafe_b64encode(b"dev-key-for-aideator-development")
        return Fernet(dev_key)

    def encrypt_api_key(self, api_key: str) -> tuple[str, str]:
        """Encrypt an API key and return encrypted value and hint.

        Args:
            api_key: The plaintext API key to encrypt

        Returns:
            Tuple of (encrypted_key, key_hint) where key_hint is last 4 chars
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        # Encrypt the key
        encrypted = self._cipher_suite.encrypt(api_key.encode())
        encrypted_str = base64.urlsafe_b64encode(encrypted).decode()

        # Create hint from last 4 characters
        key_hint = f"...{api_key[-4:]}" if len(api_key) >= 4 else "****"

        return encrypted_str, key_hint

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key.

        Args:
            encrypted_key: The encrypted API key

        Returns:
            The decrypted API key
        """
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")

        try:
            # Decode from base64 and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self._cipher_suite.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {e!s}")

    @staticmethod
    def generate_master_key() -> str:
        """Generate a new master encryption key.

        Returns:
            Base64-encoded master key suitable for ENCRYPTION_KEY env var
        """
        return Fernet.generate_key().decode()

    def rotate_key(self, old_encrypted: str, new_master_key: str) -> str:
        """Rotate an encrypted value to use a new master key.

        Args:
            old_encrypted: Value encrypted with current master key
            new_master_key: New master key to use

        Returns:
            Value encrypted with new master key
        """
        # Decrypt with current key
        decrypted = self.decrypt_api_key(old_encrypted)

        # Create new cipher with new key
        new_cipher = self._create_cipher(new_master_key)

        # Encrypt with new key
        encrypted = new_cipher.encrypt(decrypted.encode())
        return base64.urlsafe_b64encode(encrypted).decode()


# Singleton instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get the singleton encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    # Type narrowing for type checker
    return cast("EncryptionService", _encryption_service)
