"""
Unit Tests for Auth API endpoints

This test suite covers the authentication endpoints
to increase test coverage for app/api/v1/auth.py
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import create_access_token, generate_api_key, router
from app.models.user import APIKey, User


class MockSettings:
    """Mock settings for testing."""
    secret_key = "test-secret-key-for-testing-purposes-only"
    algorithm = "HS256"
    access_token_expire_minutes = 30


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def app():
    """Create FastAPI app with auth router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/auth")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = User(
        id="user-123",
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$hashed_password_here",
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return user


class TestAuthUtilities:
    """Test authentication utility functions."""

    @patch("app.api.v1.auth.settings", MockSettings())
    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "user-123"}
        expires = timedelta(hours=1)

        token = create_access_token(data, expires)

        # Decode token to verify
        decoded = jwt.decode(token, MockSettings().secret_key, algorithms=[MockSettings().algorithm])
        assert decoded["sub"] == "user-123"
        assert "exp" in decoded

    @patch("app.api.v1.auth.settings", MockSettings())
    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry."""
        data = {"sub": "user-456"}

        token = create_access_token(data)

        # Decode token to verify
        decoded = jwt.decode(token, MockSettings().secret_key, algorithms=[MockSettings().algorithm])
        assert decoded["sub"] == "user-456"
        assert "exp" in decoded

    def test_generate_api_key(self):
        """Test API key generation."""
        key = generate_api_key()

        assert key.startswith("aid_sk_")
        assert len(key) > 40  # Prefix + 32 character token

        # Generate multiple keys to ensure uniqueness
        keys = [generate_api_key() for _ in range(10)]
        assert len(set(keys)) == 10  # All unique


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @patch("app.api.v1.auth.get_session")
    @patch("app.api.v1.auth.get_password_hash")
    @pytest.mark.asyncio
    async def test_register_success(self, mock_hash_password, mock_get_session, client):
        """Test successful user registration."""
        # Mock password hashing
        mock_hash_password.return_value = "hashed_password"

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # User doesn't exist
        mock_session.execute.return_value = mock_result
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_get_session.return_value = mock_session

        # Register user
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data

        # Verify database operations
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("app.api.v1.auth.get_session")
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_get_session, client):
        """Test registration with duplicate email."""
        # Mock database session - user already exists
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # User exists
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value = mock_session

        # Try to register with existing email
        user_data = {
            "email": "existing@example.com",
            "username": "newuser",
            "password": "SecurePass123!"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @patch("app.api.v1.auth.get_session")
    @patch("app.api.v1.auth.verify_password")
    @patch("app.api.v1.auth.create_access_token")
    @patch("app.api.v1.auth.settings", MockSettings())
    @pytest.mark.asyncio
    async def test_login_success(self, mock_create_token, mock_verify_pass, mock_get_session, client, mock_user):
        """Test successful login."""
        # Mock password verification
        mock_verify_pass.return_value = True

        # Mock token creation
        mock_create_token.return_value = "test_token_123"

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value = mock_session

        # Login
        login_data = {
            "email": "test@example.com",
            "password": "correctpassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "test_token_123"
        assert data["token_type"] == "bearer"

        # Verify token creation
        mock_create_token.assert_called_once()

    @patch("app.api.v1.auth.get_session")
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_get_session, client):
        """Test login with non-existent user."""
        # Mock database session - user not found
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value = mock_session

        # Try to login
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @patch("app.api.v1.auth.get_session")
    @patch("app.api.v1.auth.verify_password")
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_verify_pass, mock_get_session, client, mock_user):
        """Test login with wrong password."""
        # Mock password verification failure
        mock_verify_pass.return_value = False

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value = mock_session

        # Try to login
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @patch("app.api.v1.auth.get_session")
    @patch("app.api.v1.auth.get_password_hash")
    @patch("app.api.v1.auth.generate_api_key")
    @pytest.mark.asyncio
    async def test_create_api_key_success(self, mock_gen_key, mock_hash, mock_get_session, client, mock_user):
        """Test successful API key creation."""
        # Mock key generation and hashing
        mock_gen_key.return_value = "aid_sk_test_key_123"
        mock_hash.return_value = "hashed_key"

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user
        app = client.app
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Create API key
        key_data = {
            "name": "Test Key",
            "description": "Key for testing",
            "expires_in_days": 30
        }

        response = client.post("/api/v1/auth/api-keys", json=key_data)

        assert response.status_code == 201
        data = response.json()
        assert data["key"] == "aid_sk_test_key_123"
        assert data["api_key"]["name"] == "Test Key"
        assert data["api_key"]["description"] == "Key for testing"
        assert "expires_at" in data["api_key"]

        # Verify database operations
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("app.api.v1.auth.get_session")
    @pytest.mark.asyncio
    async def test_list_api_keys(self, mock_get_session, client, mock_user):
        """Test listing user's API keys."""
        # Create mock API keys
        mock_keys = [
            APIKey(
                id="key1",
                user_id=mock_user.id,
                name="Key 1",
                key_hash="hash1",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            APIKey(
                id="key2",
                user_id=mock_user.id,
                name="Key 2",
                key_hash="hash2",
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_keys
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user
        app = client.app
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # List API keys
        response = client.get("/api/v1/auth/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Key 1"
        assert data[1]["name"] == "Key 2"

    @patch("app.api.v1.auth.get_session")
    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, mock_get_session, client, mock_user):
        """Test successful API key revocation."""
        # Create mock API key
        mock_key = APIKey(
            id="key123",
            user_id=mock_user.id,
            name="Test Key",
            key_hash="hash123",
            is_active=True
        )

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = mock_key
        mock_session.commit = AsyncMock()

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user
        app = client.app
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Revoke API key
        response = client.delete("/api/v1/auth/api-keys/key123")

        assert response.status_code == 200
        assert response.json()["message"] == "API key revoked successfully"
        assert mock_key.is_active is False
        mock_session.commit.assert_called_once()

    @patch("app.api.v1.auth.get_session")
    @pytest.mark.asyncio
    async def test_revoke_api_key_not_found(self, mock_get_session, client, mock_user):
        """Test revoking non-existent API key."""
        # Mock database session - key not found
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = None

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user
        app = client.app
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Try to revoke non-existent key
        response = client.delete("/api/v1/auth/api-keys/nonexistent")

        assert response.status_code == 404
        assert "API key not found" in response.json()["detail"]

    @patch("app.api.v1.auth.get_session")
    @pytest.mark.asyncio
    async def test_revoke_api_key_wrong_user(self, mock_get_session, client, mock_user):
        """Test revoking API key belonging to another user."""
        # Create mock API key for different user
        mock_key = APIKey(
            id="key123",
            user_id="other-user-id",
            name="Other User Key",
            key_hash="hash123",
            is_active=True
        )

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = mock_key

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user
        app = client.app
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Try to revoke another user's key
        response = client.delete("/api/v1/auth/api-keys/key123")

        assert response.status_code == 404
        assert "API key not found" in response.json()["detail"]

    def test_auth_routes_registered(self, app):
        """Test that auth routes are properly registered."""
        routes = [route.path for route in app.routes]
        assert "/api/v1/auth/register" in routes
        assert "/api/v1/auth/login" in routes
        assert "/api/v1/auth/api-keys" in routes
        assert "/api/v1/auth/api-keys/{key_id}" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
