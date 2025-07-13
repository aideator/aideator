"""Tests for the provider key service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.provider_keys import (
    CreateProviderKeyRequest,
    ProviderKeyResponse,
    UpdateProviderKeyRequest,
)
from app.core.logging import get_logger
from app.models.provider_key import ProviderAPIKeyAuditLog, ProviderAPIKeyDB
from app.models.user import User
from app.services.provider_key_service import ProviderKeyService


class TestProviderKeyService:
    """Test the provider key service."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = "user_123"
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_encryption_service(self):
        """Create a mock encryption service."""
        service = Mock()
        service.encrypt_api_key.return_value = "encrypted_key"
        service.decrypt_api_key.return_value = "decrypted_key"
        service.get_key_hint.return_value = "sk-...xyz"
        return service

    @pytest.fixture
    def service(self, mock_db_session, mock_encryption_service):
        """Create a provider key service instance."""
        with patch(
            "app.services.provider_key_service.get_encryption_service"
        ) as mock_get_enc:
            mock_get_enc.return_value = mock_encryption_service
            service = ProviderKeyService(db=mock_db_session)
            service.encryption = mock_encryption_service
            return service

    @pytest.mark.asyncio
    async def test_create_provider_key_internal(
        self, service, mock_user, mock_db_session
    ):
        """Test creating a provider key internally."""
        # Arrange
        mock_db_session.execute = AsyncMock()
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Mock the _get_active_key method to return None (no existing key)
        with patch.object(service, "_get_active_key", new=AsyncMock(return_value=None)):
            # Mock encryption response
            service.encryption.encrypt_api_key.return_value = (
                "encrypted_key",
                "sk-...123",
            )

            # Act
            result = await service.create_provider_key_internal(
                session=mock_db_session,
                user=mock_user,
                provider="openai",
                api_key="sk-test-123",
                name="My OpenAI Key",
                model_name="gpt-4",
                metadata={"test": "data"},
            )

            # Assert
            assert result.provider == "openai"
            assert result.name == "My OpenAI Key"
            mock_db_session.add.assert_called()
            # Note: internal method doesn't commit - session manager handles it
            mock_db_session.commit.assert_not_called()
            service.encryption.encrypt_api_key.assert_called_once_with("sk-test-123")

    @pytest.mark.asyncio
    async def test_create_provider_key(self, service, mock_user, mock_db_session):
        """Test creating a provider key through the public API."""
        # Arrange
        request = CreateProviderKeyRequest(
            provider="anthropic",
            api_key="sk-ant-test-456",
            name="My Anthropic Key",
            model_name="claude-3-opus",
        )

        # Mock the internal method and set up the service with a DB session
        service.db = mock_db_session

        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = "provkey_123"
        mock_key.provider = "anthropic"
        mock_key.name = "My Anthropic Key"
        mock_key.model_name = "claude-3-opus"
        mock_key.is_active = True
        mock_key.created_at = datetime.utcnow()
        mock_key.updated_at = datetime.utcnow()
        mock_key.key_hint = "sk-ant-...456"

        # Mock the database get method to return the user
        mock_db_session.get = Mock(return_value=mock_user)

        with patch.object(service, "create_provider_key_internal") as mock_create:
            mock_create.return_value = mock_key

            # Act - use the API compatibility method signature
            result = await service.create_provider_key(
                user_id=mock_user.id,
                provider_type=request.provider,
                name=request.name,
                api_key=request.api_key,
                model_name=request.model_name,
            )

            # Assert
            assert result.id == "provkey_123"
            assert result.provider == "anthropic"
            assert result.name == "My Anthropic Key"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_provider_key(self, service, mock_user, mock_db_session):
        """Test getting a provider key by ID."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.provider = "openai"
        mock_key.is_active = True

        # Set up service with db session and mock get method to return the key
        service.db = mock_db_session
        mock_db_session.get = Mock(return_value=mock_key)

        # Act
        result = await service.get_provider_key(key_id)

        # Assert
        assert result == mock_key
        mock_db_session.get.assert_called_once_with(ProviderAPIKeyDB, key_id)

    @pytest.mark.asyncio
    async def test_get_provider_key_not_found(
        self, service, mock_user, mock_db_session
    ):
        """Test getting a non-existent provider key."""
        # Arrange
        service.db = mock_db_session
        mock_db_session.get = Mock(return_value=None)

        # Act
        result = await service.get_provider_key("nonexistent")

        # Assert
        assert result is None
        mock_db_session.get.assert_called_once_with(ProviderAPIKeyDB, "nonexistent")

    @pytest.mark.asyncio
    async def test_list_provider_keys(self, service, mock_user, mock_db_session):
        """Test listing provider keys for a user."""
        # Arrange
        mock_keys = [
            Mock(spec=ProviderAPIKeyDB, id="key1", provider="openai"),
            Mock(spec=ProviderAPIKeyDB, id="key2", provider="anthropic"),
        ]

        # Set up service with db session and mock get method to return the user
        service.db = mock_db_session
        mock_db_session.get = Mock(return_value=mock_user)

        # Mock the execute method for list_user_keys
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        mock_db_session.execute.return_value = mock_result

        # Act - use the API compatibility method
        result = await service.get_user_provider_keys(mock_user.id)

        # Assert
        assert len(result) == 2
        assert result == mock_keys
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_provider_key(self, service, mock_user):
        """Test updating a provider key."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.name = "Old Name"
        mock_key.is_active = True

        update_request = UpdateProviderKeyRequest(
            name="New Name",
            is_active=False,
        )

        # Create a non-async mock session for the sync calls in API compatibility method
        mock_sync_session = Mock()
        service.db = mock_sync_session

        # Create separate mocks for different get calls
        def mock_get_side_effect(model_class, id_value):
            if model_class == ProviderAPIKeyDB:
                return mock_key
            if id_value == mock_user.id:
                return mock_user
            return None

        mock_sync_session.get = Mock(side_effect=mock_get_side_effect)
        mock_sync_session.commit = Mock()
        mock_sync_session.refresh = Mock()
        mock_sync_session.add = Mock()

        # Mock the _create_audit_log method
        with patch.object(service, "_create_audit_log", new=AsyncMock()):
            # Act - use the API compatibility method
            result = await service.update_provider_key(
                credential_id=key_id,
                name=update_request.name,
            )

            # Assert
            assert result.name == "New Name"
            # Note: service doesn't commit - session manager handles it
            mock_sync_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_provider_key(self, service, mock_user):
        """Test deleting a provider key."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.provider = "openai"
        mock_key.model_name = None

        # Create a non-async mock session for the sync calls in API compatibility method
        mock_sync_session = Mock()
        service.db = mock_sync_session

        # Create separate mocks for different get calls
        def mock_get_side_effect(model_class, id_value):
            if model_class == ProviderAPIKeyDB:
                return mock_key
            if id_value == mock_user.id:
                return mock_user
            return None

        mock_sync_session.get = Mock(side_effect=mock_get_side_effect)
        mock_sync_session.commit = Mock()
        mock_sync_session.add = Mock()

        # Mock the _create_audit_log method
        with patch.object(service, "_create_audit_log", new=AsyncMock()):
            # Act - use the API compatibility method
            result = await service.delete_provider_key(key_id)

            # Assert
            assert result is True
            assert mock_key.is_active is False
            # Note: service doesn't commit - session manager handles it
            mock_sync_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_key_for_model(self, service, mock_user, mock_db_session):
        """Test getting API key for a specific model."""
        # Arrange
        model_specific_key = Mock(spec=ProviderAPIKeyDB)
        model_specific_key.id = "key_123"
        model_specific_key.encrypted_key = "model_encrypted_key"
        model_specific_key.is_active = True
        model_specific_key.last_used_at = datetime.utcnow()
        model_specific_key.total_requests = 5

        # Mock _get_active_key to return the model specific key
        with patch.object(service, "_get_active_key") as mock_get_key:
            mock_get_key.return_value = model_specific_key
            mock_db_session.add = Mock()
            mock_db_session.commit = AsyncMock()

            # Act
            result = await service.get_key_for_model(
                mock_db_session, mock_user, "gpt-4"
            )

            # Assert
            assert result == model_specific_key
            assert model_specific_key.total_requests == 6
            # Note: service doesn't commit - session manager handles it
            mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_provider_key(self, service, mock_user, mock_db_session):
        """Test validating a provider key by ID."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.encrypted_key = "encrypted_test_key"

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()

        # Mock encryption service to return valid key
        service.encryption.decrypt_api_key.return_value = "sk-test-1234567890"

        # Act
        result = await service.validate_provider_key(mock_db_session, mock_user, key_id)

        # Assert
        assert result is True
        assert mock_key.is_valid is True
        # Note: service doesn't commit - session manager handles it
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_provider_key_invalid_short(
        self, service, mock_user, mock_db_session
    ):
        """Test validating a provider key that is too short."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.encrypted_key = "encrypted_test_key"

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()

        # Mock encryption service to return short key
        service.encryption.decrypt_api_key.return_value = "short"

        with patch.object(service, "_create_audit_log", new=AsyncMock()):
            # Act
            result = await service.validate_provider_key(
                mock_db_session, mock_user, key_id
            )

            # Assert
            assert result is False
            assert mock_key.is_valid is False
            assert mock_key.last_error == "Key appears to be too short"
            # Note: service doesn't commit - session manager handles it
            mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_provider_key_decryption_error(
        self, service, mock_user, mock_db_session
    ):
        """Test validating a provider key with decryption error."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.encrypted_key = "encrypted_test_key"

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()

        # Mock encryption service to raise error
        service.encryption.decrypt_api_key.side_effect = Exception("Decryption failed")

        # Act
        result = await service.validate_provider_key(mock_db_session, mock_user, key_id)

        # Assert
        assert result is False
        assert mock_key.is_valid is False
        assert mock_key.last_error == "Decryption failed"
        # Note: service doesn't commit - session manager handles it
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_provider_key_not_found(
        self, service, mock_user, mock_db_session
    ):
        """Test validating a non-existent provider key."""
        # Arrange
        mock_db_session.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.validate_provider_key(
                mock_db_session, mock_user, "nonexistent"
            )

        assert exc_info.value.status_code == 404
        assert "Provider key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_provider_key_wrong_user(
        self, service, mock_user, mock_db_session
    ):
        """Test validating a provider key that belongs to different user."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = "different_user_id"

        mock_db_session.get = AsyncMock(return_value=mock_key)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.validate_provider_key(mock_db_session, mock_user, key_id)

        assert exc_info.value.status_code == 404
        assert "Provider key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_key_for_model_fallback(
        self, service, mock_user, mock_db_session
    ):
        """Test getting API key for model with fallback to provider-level key."""
        # Arrange
        provider_key = Mock(spec=ProviderAPIKeyDB)
        provider_key.id = "key_123"
        provider_key.encrypted_key = "provider_encrypted_key"
        provider_key.is_active = True
        provider_key.last_used_at = datetime.utcnow()
        provider_key.total_requests = 10

        # Mock _get_active_key to return None for model-specific, then provider key
        def mock_get_active_key_side_effect(session, user_id, provider, model_name):
            if model_name is None:  # provider-level key
                return provider_key
            return None  # no model-specific key

        with patch.object(
            service, "_get_active_key", side_effect=mock_get_active_key_side_effect
        ):
            with patch.object(service, "_create_audit_log", new=AsyncMock()):
                mock_db_session.add = Mock()
                mock_db_session.commit = AsyncMock()

                # Act
                result = await service.get_key_for_model(
                    mock_db_session, mock_user, "gpt-4"
                )

                # Assert
                assert result == provider_key
                assert provider_key.total_requests == 11
                # Note: service doesn't commit - session manager handles it
                mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_key_for_model_not_found(
        self, service, mock_user, mock_db_session
    ):
        """Test getting API key for model when no key exists."""
        # Mock _get_active_key to return None for both calls
        with patch.object(service, "_get_active_key", return_value=None):
            # Act
            result = await service.get_key_for_model(
                mock_db_session, mock_user, "gpt-4"
            )

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_track_usage(self, service, mock_db_session):
        """Test tracking usage for a provider key."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.total_tokens = 100
        mock_key.total_cost = 0.05
        mock_key.total_requests = 5

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()

        # Act
        await service.track_usage(mock_db_session, key_id, 50, 0.01)

        # Assert
        assert mock_key.total_tokens == 150
        assert (
            abs(mock_key.total_cost - 0.06) < 0.001
        )  # Handle floating point precision
        assert mock_key.total_requests == 6
        assert mock_key.last_used_at is not None
        # Note: service doesn't commit - session manager handles it
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_track_usage_key_not_found(self, service, mock_db_session):
        """Test tracking usage for non-existent key."""
        # Arrange
        mock_db_session.get = AsyncMock(return_value=None)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()

        # Act (should not raise exception)
        await service.track_usage(mock_db_session, "nonexistent", 50, 0.01)

        # Assert
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_decrypt_api_key(self, service, mock_user, mock_db_session):
        """Test decrypting an API key."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.encrypted_key = "encrypted_test_key"

        mock_db_session.get = AsyncMock(return_value=mock_key)
        service.encryption.decrypt_api_key.return_value = "sk-decrypted-key"

        # Act
        result = await service.decrypt_api_key(mock_db_session, mock_user, key_id)

        # Assert
        assert result == "sk-decrypted-key"
        service.encryption.decrypt_api_key.assert_called_once_with("encrypted_test_key")

    @pytest.mark.asyncio
    async def test_decrypt_api_key_not_found(self, service, mock_user, mock_db_session):
        """Test decrypting non-existent API key."""
        # Arrange
        mock_db_session.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.decrypt_api_key(mock_db_session, mock_user, "nonexistent")

        assert exc_info.value.status_code == 404
        assert "Provider key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_decrypt_api_key_wrong_user(
        self, service, mock_user, mock_db_session
    ):
        """Test decrypting API key that belongs to different user."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = "different_user_id"

        mock_db_session.get = AsyncMock(return_value=mock_key)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.decrypt_api_key(mock_db_session, mock_user, key_id)

        assert exc_info.value.status_code == 404
        assert "Provider key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_provider_key_for_user(self, service, mock_user, mock_db_session):
        """Test getting provider key for specific user."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id

        mock_db_session.get = AsyncMock(return_value=mock_key)

        # Act
        result = await service.get_provider_key_for_user(
            mock_db_session, mock_user, key_id
        )

        # Assert
        assert result == mock_key

    @pytest.mark.asyncio
    async def test_get_provider_key_for_user_not_found(
        self, service, mock_user, mock_db_session
    ):
        """Test getting non-existent provider key for user."""
        # Arrange
        mock_db_session.get = AsyncMock(return_value=None)

        # Act
        result = await service.get_provider_key_for_user(
            mock_db_session, mock_user, "nonexistent"
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_provider_key_for_user_wrong_user(
        self, service, mock_user, mock_db_session
    ):
        """Test getting provider key that belongs to different user."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = "different_user_id"

        mock_db_session.get = AsyncMock(return_value=mock_key)

        # Act
        result = await service.get_provider_key_for_user(
            mock_db_session, mock_user, key_id
        )

        # Assert
        assert result is None

    def test_infer_provider_from_model_openai(self, service):
        """Test inferring OpenAI provider from model names."""
        test_cases = [
            "gpt-4",
            "gpt-3.5-turbo",
            "text-davinci-003",
            "dall-e-2",
            "whisper-1",
            "tts-1",
        ]

        for model in test_cases:
            result = service._infer_provider_from_model(model)
            assert result == "openai", f"Failed for model: {model}"

    def test_infer_provider_from_model_anthropic(self, service):
        """Test inferring Anthropic provider from model names."""
        test_cases = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-2.1",
            "claude-instant-1.2",
        ]

        for model in test_cases:
            result = service._infer_provider_from_model(model)
            assert result == "anthropic", f"Failed for model: {model}"

    def test_infer_provider_from_model_google(self, service):
        """Test inferring Google provider from model names."""
        test_cases = ["gemini-pro", "palm-2", "text-bison-001", "chat-bison"]

        for model in test_cases:
            result = service._infer_provider_from_model(model)
            assert result == "google", f"Failed for model: {model}"

    def test_infer_provider_from_model_other_providers(self, service):
        """Test inferring other providers from model names."""
        test_cases = [
            ("cohere-command", "cohere"),
            ("groq-llama2-70b", "groq"),
            ("mistral-7b", "mistral"),
            ("perplexity-llama-2", "perplexity"),
            ("deepseek-chat", "deepseek"),
            ("grok-1", "xai"),
            ("fireworks-llama-v2", "fireworks"),
            ("together-llama-2", "together"),
            ("bedrock-claude", "anthropic"),  # claude pattern matches first
            ("azure-gpt-4", "openai"),  # gpt pattern matches first
            ("ollama-llama2", "ollama"),
            ("huggingface-bert", "huggingface"),
        ]

        for model, expected_provider in test_cases:
            result = service._infer_provider_from_model(model)
            assert result == expected_provider, f"Failed for model: {model}"

    def test_infer_provider_from_model_unknown_defaults_to_openai(self, service):
        """Test that unknown model names default to OpenAI."""
        unknown_models = ["unknown-model", "custom-llm", "some-random-name"]

        for model in unknown_models:
            result = service._infer_provider_from_model(model)
            assert result == "openai", f"Failed for model: {model}"

    @pytest.mark.asyncio
    async def test_list_user_keys_sync_session(self, service, mock_user):
        """Test listing user keys with sync session."""
        # Arrange
        mock_sync_session = Mock()
        mock_keys = [Mock(spec=ProviderAPIKeyDB), Mock(spec=ProviderAPIKeyDB)]

        # For sync sessions, the exec result is directly iterable
        mock_sync_session.exec.return_value = iter(mock_keys)

        # Act
        result = await service.list_user_keys(mock_sync_session, mock_user)

        # Assert
        assert result == mock_keys
        mock_sync_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_user_keys_with_provider_filter(
        self, service, mock_user, mock_db_session
    ):
        """Test listing user keys with provider filter."""
        # Arrange
        mock_keys = [Mock(spec=ProviderAPIKeyDB)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await service.list_user_keys(
            mock_db_session, mock_user, provider="openai"
        )

        # Assert
        assert result == mock_keys
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_user_keys_include_inactive(
        self, service, mock_user, mock_db_session
    ):
        """Test listing user keys including inactive ones."""
        # Arrange
        mock_keys = [Mock(spec=ProviderAPIKeyDB), Mock(spec=ProviderAPIKeyDB)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await service.list_user_keys(
            mock_db_session, mock_user, include_inactive=True
        )

        # Assert
        assert result == mock_keys
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_provider_key_internal_async_session(
        self, service, mock_user, mock_db_session
    ):
        """Test updating provider key with async session."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.name = "Old Name"
        mock_key.is_active = True

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with patch.object(service, "_create_audit_log", new=AsyncMock()):
            # Act
            result = await service.update_provider_key_internal(
                session=mock_db_session,
                user=mock_user,
                key_id=key_id,
                name="New Name",
                is_active=False,
            )

            # Assert
            assert result.name == "New Name"
            assert result.is_active is False
            # Note: internal method doesn't commit - session manager handles it
            mock_db_session.commit.assert_not_called()
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_provider_key_internal_with_api_key(
        self, service, mock_user, mock_db_session
    ):
        """Test updating provider key with new API key."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        service.encryption.encrypt_api_key.return_value = ("new_encrypted", "new_hint")

        with patch.object(service, "_create_audit_log", new=AsyncMock()):
            # Act
            result = await service.update_provider_key_internal(
                session=mock_db_session,
                user=mock_user,
                key_id=key_id,
                api_key="new-api-key",
            )

            # Assert
            assert result.encrypted_key == "new_encrypted"
            assert result.key_hint == "new_hint"
            service.encryption.encrypt_api_key.assert_called_once_with("new-api-key")

    @pytest.mark.asyncio
    async def test_update_provider_key_internal_not_found(
        self, service, mock_user, mock_db_session
    ):
        """Test updating non-existent provider key."""
        # Arrange
        mock_db_session.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.update_provider_key_internal(
                session=mock_db_session,
                user=mock_user,
                key_id="nonexistent",
                name="New Name",
            )

        assert exc_info.value.status_code == 404
        assert "Provider key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_provider_key_internal_async_session(
        self, service, mock_user, mock_db_session
    ):
        """Test deleting provider key with async session."""
        # Arrange
        key_id = "provkey_123"
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_key.id = key_id
        mock_key.user_id = mock_user.id
        mock_key.provider = "openai"
        mock_key.model_name = None

        mock_db_session.get = AsyncMock(return_value=mock_key)
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()

        with patch.object(service, "_create_audit_log", new=AsyncMock()):
            # Act
            result = await service.delete_provider_key_internal(
                session=mock_db_session, user=mock_user, key_id=key_id
            )

            # Assert
            assert result is True
            assert mock_key.is_active is False
            # Note: internal method doesn't commit - session manager handles it
            mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_provider_key_internal_not_found(
        self, service, mock_user, mock_db_session
    ):
        """Test deleting non-existent provider key."""
        # Arrange
        mock_db_session.get = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_provider_key_internal(
                session=mock_db_session, user=mock_user, key_id="nonexistent"
            )

        assert exc_info.value.status_code == 404
        assert "Provider key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_active_key_async_session(
        self, service, mock_user, mock_db_session
    ):
        """Test _get_active_key with async session."""
        # Arrange
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_key
        mock_db_session.execute.return_value = mock_result

        # Act
        result = await service._get_active_key(
            mock_db_session, mock_user.id, "openai", "gpt-4"
        )

        # Assert
        assert result == mock_key
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_key_sync_session(self, service, mock_user):
        """Test _get_active_key with sync session."""
        # Arrange
        mock_sync_session = Mock()
        mock_key = Mock(spec=ProviderAPIKeyDB)
        mock_result = Mock()
        mock_result.first.return_value = mock_key
        mock_sync_session.exec.return_value = mock_result

        # Act
        result = await service._get_active_key(
            mock_sync_session, mock_user.id, "openai", None
        )

        # Assert
        assert result == mock_key
        mock_sync_session.exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_audit_log(self, service, mock_user, mock_db_session):
        """Test creating audit log entry."""
        # Arrange
        mock_db_session.add = Mock()

        # Act
        await service._create_audit_log(
            session=mock_db_session,
            user_id=mock_user.id,
            provider_key_id="provkey_123",
            action="created",
            details={"test": "data"},
        )

        # Assert
        mock_db_session.add.assert_called_once()
        added_log = mock_db_session.add.call_args[0][0]
        assert isinstance(added_log, ProviderAPIKeyAuditLog)
        assert added_log.user_id == mock_user.id
        assert added_log.provider_key_id == "provkey_123"
        assert added_log.action == "created"
        assert added_log.details == {"test": "data"}
