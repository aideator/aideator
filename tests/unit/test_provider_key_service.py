"""
Tests for the provider key service.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.provider_key_service import ProviderKeyService
from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import User


class TestProviderKeyService:
    """Test suite for ProviderKeyService."""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        return User(
            id="user_test123",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            full_name="Test User",
        )
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.exec = MagicMock()
        session.get = MagicMock()
        return session
    
    @pytest.fixture
    def provider_key_service(self):
        """Create provider key service with mocked encryption."""
        with patch('app.services.provider_key_service.get_encryption_service') as mock_encryption:
            mock_encryption.return_value.encrypt_api_key.return_value = ("encrypted_key", "...cdef")
            mock_encryption.return_value.decrypt_api_key.return_value = "sk-test-1234567890abcdef"
            service = ProviderKeyService()
            service.encryption = mock_encryption.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_create_provider_key(self, provider_key_service, mock_session, mock_user):
        """Test creating a new provider key."""
        # Mock no existing key
        mock_session.exec.return_value.first.return_value = None
        
        result = await provider_key_service.create_provider_key(
            session=mock_session,
            user=mock_user,
            provider="openai",
            api_key="sk-test-1234567890abcdef",
            name="My OpenAI Key",
        )
        
        # Verify encryption was called
        provider_key_service.encryption.encrypt_api_key.assert_called_once_with("sk-test-1234567890abcdef")
        
        # Verify database operations
        assert mock_session.add.call_count == 2  # Key + audit log
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        
        # Verify the key data
        key_call = mock_session.add.call_args_list[0][0][0]
        assert isinstance(key_call, ProviderAPIKeyDB)
        assert key_call.provider == "openai"
        assert key_call.name == "My OpenAI Key"
        assert key_call.encrypted_key == "encrypted_key"
        assert key_call.key_hint == "...cdef"
    
    @pytest.mark.asyncio
    async def test_create_provider_key_replaces_existing(self, provider_key_service, mock_session, mock_user):
        """Test creating provider key when one already exists."""
        # Mock existing key
        existing_key = ProviderAPIKeyDB(
            id="existing_key",
            user_id=mock_user.id,
            provider="openai",
            encrypted_key="old_encrypted",
            key_hint="...old",
            is_active=True,
        )
        mock_session.exec.return_value.first.return_value = existing_key
        
        await provider_key_service.create_provider_key(
            session=mock_session,
            user=mock_user,
            provider="openai",
            api_key="sk-test-new-key",
        )
        
        # Verify old key was deactivated
        assert existing_key.is_active == False
        assert existing_key.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_list_user_keys(self, provider_key_service, mock_session, mock_user):
        """Test listing user's provider keys."""
        # Mock query results
        mock_keys = [
            ProviderAPIKeyDB(id="key1", user_id=mock_user.id, provider="openai", encrypted_key="enc1", key_hint="...1"),
            ProviderAPIKeyDB(id="key2", user_id=mock_user.id, provider="anthropic", encrypted_key="enc2", key_hint="...2"),
        ]
        mock_session.exec.return_value = mock_keys
        
        result = await provider_key_service.list_user_keys(
            session=mock_session,
            user=mock_user,
        )
        
        assert len(result) == 2
        assert result[0].id == "key1"
        assert result[1].id == "key2"
    
    @pytest.mark.asyncio
    async def test_get_key_for_model_model_specific(self, provider_key_service, mock_session, mock_user):
        """Test getting model-specific key."""
        # Mock model-specific key exists
        model_key = ProviderAPIKeyDB(
            id="model_key",
            user_id=mock_user.id,
            provider="openai",
            model_name="gpt-4",
            encrypted_key="encrypted_model_key",
            key_hint="...model",
            is_active=True,
        )
        mock_session.exec.return_value.first.return_value = model_key
        
        result = await provider_key_service.get_key_for_model(
            session=mock_session,
            user=mock_user,
            provider="openai",
            model_name="gpt-4",
        )
        
        assert result == "sk-test-1234567890abcdef"
        provider_key_service.encryption.decrypt_api_key.assert_called_with("encrypted_model_key")
        
        # Verify usage tracking
        assert model_key.last_used_at is not None
        assert model_key.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_get_key_for_model_fallback_to_provider(self, provider_key_service, mock_session, mock_user):
        """Test fallback to provider-level key when model-specific doesn't exist."""
        # Mock no model-specific key, but provider key exists
        provider_key = ProviderAPIKeyDB(
            id="provider_key",
            user_id=mock_user.id,
            provider="openai",
            model_name=None,
            encrypted_key="encrypted_provider_key",
            key_hint="...provider",
            is_active=True,
        )
        
        # First call (model-specific) returns None, second call (provider) returns key
        mock_session.exec.return_value.first.side_effect = [None, provider_key]
        
        result = await provider_key_service.get_key_for_model(
            session=mock_session,
            user=mock_user,
            provider="openai",
            model_name="gpt-4",
        )
        
        assert result == "sk-test-1234567890abcdef"
        provider_key_service.encryption.decrypt_api_key.assert_called_with("encrypted_provider_key")
    
    @pytest.mark.asyncio
    async def test_get_key_for_model_not_found(self, provider_key_service, mock_session, mock_user):
        """Test getting key when none exists."""
        # Mock no keys exist
        mock_session.exec.return_value.first.return_value = None
        
        result = await provider_key_service.get_key_for_model(
            session=mock_session,
            user=mock_user,
            provider="openai",
            model_name="gpt-4",
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_provider_key(self, provider_key_service, mock_session, mock_user):
        """Test updating a provider key."""
        # Mock existing key
        existing_key = ProviderAPIKeyDB(
            id="test_key",
            user_id=mock_user.id,
            provider="openai",
            encrypted_key="old_encrypted",
            key_hint="...old",
            name="Old Name",
            is_active=True,
        )
        mock_session.get.return_value = existing_key
        
        result = await provider_key_service.update_provider_key(
            session=mock_session,
            user=mock_user,
            key_id="test_key",
            api_key="new-api-key",
            name="New Name",
            is_active=False,
        )
        
        # Verify updates
        assert existing_key.name == "New Name"
        assert existing_key.is_active == False
        assert existing_key.encrypted_key == "encrypted_key"
        assert existing_key.key_hint == "...cdef"
        assert existing_key.updated_at is not None
        
        # Verify encryption was called with new key
        provider_key_service.encryption.encrypt_api_key.assert_called_with("new-api-key")
    
    @pytest.mark.asyncio
    async def test_update_provider_key_not_found(self, provider_key_service, mock_session, mock_user):
        """Test updating non-existent key raises error."""
        mock_session.get.return_value = None
        
        with pytest.raises(Exception, match="Provider key not found"):
            await provider_key_service.update_provider_key(
                session=mock_session,
                user=mock_user,
                key_id="nonexistent",
                name="New Name",
            )
    
    @pytest.mark.asyncio
    async def test_delete_provider_key(self, provider_key_service, mock_session, mock_user):
        """Test deleting a provider key."""
        # Mock existing key
        existing_key = ProviderAPIKeyDB(
            id="test_key",
            user_id=mock_user.id,
            provider="openai",
            encrypted_key="encrypted",
            key_hint="...test",
            is_active=True,
        )
        mock_session.get.return_value = existing_key
        
        result = await provider_key_service.delete_provider_key(
            session=mock_session,
            user=mock_user,
            key_id="test_key",
        )
        
        assert result == True
        assert existing_key.is_active == False
        assert existing_key.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_validate_provider_key(self, provider_key_service, mock_session, mock_user):
        """Test validating a provider key."""
        # Mock existing key
        existing_key = ProviderAPIKeyDB(
            id="test_key",
            user_id=mock_user.id,
            provider="openai",
            encrypted_key="encrypted",
            key_hint="...test",
            is_active=True,
        )
        mock_session.get.return_value = existing_key
        
        result = await provider_key_service.validate_provider_key(
            session=mock_session,
            user=mock_user,
            key_id="test_key",
        )
        
        assert result == True
        assert existing_key.is_valid == True
        assert existing_key.last_validated_at is not None
        assert existing_key.last_error is None
    
    @pytest.mark.asyncio
    async def test_validate_provider_key_decryption_failure(self, provider_key_service, mock_session, mock_user):
        """Test validation when decryption fails."""
        # Mock existing key
        existing_key = ProviderAPIKeyDB(
            id="test_key",
            user_id=mock_user.id,
            provider="openai",
            encrypted_key="encrypted",
            key_hint="...test",
            is_active=True,
        )
        mock_session.get.return_value = existing_key
        
        # Mock decryption failure
        provider_key_service.encryption.decrypt_api_key.side_effect = Exception("Decryption failed")
        
        result = await provider_key_service.validate_provider_key(
            session=mock_session,
            user=mock_user,
            key_id="test_key",
        )
        
        assert result == False
        assert existing_key.is_valid == False
        assert existing_key.last_error == "Decryption failed"