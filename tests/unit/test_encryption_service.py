"""Tests for the encryption service."""

import base64
import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from app.services.encryption_service import EncryptionService, get_encryption_service


class TestEncryptionService:
    """Test the encryption service."""

    @pytest.fixture
    def master_key(self):
        """Generate a test master key."""
        return Fernet.generate_key().decode()

    @pytest.fixture
    def service(self, master_key):
        """Create an encryption service instance."""
        return EncryptionService(master_key)

    def test_init_with_master_key(self, master_key):
        """Test initialization with provided master key."""
        service = EncryptionService(master_key)
        assert service._cipher_suite is not None

    def test_init_with_env_var(self, master_key):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": master_key}):
            service = EncryptionService()
            assert service._cipher_suite is not None

    def test_init_no_key_raises_error(self):
        """Test initialization without key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="ENCRYPTION_KEY environment variable must be set"
            ):
                EncryptionService()

    def test_encrypt_api_key_basic(self, service):
        """Test basic API key encryption."""
        api_key = "sk-test-1234567890abcdef"
        encrypted, hint = service.encrypt_api_key(api_key)

        assert encrypted != api_key
        assert hint == "...cdef"
        assert len(encrypted) > 0

    def test_encrypt_api_key_short(self, service):
        """Test encrypting short API key."""
        api_key = "abc"
        encrypted, hint = service.encrypt_api_key(api_key)

        assert encrypted != api_key
        assert hint == "****"

    def test_encrypt_api_key_empty_raises_error(self, service):
        """Test encrypting empty API key raises error."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            service.encrypt_api_key("")

    def test_decrypt_api_key_basic(self, service):
        """Test basic API key decryption."""
        original = "sk-test-1234567890abcdef"
        encrypted, _ = service.encrypt_api_key(original)

        decrypted = service.decrypt_api_key(encrypted)
        assert decrypted == original

    def test_decrypt_api_key_empty_raises_error(self, service):
        """Test decrypting empty key raises error."""
        with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
            service.decrypt_api_key("")

    def test_decrypt_api_key_invalid_raises_error(self, service):
        """Test decrypting invalid key raises error."""
        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            service.decrypt_api_key("invalid-encrypted-data")

    def test_encrypt_decrypt_round_trip(self, service):
        """Test full encryption/decryption round trip."""
        test_keys = [
            "sk-test-1234567890abcdef",
            "sk-proj_abcdefghijklmnopqrstuvwxyz",
            "anthropic-key-12345",
            "a",  # Single character
            "あいうえお",  # Unicode characters
        ]

        for original in test_keys:
            encrypted, hint = service.encrypt_api_key(original)
            decrypted = service.decrypt_api_key(encrypted)
            assert decrypted == original

    def test_encryption_is_non_deterministic(self, service):
        """Test that encryption produces different outputs for same input."""
        api_key = "sk-test-1234567890abcdef"

        encrypted1, _ = service.encrypt_api_key(api_key)
        encrypted2, _ = service.encrypt_api_key(api_key)

        # Encrypted values should be different due to Fernet's timestamp/nonce
        assert encrypted1 != encrypted2

        # But both should decrypt to the same value
        assert service.decrypt_api_key(encrypted1) == api_key
        assert service.decrypt_api_key(encrypted2) == api_key

    def test_generate_master_key(self):
        """Test master key generation."""
        key1 = EncryptionService.generate_master_key()
        key2 = EncryptionService.generate_master_key()

        # Keys should be different
        assert key1 != key2

        # Keys should be valid base64
        try:
            base64.urlsafe_b64decode(key1)
            base64.urlsafe_b64decode(key2)
        except Exception:
            pytest.fail("Generated keys are not valid base64")

        # Keys should work for encryption
        service = EncryptionService(key1)
        encrypted, _ = service.encrypt_api_key("test")
        assert service.decrypt_api_key(encrypted) == "test"

    def test_rotate_key(self, service, master_key):
        """Test key rotation."""
        # Encrypt with original key
        api_key = "sk-test-1234567890abcdef"
        encrypted_old, _ = service.encrypt_api_key(api_key)

        # Generate new master key
        new_master_key = EncryptionService.generate_master_key()

        # Rotate to new key
        encrypted_new = service.rotate_key(encrypted_old, new_master_key)

        # Verify old encrypted value still works with old service
        assert service.decrypt_api_key(encrypted_old) == api_key

        # Verify new encrypted value works with new service
        new_service = EncryptionService(new_master_key)
        assert new_service.decrypt_api_key(encrypted_new) == api_key

        # Verify old service cannot decrypt new encrypted value
        with pytest.raises(ValueError, match="Failed to decrypt"):
            service.decrypt_api_key(encrypted_new)

    def test_create_cipher_deterministic(self, master_key):
        """Test that cipher creation is deterministic for same master key."""
        service1 = EncryptionService(master_key)
        service2 = EncryptionService(master_key)

        # Encrypt with first service
        api_key = "test-key"
        encrypted, _ = service1.encrypt_api_key(api_key)

        # Second service should be able to decrypt
        decrypted = service2.decrypt_api_key(encrypted)
        assert decrypted == api_key

    def test_get_encryption_service_singleton(self, master_key):
        """Test that get_encryption_service returns singleton."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": master_key}):
            # Clear any existing instance
            import app.services.encryption_service

            app.services.encryption_service._encryption_service = None

            service1 = get_encryption_service()
            service2 = get_encryption_service()

            assert service1 is service2

    def test_get_encryption_service_creates_instance(self, master_key):
        """Test that get_encryption_service creates instance when needed."""
        with patch.dict(os.environ, {"ENCRYPTION_KEY": master_key}):
            # Clear any existing instance
            import app.services.encryption_service

            app.services.encryption_service._encryption_service = None

            service = get_encryption_service()
            assert isinstance(service, EncryptionService)

    def test_hint_generation(self, service):
        """Test API key hint generation."""
        test_cases = [
            ("sk-test-1234", "...1234"),
            ("abc", "****"),
            ("abcd", "...abcd"),
            ("12345", "...2345"),
            ("x", "****"),
            ("", None),  # Should raise before hint generation
        ]

        for api_key, expected_hint in test_cases:
            if expected_hint is None:
                with pytest.raises(ValueError):
                    service.encrypt_api_key(api_key)
            else:
                _, hint = service.encrypt_api_key(api_key)
                assert hint == expected_hint

    def test_encryption_with_special_characters(self, service):
        """Test encryption with special characters."""
        special_keys = [
            "key-with-spaces test",
            "key@with#special$chars%",
            "key\nwith\nnewlines",
            "key\twith\ttabs",
            "emoji-key-🔑-🔐",
        ]

        for original in special_keys:
            encrypted, _ = service.encrypt_api_key(original)
            decrypted = service.decrypt_api_key(encrypted)
            assert decrypted == original

    def test_large_api_key(self, service):
        """Test encryption with large API key."""
        # Create a large API key (1MB)
        large_key = "sk-" + "x" * (1024 * 1024)

        encrypted, hint = service.encrypt_api_key(large_key)
        decrypted = service.decrypt_api_key(encrypted)

        assert decrypted == large_key
        assert hint == "...xxxx"

    def test_decrypt_corrupted_data(self, service):
        """Test decrypting corrupted data."""
        api_key = "sk-test-1234567890abcdef"
        encrypted, _ = service.encrypt_api_key(api_key)

        # Corrupt the encrypted data
        encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
        corrupted_bytes = encrypted_bytes[:-5] + b"xxxxx"
        corrupted = base64.urlsafe_b64encode(corrupted_bytes).decode()

        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            service.decrypt_api_key(corrupted)

    def test_decrypt_with_wrong_key(self):
        """Test decrypting with wrong master key."""
        key1 = EncryptionService.generate_master_key()
        key2 = EncryptionService.generate_master_key()

        service1 = EncryptionService(key1)
        service2 = EncryptionService(key2)

        # Encrypt with first service
        encrypted, _ = service1.encrypt_api_key("test-key")

        # Try to decrypt with second service (different key)
        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            service2.decrypt_api_key(encrypted)
