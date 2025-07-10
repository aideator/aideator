"""
Comprehensive API tests for provider key endpoints.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import User


class TestProviderKeyAPI:
    """Test suite for provider key API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        return User(
            id="user_test123",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            full_name="Test User",
        )

    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for authentication."""
        return "aid_sk_test123456789"

    @pytest.fixture
    def auth_headers(self, mock_api_key):
        """Headers with API key authentication."""
        return {"X-API-Key": mock_api_key}

    @pytest.fixture
    def sample_provider_key(self, mock_user):
        """Sample provider key for testing."""
        return ProviderAPIKeyDB(
            id="provkey_test123",
            user_id=mock_user.id,
            provider="openai",
            encrypted_key="encrypted_test_key",
            key_hint="...cdef",
            name="Test OpenAI Key",
            is_active=True,
            total_requests=42,
            created_at="2025-01-10T14:00:00Z"
        )

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_create_provider_key_success(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test successful provider key creation."""
        # Mock authentication
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            # Mock service response
            created_key = ProviderAPIKeyDB(
                id="provkey_new123",
                user_id=mock_user.id,
                provider="openai",
                encrypted_key="encrypted_new_key",
                key_hint="...abcd",
                name="My OpenAI Key",
                is_active=True,
                total_requests=0,
                created_at="2025-01-10T14:00:00Z"
            )
            mock_service.create_provider_key.return_value = created_key

            # Make request
            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={
                    "provider": "openai",
                    "api_key": "sk-test-1234567890abcd",
                    "name": "My OpenAI Key"
                }
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "provkey_new123"
            assert data["provider"] == "openai"
            assert data["name"] == "My OpenAI Key"
            assert data["key_hint"] == "...abcd"
            assert data["is_active"] == True

            # Verify service was called correctly
            mock_service.create_provider_key.assert_called_once()
            call_args = mock_service.create_provider_key.call_args
            assert call_args[1]["provider"] == "openai"
            assert call_args[1]["api_key"] == "sk-test-1234567890abcd"
            assert call_args[1]["name"] == "My OpenAI Key"

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    def test_create_provider_key_invalid_provider(self, mock_session, client, auth_headers, mock_user):
        """Test provider key creation with invalid provider."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={
                    "provider": "invalid_provider",
                    "api_key": "sk-test-1234567890abcd",
                    "name": "Invalid Provider Key"
                }
            )

            assert response.status_code == 422  # Validation error
            assert "Provider must be one of:" in str(response.json())

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_list_provider_keys(self, mock_service, mock_session, client, auth_headers, mock_user, sample_provider_key):
        """Test listing user's provider keys."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            # Mock service response
            mock_service.list_user_keys.return_value = [sample_provider_key]

            response = client.get("/api/v1/provider-keys/", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "provkey_test123"
            assert data[0]["provider"] == "openai"
            assert data[0]["name"] == "Test OpenAI Key"

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_list_provider_keys_with_filters(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test listing provider keys with filters."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            mock_service.list_user_keys.return_value = []

            response = client.get(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                params={"provider": "openai", "include_inactive": "true"}
            )

            assert response.status_code == 200

            # Verify service was called with correct filters
            mock_service.list_user_keys.assert_called_once()
            call_args = mock_service.list_user_keys.call_args
            assert call_args[1]["provider"] == "openai"
            assert call_args[1]["include_inactive"] == True

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_get_provider_key(self, mock_service, mock_session, client, auth_headers, mock_user, sample_provider_key):
        """Test getting a specific provider key."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            mock_service.list_user_keys.return_value = [sample_provider_key]

            response = client.get(
                "/api/v1/provider-keys/provkey_test123",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "provkey_test123"
            assert data["provider"] == "openai"

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_get_provider_key_not_found(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test getting non-existent provider key."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            mock_service.list_user_keys.return_value = []

            response = client.get(
                "/api/v1/provider-keys/nonexistent",
                headers=auth_headers
            )

            assert response.status_code == 404

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_update_provider_key(self, mock_service, mock_session, client, auth_headers, mock_user, sample_provider_key):
        """Test updating a provider key."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            # Mock updated key
            updated_key = sample_provider_key.copy()
            updated_key.name = "Updated OpenAI Key"
            updated_key.is_active = False
            mock_service.update_provider_key.return_value = updated_key

            response = client.put(
                "/api/v1/provider-keys/provkey_test123",
                headers=auth_headers,
                json={
                    "name": "Updated OpenAI Key",
                    "is_active": False
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated OpenAI Key"
            assert data["is_active"] == False

            # Verify service was called correctly
            mock_service.update_provider_key.assert_called_once()
            call_args = mock_service.update_provider_key.call_args
            assert call_args[1]["key_id"] == "provkey_test123"
            assert call_args[1]["name"] == "Updated OpenAI Key"
            assert call_args[1]["is_active"] == False

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_delete_provider_key(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test deleting a provider key."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            mock_service.delete_provider_key.return_value = True

            response = client.delete(
                "/api/v1/provider-keys/provkey_test123",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "deleted" in data["message"]

            # Verify service was called correctly
            mock_service.delete_provider_key.assert_called_once()
            call_args = mock_service.delete_provider_key.call_args
            assert call_args[1]["key_id"] == "provkey_test123"

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_validate_provider_key(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test validating a provider key."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            mock_service.validate_provider_key.return_value = True

            response = client.post(
                "/api/v1/provider-keys/provkey_test123/validate",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["is_valid"] == True
            assert "valid" in data["message"]

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_validate_provider_key_invalid(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test validating an invalid provider key."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            mock_service.validate_provider_key.return_value = False

            response = client.post(
                "/api/v1/provider-keys/provkey_test123/validate",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["is_valid"] == False
            assert "failed" in data["message"]

    def test_list_supported_providers(self, client):
        """Test getting list of supported providers."""
        response = client.get("/api/v1/provider-keys/providers/list")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data

        providers = data["providers"]
        assert len(providers) > 0

        # Check OpenAI provider details
        openai_provider = next((p for p in providers if p["name"] == "openai"), None)
        assert openai_provider is not None
        assert openai_provider["display_name"] == "OpenAI"
        assert "gpt-4" in openai_provider["models"]
        assert openai_provider["requires_api_key"] == True
        assert "platform.openai.com" in openai_provider["documentation_url"]

    def test_unauthorized_access(self, client):
        """Test accessing endpoints without authentication."""
        # Test without API key
        response = client.get("/api/v1/provider-keys/")
        assert response.status_code == 401

        response = client.post("/api/v1/provider-keys/", json={
            "provider": "openai",
            "api_key": "sk-test"
        })
        assert response.status_code == 401

    def test_invalid_api_key(self, client):
        """Test accessing endpoints with invalid API key."""
        headers = {"X-API-Key": "invalid_key"}

        response = client.get("/api/v1/provider-keys/", headers=headers)
        assert response.status_code == 401

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_service_error_handling(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test handling of service errors."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            # Mock service to raise an exception
            mock_service.create_provider_key.side_effect = Exception("Database error")

            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={
                    "provider": "openai",
                    "api_key": "sk-test-1234567890abcd",
                    "name": "Test Key"
                }
            )

            assert response.status_code == 500

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    def test_missing_required_fields(self, mock_session, client, auth_headers, mock_user):
        """Test validation of required fields."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            # Missing provider
            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={"api_key": "sk-test-1234567890abcd"}
            )
            assert response.status_code == 422

            # Missing api_key
            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={"provider": "openai"}
            )
            assert response.status_code == 422

            # Empty api_key
            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={"provider": "openai", "api_key": ""}
            )
            assert response.status_code == 422

    @patch("app.api.v1.endpoints.provider_keys.get_session")
    @patch("app.api.v1.endpoints.provider_keys.provider_key_service")
    def test_model_specific_key_creation(self, mock_service, mock_session, client, auth_headers, mock_user):
        """Test creating model-specific provider keys."""
        with patch("app.core.dependencies.get_current_user", return_value=mock_user):
            created_key = ProviderAPIKeyDB(
                id="provkey_model123",
                user_id=mock_user.id,
                provider="openai",
                model_name="gpt-4",
                encrypted_key="encrypted_model_key",
                key_hint="...xyz",
                name="GPT-4 Specific Key",
                is_active=True,
                total_requests=0,
                created_at="2025-01-10T14:00:00Z"
            )
            mock_service.create_provider_key.return_value = created_key

            response = client.post(
                "/api/v1/provider-keys/",
                headers=auth_headers,
                json={
                    "provider": "openai",
                    "api_key": "sk-test-model-specific",
                    "name": "GPT-4 Specific Key",
                    "model_name": "gpt-4"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["model_name"] == "gpt-4"
            assert data["name"] == "GPT-4 Specific Key"
