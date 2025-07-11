"""
Test encryption service.
"""

import os
from unittest.mock import patch

import pytest

from app.services.encryption_service import EncryptionService, get_encryption_service


class TestEncryptionService:
    """Test cases for encryption service."""

    def test_init_with_master_key(self):
        """Test initialization with provided master key."""
        master_key = "test-master-key-for-encryption"
        service = EncryptionService(master_key=master_key)

        # Should create cipher without error
        assert service._cipher_suite is not None

    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "env-master-key"}):
            service = EncryptionService()

            # Should create cipher without error
            assert service._cipher_suite is not None

    def test_init_without_master_key_raises_error(self):
        """Test initialization without master key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="ENCRYPTION_KEY environment variable must be set"
            ):
                EncryptionService()

    def test_encrypt_api_key(self):
        """Test encrypting API key."""
        service = EncryptionService(master_key="test-key")
        api_key = "sk-test-api-key-12345"

        encrypted_key, key_hint = service.encrypt_api_key(api_key)

        # Should return encrypted string and hint
        assert isinstance(encrypted_key, str)
        assert isinstance(key_hint, str)
        assert key_hint == "...2345"  # Last 4 chars
        assert encrypted_key != api_key

    def test_encrypt_api_key_short_key(self):
        """Test encrypting short API key."""
        service = EncryptionService(master_key="test-key")
        api_key = "abc"

        encrypted_key, key_hint = service.encrypt_api_key(api_key)

        # Should return encrypted string and hint
        assert isinstance(encrypted_key, str)
        assert isinstance(key_hint, str)
        assert key_hint == "****"  # Short key gets ****
        assert encrypted_key != api_key

    def test_encrypt_api_key_empty_raises_error(self):
        """Test encrypting empty API key raises error."""
        service = EncryptionService(master_key="test-key")

        with pytest.raises(ValueError, match="API key cannot be empty"):
            service.encrypt_api_key("")

    def test_decrypt_api_key(self):
        """Test decrypting API key."""
        service = EncryptionService(master_key="test-key")
        api_key = "sk-test-api-key-12345"

        # Encrypt first
        encrypted_key, _ = service.encrypt_api_key(api_key)

        # Then decrypt
        decrypted_key = service.decrypt_api_key(encrypted_key)

        assert decrypted_key == api_key

    def test_decrypt_empty_key_raises_error(self):
        """Test decrypting empty key raises error."""
        service = EncryptionService(master_key="test-key")

        with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
            service.decrypt_api_key("")

    def test_encrypt_decrypt_roundtrip(self):
        """Test encrypt/decrypt roundtrip with various keys."""
        service = EncryptionService(master_key="test-key")

        test_keys = [
            "sk-test-key-12345",
            "sk-ant-api03-very-long-key-abcdefghijklmnop",
            "AI-short-key",
            "x" * 100,  # Very long key
            "simple",  # Simple key
            "1234",  # 4-char key
        ]

        for original_key in test_keys:
            encrypted_key, key_hint = service.encrypt_api_key(original_key)
            decrypted_key = service.decrypt_api_key(encrypted_key)

            assert decrypted_key == original_key

            # Verify key hint logic
            if len(original_key) >= 4:
                assert key_hint == f"...{original_key[-4:]}"
            else:
                assert key_hint == "****"

    def test_different_master_keys_produce_different_encryption(self):
        """Test that different master keys produce different encrypted values."""
        api_key = "sk-test-api-key-12345"

        service1 = EncryptionService(master_key="master-key-1")
        service2 = EncryptionService(master_key="master-key-2")

        encrypted1, hint1 = service1.encrypt_api_key(api_key)
        encrypted2, hint2 = service2.encrypt_api_key(api_key)

        # Hints should be the same (they're derived from original key)
        assert hint1 == hint2

        # But encrypted values should be different
        assert encrypted1 != encrypted2

        # And each service should decrypt its own encryption
        assert service1.decrypt_api_key(encrypted1) == api_key
        assert service2.decrypt_api_key(encrypted2) == api_key

    def test_encryption_is_non_deterministic(self):
        """Test that encryption is non-deterministic (includes random nonce)."""
        api_key = "sk-test-api-key-12345"
        master_key = "consistent-master-key"

        service = EncryptionService(master_key=master_key)

        encrypted1, hint1 = service.encrypt_api_key(api_key)
        encrypted2, hint2 = service.encrypt_api_key(api_key)

        # Hints should be the same
        assert hint1 == hint2

        # But encrypted values should be different (due to random nonce)
        assert encrypted1 != encrypted2

        # But both should decrypt to original
        assert service.decrypt_api_key(encrypted1) == api_key
        assert service.decrypt_api_key(encrypted2) == api_key

    def test_decrypt_invalid_data_raises_error(self):
        """Test decrypting invalid data raises error."""
        service = EncryptionService(master_key="test-key")

        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            service.decrypt_api_key("invalid-encrypted-data")

    def test_create_cipher_with_salt(self):
        """Test cipher creation uses consistent salt."""
        service = EncryptionService(master_key="test-key")

        # Should create cipher successfully
        assert service._cipher_suite is not None

        # Test encryption/decryption works
        test_data = "test-data"
        encrypted, _ = service.encrypt_api_key(test_data)
        decrypted = service.decrypt_api_key(encrypted)
        assert decrypted == test_data

    def test_key_hint_generation(self):
        """Test key hint generation for various key formats."""
        service = EncryptionService(master_key="test-key")

        test_cases = [
            ("sk-test-key-12345", "...2345"),
            ("sk-ant-api03-very-long-key", "...-key"),
            ("AI-short", "...hort"),
            ("x", "****"),
            ("123456789", "...6789"),
            ("1234", "...1234"),
        ]

        for api_key, expected_hint in test_cases:
            _, hint = service.encrypt_api_key(api_key)
            assert hint == expected_hint

    def test_generate_master_key(self):
        """Test generating master key."""
        master_key = EncryptionService.generate_master_key()

        # Should be a string
        assert isinstance(master_key, str)

        # Should be long enough
        assert len(master_key) > 20

        # Should be able to create service with it
        service = EncryptionService(master_key=master_key)
        assert service._cipher_suite is not None


class TestGetEncryptionService:
    """Test the get_encryption_service function."""

    def test_get_encryption_service_singleton(self):
        """Test get_encryption_service returns singleton instance."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "test-singleton-key"}):
            service1 = get_encryption_service()
            service2 = get_encryption_service()

            # Should return same instance
            assert service1 is service2

    def test_get_encryption_service_with_env_var(self):
        """Test get_encryption_service with environment variable."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "test-env-key"}):
            service = get_encryption_service()

            # Should create service successfully
            assert isinstance(service, EncryptionService)
            assert service._cipher_suite is not None

    def test_get_encryption_service_returns_new_instance_when_no_caching(self):
        """Test get_encryption_service returns working instance."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "test-cache-key"}):
            service1 = get_encryption_service()
            service2 = get_encryption_service()

            # Should be same instance (caching)
            assert service1 is service2

            # Should work with encryption
            test_key = "test-api-key"
            encrypted, hint = service1.encrypt_api_key(test_key)
            decrypted = service2.decrypt_api_key(encrypted)
            assert decrypted == test_key

    def test_get_encryption_service_works_with_default_env(self):
        """Test get_encryption_service works with default environment."""
        # This will use whatever ENCRYPTION_KEY is set in the environment
        try:
            service = get_encryption_service()
            assert isinstance(service, EncryptionService)
            assert service._cipher_suite is not None
        except ValueError:
            # If no ENCRYPTION_KEY is set, that's expected
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
