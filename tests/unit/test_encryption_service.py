"""
Comprehensive tests for the encryption service.
"""

import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from app.services.encryption_service import EncryptionService, get_encryption_service


class TestEncryptionService:
    """Test suite for EncryptionService."""

    @pytest.fixture
    def mock_master_key(self):
        """Generate a test master key."""
        return Fernet.generate_key().decode()

    @pytest.fixture
    def encryption_service(self, mock_master_key):
        """Create encryption service with test key."""
        return EncryptionService(master_key=mock_master_key)

    def test_init_with_provided_key(self, mock_master_key):
        """Test initialization with provided master key."""
        service = EncryptionService(master_key=mock_master_key)
        assert service._cipher_suite is not None

    def test_init_with_env_key(self, mock_master_key):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": mock_master_key}):
            service = EncryptionService()
            assert service._cipher_suite is not None

    def test_init_without_key_raises_error(self):
        """Test initialization without key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ENCRYPTION_KEY environment variable must be set"):
                EncryptionService()

    def test_encrypt_api_key(self, encryption_service):
        """Test API key encryption."""
        api_key = "sk-test-1234567890abcdef"
        encrypted, hint = encryption_service.encrypt_api_key(api_key)

        # Check encrypted is different from original
        assert encrypted != api_key
        assert len(encrypted) > 0

        # Check hint shows last 4 chars
        assert hint == "...cdef"

    def test_encrypt_api_key_short(self, encryption_service):
        """Test encryption of short API key."""
        api_key = "abc"
        encrypted, hint = encryption_service.encrypt_api_key(api_key)

        assert encrypted != api_key
        assert hint == "****"

    def test_encrypt_empty_key_raises_error(self, encryption_service):
        """Test encrypting empty key raises error."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            encryption_service.encrypt_api_key("")

    def test_decrypt_api_key(self, encryption_service):
        """Test API key decryption."""
        original_key = "sk-test-1234567890abcdef"
        encrypted, _ = encryption_service.encrypt_api_key(original_key)

        decrypted = encryption_service.decrypt_api_key(encrypted)
        assert decrypted == original_key

    def test_decrypt_empty_key_raises_error(self, encryption_service):
        """Test decrypting empty key raises error."""
        with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
            encryption_service.decrypt_api_key("")

    def test_decrypt_invalid_key_raises_error(self, encryption_service):
        """Test decrypting invalid key raises error."""
        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            encryption_service.decrypt_api_key("invalid-encrypted-data")

    def test_encrypt_decrypt_various_keys(self, encryption_service):
        """Test encryption/decryption of various API key formats."""
        test_keys = [
            "sk-proj-1234567890abcdef",
            "sk-ant-api03-1234567890abcdef",
            "AIzaSyD-1234567890abcdef",
            "1234567890abcdef",
            "very-long-key-" + "x" * 100,
        ]

        for key in test_keys:
            encrypted, hint = encryption_service.encrypt_api_key(key)
            decrypted = encryption_service.decrypt_api_key(encrypted)
            assert decrypted == key

    def test_generate_master_key(self):
        """Test master key generation."""
        key1 = EncryptionService.generate_master_key()
        key2 = EncryptionService.generate_master_key()

        # Keys should be valid base64
        assert len(key1) == 44  # Fernet keys are 44 chars
        assert key1 != key2  # Should be different each time

        # Should be usable as master key
        service = EncryptionService(master_key=key1)
        assert service._cipher_suite is not None

    def test_key_rotation(self, mock_master_key):
        """Test key rotation functionality."""
        # Create service with old key
        old_service = EncryptionService(master_key=mock_master_key)
        api_key = "sk-test-1234567890abcdef"
        encrypted_old, _ = old_service.encrypt_api_key(api_key)

        # Generate new master key
        new_master_key = EncryptionService.generate_master_key()

        # Rotate the encrypted value
        encrypted_new = old_service.rotate_key(encrypted_old, new_master_key)

        # Verify new encryption works with new key
        new_service = EncryptionService(master_key=new_master_key)
        decrypted = new_service.decrypt_api_key(encrypted_new)
        assert decrypted == api_key

        # Verify old encryption doesn't work with new key
        with pytest.raises(ValueError):
            new_service.decrypt_api_key(encrypted_old)

    def test_deterministic_key_derivation(self, mock_master_key):
        """Test that same master key produces same cipher."""
        service1 = EncryptionService(master_key=mock_master_key)
        service2 = EncryptionService(master_key=mock_master_key)

        api_key = "sk-test-1234567890abcdef"

        # Encrypt with first service
        encrypted1, _ = service1.encrypt_api_key(api_key)

        # Decrypt with second service (should work due to same master key)
        decrypted = service2.decrypt_api_key(encrypted1)
        assert decrypted == api_key

    def test_different_master_keys_incompatible(self):
        """Test that different master keys can't decrypt each other's data."""
        key1 = EncryptionService.generate_master_key()
        key2 = EncryptionService.generate_master_key()

        service1 = EncryptionService(master_key=key1)
        service2 = EncryptionService(master_key=key2)

        api_key = "sk-test-1234567890abcdef"
        encrypted, _ = service1.encrypt_api_key(api_key)

        # Should not be able to decrypt with different key
        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            service2.decrypt_api_key(encrypted)

    def test_get_encryption_service_singleton(self, mock_master_key):
        """Test singleton pattern for get_encryption_service."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": mock_master_key}):
            service1 = get_encryption_service()
            service2 = get_encryption_service()

            # Should be the same instance
            assert service1 is service2

    def test_unicode_api_keys(self, encryption_service):
        """Test encryption of API keys with unicode characters."""
        api_key = "sk-test-🔑-1234567890"
        encrypted, hint = encryption_service.encrypt_api_key(api_key)
        decrypted = encryption_service.decrypt_api_key(encrypted)

        assert decrypted == api_key
        assert hint == "...7890"

    def test_special_characters_in_key(self, encryption_service):
        """Test encryption of API keys with special characters."""
        api_key = "sk-test-!@#$%^&*()_+-=[]{}|;:,.<>?"
        encrypted, hint = encryption_service.encrypt_api_key(api_key)
        decrypted = encryption_service.decrypt_api_key(encrypted)

        assert decrypted == api_key

    def test_concurrent_encryption(self, mock_master_key):
        """Test concurrent encryption operations don't interfere."""
        import threading

        service = EncryptionService(master_key=mock_master_key)
        results = []
        errors = []

        def encrypt_key(key_id):
            try:
                api_key = f"sk-test-concurrent-{key_id}"
                encrypted, hint = service.encrypt_api_key(api_key)
                decrypted = service.decrypt_api_key(encrypted)
                results.append((key_id, api_key == decrypted))
            except Exception as e:
                errors.append((key_id, str(e)))

        # Run 10 concurrent encryption operations
        threads = []
        for i in range(10):
            thread = threading.Thread(target=encrypt_key, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all operations succeeded
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 10
        assert all(success for _, success in results)

    def test_encryption_performance(self, encryption_service):
        """Test encryption performance for reasonable response times."""
        import time

        api_key = "sk-test-performance-1234567890abcdef"

        # Measure encryption time
        start_time = time.time()
        for _ in range(100):
            encrypted, hint = encryption_service.encrypt_api_key(api_key)
        encryption_time = time.time() - start_time

        # Should encrypt 100 keys in less than 1 second
        assert encryption_time < 1.0, f"Encryption too slow: {encryption_time}s for 100 operations"

        # Measure decryption time
        start_time = time.time()
        for _ in range(100):
            decrypted = encryption_service.decrypt_api_key(encrypted)
        decryption_time = time.time() - start_time

        # Should decrypt 100 keys in less than 1 second
        assert decryption_time < 1.0, f"Decryption too slow: {decryption_time}s for 100 operations"

    def test_key_rotation_with_multiple_keys(self, mock_master_key):
        """Test key rotation with multiple encrypted values."""
        old_service = EncryptionService(master_key=mock_master_key)
        new_master_key = EncryptionService.generate_master_key()

        # Encrypt multiple API keys with old master key
        api_keys = [
            "sk-test-rotation-1",
            "sk-test-rotation-2",
            "sk-test-rotation-3"
        ]

        old_encrypted_keys = []
        for api_key in api_keys:
            encrypted, _ = old_service.encrypt_api_key(api_key)
            old_encrypted_keys.append(encrypted)

        # Rotate all keys to new master key
        new_encrypted_keys = []
        for encrypted in old_encrypted_keys:
            new_encrypted = old_service.rotate_key(encrypted, new_master_key)
            new_encrypted_keys.append(new_encrypted)

        # Verify all keys can be decrypted with new master key
        new_service = EncryptionService(master_key=new_master_key)
        for i, new_encrypted in enumerate(new_encrypted_keys):
            decrypted = new_service.decrypt_api_key(new_encrypted)
            assert decrypted == api_keys[i]

    def test_tampering_detection(self, encryption_service):
        """Test that tampering with encrypted data is detected."""
        api_key = "sk-test-tampering-detection"
        encrypted, _ = encryption_service.encrypt_api_key(api_key)

        # Tamper with the encrypted data
        tampered = encrypted[:-1] + ("a" if encrypted[-1] != "a" else "b")

        # Should raise an error when trying to decrypt tampered data
        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            encryption_service.decrypt_api_key(tampered)

    def test_empty_and_whitespace_handling(self, encryption_service):
        """Test handling of edge case inputs."""
        # Test whitespace-only key
        with pytest.raises(ValueError, match="API key cannot be empty"):
            encryption_service.encrypt_api_key("   ")

        # Test key with leading/trailing whitespace
        api_key = "  sk-test-whitespace-key  "
        encrypted, hint = encryption_service.encrypt_api_key(api_key)
        decrypted = encryption_service.decrypt_api_key(encrypted)

        # Should preserve whitespace
        assert decrypted == api_key
        assert hint == "...y  "  # Last 4 chars including spaces
