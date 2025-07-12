"""Tests for the auth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import User
from app.services.auth_service import AuthService, auth_service


class TestAuthService:
    """Test the auth service."""

    @pytest.fixture
    def service(self):
        """Create an auth service instance."""
        return AuthService()

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = "test-user-123"
        user.email = "test@example.com"
        user.username = "testuser"
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_validate_api_key_valid(self, service, mock_user):
        """Test validating a valid API key."""
        with patch(
            "app.services.auth_service.async_session_maker"
        ) as mock_session_maker:
            with patch(
                "app.services.auth_service.get_user_from_api_key"
            ) as mock_get_user:
                # Setup mocks
                mock_session = AsyncMock()
                mock_session_maker.return_value.__aenter__.return_value = mock_session
                mock_get_user.return_value = mock_user

                # Call service
                result = await service.validate_api_key("valid-api-key")

                # Verify
                assert result == mock_user
                mock_get_user.assert_called_once_with("valid-api-key", mock_session)

    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, service):
        """Test validating an invalid API key."""
        with patch(
            "app.services.auth_service.async_session_maker"
        ) as mock_session_maker:
            with patch(
                "app.services.auth_service.get_user_from_api_key"
            ) as mock_get_user:
                # Setup mocks
                mock_session = AsyncMock()
                mock_session_maker.return_value.__aenter__.return_value = mock_session
                mock_get_user.return_value = None

                # Call service
                result = await service.validate_api_key("invalid-api-key")

                # Verify
                assert result is None
                mock_get_user.assert_called_once_with("invalid-api-key", mock_session)

    @pytest.mark.asyncio
    async def test_validate_api_key_with_exception(self, service):
        """Test validate_api_key when exception occurs."""
        with patch(
            "app.services.auth_service.async_session_maker"
        ) as mock_session_maker:
            with patch(
                "app.services.auth_service.get_user_from_api_key"
            ) as mock_get_user:
                # Setup mocks
                mock_session = AsyncMock()
                mock_session_maker.return_value.__aenter__.return_value = mock_session
                mock_get_user.side_effect = Exception("Database error")

                # Call service - should propagate exception
                with pytest.raises(Exception, match="Database error"):
                    await service.validate_api_key("test-api-key")

    def test_global_instance_exists(self):
        """Test that the global auth service instance exists."""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)

    @pytest.mark.asyncio
    async def test_session_context_manager(self, service, mock_user):
        """Test that session context manager is properly used."""
        mock_session_maker = MagicMock()
        mock_session = AsyncMock()
        mock_context_manager = AsyncMock()

        # Setup context manager
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_session_maker.return_value = mock_context_manager

        with patch("app.services.auth_service.async_session_maker", mock_session_maker):
            with patch(
                "app.services.auth_service.get_user_from_api_key"
            ) as mock_get_user:
                mock_get_user.return_value = mock_user

                # Call service
                result = await service.validate_api_key("test-key")

                # Verify context manager was used
                mock_context_manager.__aenter__.assert_called_once()
                mock_context_manager.__aexit__.assert_called_once()
                assert result == mock_user
