"""
Unit Tests for Core Dependencies

This test suite covers the authentication dependencies
to increase test coverage for app/core/dependencies.py
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthError
from app.core.dependencies import (
    get_current_active_user,
    get_current_user,
    get_current_user_from_api_key,
    get_optional_current_user,
    security,
)
from app.models.user import User


@pytest.mark.asyncio
class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @patch("app.core.dependencies.authenticate_user")
    async def test_get_current_user_success(self, mock_authenticate):
        """Test successful user authentication."""
        # Mock user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=True
        )
        mock_authenticate.return_value = mock_user

        # Mock credentials and session
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await get_current_user(mock_credentials, mock_db)

        # Verify
        assert result is mock_user
        mock_authenticate.assert_called_once_with(mock_credentials, mock_db)

    @patch("app.core.dependencies.authenticate_user")
    async def test_get_current_user_auth_error(self, mock_authenticate):
        """Test authentication error handling."""
        # Mock authentication failure
        mock_authenticate.side_effect = AuthError("Invalid token")

        # Mock credentials and session
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
        mock_db = AsyncMock(spec=AsyncSession)

        # Should raise AuthError
        with pytest.raises(AuthError, match="Invalid token"):
            await get_current_user(mock_credentials, mock_db)


@pytest.mark.asyncio
class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""

    async def test_get_current_active_user_success(self):
        """Test with active user."""
        # Mock active user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=True
        )

        # Call the function
        result = await get_current_active_user(mock_user)

        # Should return the user
        assert result is mock_user

    async def test_get_current_active_user_inactive(self):
        """Test with inactive user."""
        # Mock inactive user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=False
        )

        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Inactive user"


@pytest.mark.asyncio
class TestGetCurrentUserFromAPIKey:
    """Test get_current_user_from_api_key dependency."""

    @patch("app.core.dependencies.get_user_from_api_key")
    async def test_api_key_from_header_success(self, mock_get_user):
        """Test successful authentication with API key from header."""
        # Mock user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=True
        )
        mock_get_user.return_value = mock_user

        # Mock session
        mock_db = AsyncMock(spec=AsyncSession)

        # Call with header API key
        result = await get_current_user_from_api_key(
            x_api_key="test-api-key",
            api_key=None,
            db=mock_db
        )

        # Verify
        assert result is mock_user
        mock_get_user.assert_called_once_with("test-api-key", mock_db)

    @patch("app.core.dependencies.get_user_from_api_key")
    async def test_api_key_from_query_success(self, mock_get_user):
        """Test successful authentication with API key from query parameter."""
        # Mock user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=True
        )
        mock_get_user.return_value = mock_user

        # Mock session
        mock_db = AsyncMock(spec=AsyncSession)

        # Call with query API key
        result = await get_current_user_from_api_key(
            x_api_key=None,
            api_key="test-api-key",
            db=mock_db
        )

        # Verify
        assert result is mock_user
        mock_get_user.assert_called_once_with("test-api-key", mock_db)

    @patch("app.core.dependencies.get_user_from_api_key")
    async def test_api_key_header_takes_precedence(self, mock_get_user):
        """Test that header API key takes precedence over query."""
        # Mock user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=True
        )
        mock_get_user.return_value = mock_user

        # Mock session
        mock_db = AsyncMock(spec=AsyncSession)

        # Call with both header and query API key
        result = await get_current_user_from_api_key(
            x_api_key="header-key",
            api_key="query-key",
            db=mock_db
        )

        # Should use header key
        assert result is mock_user
        mock_get_user.assert_called_once_with("header-key", mock_db)

    async def test_api_key_missing(self):
        """Test error when no API key provided."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Should raise 401 Unauthorized
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_api_key(
                x_api_key=None,
                api_key=None,
                db=mock_db
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "API key required"
        assert exc_info.value.headers == {"WWW-Authenticate": "API-Key"}

    @patch("app.core.dependencies.get_user_from_api_key")
    async def test_api_key_invalid(self, mock_get_user):
        """Test error when API key is invalid."""
        # Mock no user found
        mock_get_user.return_value = None

        mock_db = AsyncMock(spec=AsyncSession)

        # Should raise AuthError
        with pytest.raises(AuthError, match="Invalid API key"):
            await get_current_user_from_api_key(
                x_api_key="invalid-key",
                api_key=None,
                db=mock_db
            )

    @patch("app.core.dependencies.get_user_from_api_key")
    async def test_api_key_inactive_user(self, mock_get_user):
        """Test error when user is inactive."""
        # Mock inactive user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=False
        )
        mock_get_user.return_value = mock_user

        mock_db = AsyncMock(spec=AsyncSession)

        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_api_key(
                x_api_key="test-key",
                api_key=None,
                db=mock_db
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Inactive user"


@pytest.mark.asyncio
class TestGetOptionalCurrentUser:
    """Test get_optional_current_user dependency."""

    @patch("app.core.dependencies.authenticate_user")
    async def test_optional_user_with_valid_credentials(self, mock_authenticate):
        """Test with valid credentials returns user."""
        # Mock user
        mock_user = User(
            id="user_123",
            email="test@example.com",
            is_active=True
        )
        mock_authenticate.return_value = mock_user

        # Mock credentials and session
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await get_optional_current_user(mock_credentials, mock_db)

        # Should return the user
        assert result is mock_user
        mock_authenticate.assert_called_once_with(mock_credentials, mock_db)

    async def test_optional_user_without_credentials(self):
        """Test without credentials returns None."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Call with no credentials
        result = await get_optional_current_user(None, mock_db)

        # Should return None
        assert result is None

    @patch("app.core.dependencies.authenticate_user")
    async def test_optional_user_with_invalid_credentials(self, mock_authenticate):
        """Test with invalid credentials returns None."""
        # Mock authentication failure
        mock_authenticate.side_effect = AuthError("Invalid token")

        # Mock credentials and session
        mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid")
        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await get_optional_current_user(mock_credentials, mock_db)

        # Should return None (not raise error)
        assert result is None


class TestDependencyTypes:
    """Test dependency type aliases and configurations."""

    def test_security_object(self):
        """Test that security object is configured correctly."""
        from fastapi.security import HTTPBearer

        assert isinstance(security, HTTPBearer)

    def test_type_aliases(self):
        """Test that type aliases are defined."""
        from app.core.dependencies import (
            CurrentUser,
            CurrentUserAPIKey,
            OptionalCurrentUser,
        )

        # These should be defined (they're Annotated types)
        assert CurrentUser is not None
        assert CurrentUserAPIKey is not None
        assert OptionalCurrentUser is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
