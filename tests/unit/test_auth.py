"""
Unit Tests for Authentication utilities

This test suite covers the authentication functions
to increase test coverage for app/core/auth.py
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    AuthError,
    authenticate_user,
    get_password_hash,
    get_user_from_api_key,
    get_user_from_token,
    pwd_context,
    verify_password,
)
from app.models.user import APIKey, User


class TestAuthError:
    """Test custom AuthError exception."""

    def test_auth_error_defaults(self):
        """Test AuthError with default message."""
        error = AuthError()
        assert error.status_code == 401
        assert error.detail == "Authentication failed"
        assert error.headers == {"WWW-Authenticate": "Bearer"}

    def test_auth_error_custom_message(self):
        """Test AuthError with custom message."""
        error = AuthError("Custom error message")
        assert error.status_code == 401
        assert error.detail == "Custom error message"
        assert error.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
class TestGetUserFromToken:
    """Test get_user_from_token function."""

    @patch("app.core.auth.jwt.decode")
    async def test_valid_token_active_user(self, mock_decode):
        """Test with valid token and active user."""
        # Mock JWT decode
        mock_decode.return_value = {"sub": "user_123"}

        # Mock user
        mock_user = User(id="user_123", email="test@example.com", is_active=True)

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.get.return_value = mock_user

        # Call the function
        result = await get_user_from_token("valid_token", mock_db)

        # Verify
        assert result is mock_user
        mock_decode.assert_called_once()
        mock_db.get.assert_called_once_with(User, "user_123")

    @patch("app.core.auth.jwt.decode")
    async def test_valid_token_inactive_user(self, mock_decode):
        """Test with valid token but inactive user."""
        # Mock JWT decode
        mock_decode.return_value = {"sub": "user_123"}

        # Mock inactive user
        mock_user = User(id="user_123", email="test@example.com", is_active=False)

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.get.return_value = mock_user

        # Also mock execute for email lookup fallback
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        # Call the function
        result = await get_user_from_token("valid_token", mock_db)

        # Should return None for inactive user
        assert result is None

    @patch("app.core.auth.jwt.decode")
    async def test_valid_token_no_user(self, mock_decode):
        """Test with valid token but user not found."""
        # Mock JWT decode
        mock_decode.return_value = {"sub": "user_123"}

        # Mock database session - user not found
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.get.return_value = None

        # Also mock execute for email lookup fallback
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Call the function
        result = await get_user_from_token("valid_token", mock_db)

        # Should return None
        assert result is None

    @patch("app.core.auth.jwt.decode")
    async def test_token_missing_user_id(self, mock_decode):
        """Test with token missing user ID."""
        # Mock JWT decode without 'sub'
        mock_decode.return_value = {"exp": 12345}

        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await get_user_from_token("token_without_sub", mock_db)

        # Should return None
        assert result is None

    @patch("app.core.auth.jwt.decode")
    async def test_invalid_token(self, mock_decode):
        """Test with invalid JWT token."""
        # Mock JWT decode failure
        mock_decode.side_effect = JWTError("Invalid token")

        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await get_user_from_token("invalid_token", mock_db)

        # Should return None
        assert result is None


@pytest.mark.asyncio
class TestGetUserFromAPIKey:
    """Test get_user_from_api_key function."""

    async def test_invalid_key_format(self):
        """Test with API key not having correct prefix."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Call with invalid format
        result = await get_user_from_api_key("invalid_key", mock_db)

        # Should return None immediately
        assert result is None
        # Should not query database
        mock_db.execute.assert_not_called()

    @patch("app.core.auth.pwd_context.verify")
    async def test_valid_api_key_active_user(self, mock_verify):
        """Test with valid API key and active user."""
        # Mock password verification
        mock_verify.return_value = True

        # Mock user
        mock_user = User(id="user_123", email="test@example.com", is_active=True)

        # Mock API key
        mock_api_key = APIKey(
            id="key_123",
            user_id="user_123",
            key_hash="hashed_key",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=30),
            total_requests=5,
            last_used_at=datetime.utcnow() - timedelta(hours=1),
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_api_key]
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = mock_user

        # Call the function
        result = await get_user_from_api_key("aid_sk_test_key", mock_db)

        # Verify
        assert result is mock_user
        assert mock_api_key.total_requests == 6  # Incremented
        assert mock_api_key.last_used_at > datetime.utcnow() - timedelta(seconds=5)
        mock_db.commit.assert_called_once()

    @patch("app.core.auth.pwd_context.verify")
    async def test_expired_api_key(self, mock_verify):
        """Test with expired API key."""
        # Mock password verification
        mock_verify.return_value = True

        # Mock expired API key
        mock_api_key = APIKey(
            id="key_123",
            user_id="user_123",
            key_hash="hashed_key",
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
            total_requests=5,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_api_key]
        mock_db.execute.return_value = mock_result

        # Call the function
        result = await get_user_from_api_key("aid_sk_test_key", mock_db)

        # Should return None for expired key
        assert result is None

    @patch("app.core.auth.pwd_context.verify")
    async def test_api_key_no_expiry(self, mock_verify):
        """Test with API key that has no expiry date."""
        # Mock password verification
        mock_verify.return_value = True

        # Mock user
        mock_user = User(id="user_123", email="test@example.com", is_active=True)

        # Mock API key without expiry
        mock_api_key = APIKey(
            id="key_123",
            user_id="user_123",
            key_hash="hashed_key",
            is_active=True,
            expires_at=None,  # No expiry
            total_requests=0,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_api_key]
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = mock_user

        # Call the function
        result = await get_user_from_api_key("aid_sk_test_key", mock_db)

        # Should work without expiry
        assert result is mock_user

    @patch("app.core.auth.pwd_context.verify")
    async def test_api_key_inactive_user(self, mock_verify):
        """Test with valid API key but inactive user."""
        # Mock password verification
        mock_verify.return_value = True

        # Mock inactive user
        mock_user = User(id="user_123", email="test@example.com", is_active=False)

        # Mock API key
        mock_api_key = APIKey(
            id="key_123",
            user_id="user_123",
            key_hash="hashed_key",
            is_active=True,
            expires_at=None,
            total_requests=0,
        )

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_api_key]
        mock_db.execute.return_value = mock_result
        mock_db.get.return_value = mock_user

        # Call the function
        result = await get_user_from_api_key("aid_sk_test_key", mock_db)

        # Should return None for inactive user
        assert result is None

    @patch("app.core.auth.pwd_context.verify")
    async def test_api_key_not_found(self, mock_verify):
        """Test with API key not matching any stored keys."""
        # Mock password verification to always return False
        mock_verify.return_value = False

        # Mock API keys
        mock_api_keys = [
            APIKey(id="key_1", key_hash="hash_1", is_active=True),
            APIKey(id="key_2", key_hash="hash_2", is_active=True),
        ]

        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_api_keys
        mock_db.execute.return_value = mock_result

        # Call the function
        result = await get_user_from_api_key("aid_sk_test_key", mock_db)

        # Should return None
        assert result is None
        # Should have tried to verify against both keys
        assert mock_verify.call_count == 2


@pytest.mark.asyncio
class TestAuthenticateUser:
    """Test authenticate_user function."""

    @patch("app.core.auth.get_user_from_token")
    async def test_authenticate_with_jwt_token(self, mock_get_token):
        """Test authentication with JWT token."""
        # Mock user from token
        mock_user = User(id="user_123", email="test@example.com")
        mock_get_token.return_value = mock_user

        # Mock credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="jwt_token"
        )

        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await authenticate_user(credentials, mock_db)

        # Should return user from token
        assert result is mock_user
        mock_get_token.assert_called_once_with("jwt_token", mock_db)

    @patch("app.core.auth.get_user_from_token")
    @patch("app.core.auth.get_user_from_api_key")
    async def test_authenticate_with_api_key(self, mock_get_api_key, mock_get_token):
        """Test authentication with API key."""
        # Mock no user from token
        mock_get_token.return_value = None

        # Mock user from API key
        mock_user = User(id="user_123", email="test@example.com")
        mock_get_api_key.return_value = mock_user

        # Mock credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="aid_sk_test_key"
        )

        mock_db = AsyncMock(spec=AsyncSession)

        # Call the function
        result = await authenticate_user(credentials, mock_db)

        # Should return user from API key
        assert result is mock_user
        mock_get_token.assert_called_once_with("aid_sk_test_key", mock_db)
        mock_get_api_key.assert_called_once_with("aid_sk_test_key", mock_db)

    @patch("app.core.auth.get_user_from_token")
    @patch("app.core.auth.get_user_from_api_key")
    async def test_authenticate_invalid_credentials(
        self, mock_get_api_key, mock_get_token
    ):
        """Test authentication with invalid credentials."""
        # Mock no user from either method
        mock_get_token.return_value = None
        mock_get_api_key.return_value = None

        # Mock credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_credentials"
        )

        mock_db = AsyncMock(spec=AsyncSession)

        # Should raise AuthError
        with pytest.raises(AuthError) as exc_info:
            await authenticate_user(credentials, mock_db)

        exc = exc_info.value
        assert isinstance(exc, AuthError)
        assert exc.detail == "Invalid credentials"


class TestPasswordFunctions:
    """Test password hashing and verification."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "test_password_123"

        # Hash the password
        hashed = get_password_hash(password)

        # Verify it's hashed (not plain text)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long

        # Verify it can be verified
        assert pwd_context.verify(password, hashed)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "correct_password"
        hashed = pwd_context.hash(password)

        # Should return True for correct password
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        hashed = pwd_context.hash(password)

        # Should return False for incorrect password
        assert verify_password("wrong_password", hashed) is False

    def test_password_hash_unique(self):
        """Test that same password produces different hashes."""
        password = "test_password"

        # Hash same password twice
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
