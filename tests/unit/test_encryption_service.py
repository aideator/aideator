"""
Comprehensive tests for the encryption service.
"""

import os
import pytest
from unittest.mock import patch
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