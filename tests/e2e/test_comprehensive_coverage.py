"""
Comprehensive E2E Tests for AIdeator Backend API

This test suite aims to achieve 80% test coverage by systematically testing
all major API endpoints and workflows in the AIdeator backend.

Test Categories:
1. System Health & Root Endpoints
2. Authentication & User Management  
3. API Key Management
4. Run Management & Creation
5. Streaming Functionality
6. Session Management
7. Preference Analytics
8. Model Catalog & Provider Management
9. Error Handling & Edge Cases
"""

import asyncio
import json
import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

import httpx
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.e2e
class TestSystemEndpoints:
    """Test system health and root endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API information."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "AIdeator"

    @pytest.mark.asyncio
    async def test_health_check_basic(self, client: AsyncClient):
        """Test basic health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["orchestration"] == "kubernetes"

    @pytest.mark.asyncio
    async def test_health_check_detailed(self, client: AsyncClient):
        """Test detailed health check endpoint."""
        response = await client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data


@pytest.mark.e2e
class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    @pytest.mark.asyncio
    async def test_user_registration_flow(self, client: AsyncClient):
        """Test user registration with various inputs."""
        # Test valid registration
        registration_data = {
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "company": "Test Company"
        }
        
        response = await client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201
        user_data = response.json()
        assert "id" in user_data
        assert user_data["email"] == registration_data["email"]
        assert user_data["full_name"] == registration_data["full_name"]
        assert "password" not in user_data  # Password should not be returned

    @pytest.mark.asyncio
    async def test_user_registration_validation(self, client: AsyncClient):
        """Test user registration input validation."""
        # Test invalid email
        invalid_email_data = {
            "email": "not-an-email",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        response = await client.post("/api/v1/auth/register", json=invalid_email_data)
        assert response.status_code == 422

        # Test weak password
        weak_password_data = {
            "email": "test2@example.com",
            "password": "123",
            "full_name": "Test User"
        }
        response = await client.post("/api/v1/auth/register", json=weak_password_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_flow(self, client: AsyncClient):
        """Test user login with email and password."""
        # First register a user
        registration_data = {
            "email": "logintest@example.com",
            "password": "LoginPassword123!",
            "full_name": "Login Test User"
        }
        await client.post("/api/v1/auth/register", json=registration_data)
        
        # Test valid login
        login_data = {
            "email": "logintest@example.com",
            "password": "LoginPassword123!"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_validation(self, client: AsyncClient):
        """Test login validation and error handling."""
        # Test invalid credentials
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        response = await client.post("/api/v1/auth/login", json=invalid_login)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient):
        """Test getting current user information."""
        # Register and login user
        registration_data = {
            "email": "currentuser@example.com",
            "password": "CurrentPassword123!",
            "full_name": "Current User"
        }
        await client.post("/api/v1/auth/register", json=registration_data)
        
        login_data = {
            "email": "currentuser@example.com",
            "password": "CurrentPassword123!"
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Test getting current user
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "currentuser@example.com"
        assert user_data["full_name"] == "Current User"

    @pytest.mark.asyncio
    async def test_dev_test_login(self, client: AsyncClient):
        """Test development test login endpoint."""
        response = await client.get("/api/v1/auth/dev/test-login")
        # Should either work (in dev mode) or be disabled (in prod mode)
        assert response.status_code in [200, 404, 405]


@pytest.mark.e2e
class TestAPIKeyManagement:
    """Test API key creation and management."""

    @pytest.mark.asyncio
    async def test_create_api_key(self, client: AsyncClient):
        """Test API key creation."""
        # Setup user and get token
        user_data = {
            "email": "apikey@example.com",
            "password": "APIKeyPassword123!",
            "full_name": "API Key User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "apikey@example.com",
            "password": "APIKeyPassword123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test API key creation
        api_key_data = {
            "name": "Test API Key",
            "description": "API key for testing",
            "scopes": ["runs:create", "runs:read"],
            "expires_in_days": 90
        }
        response = await client.post("/api/v1/auth/api-keys", json=api_key_data, headers=headers)
        assert response.status_code == 201
        key_response = response.json()
        assert "api_key" in key_response
        assert "key_info" in key_response
        assert key_response["key_info"]["name"] == api_key_data["name"]

    @pytest.mark.asyncio
    async def test_list_api_keys(self, client: AsyncClient):
        """Test listing user's API keys."""
        # Setup user with API keys
        user_data = {
            "email": "listkeys@example.com",
            "password": "ListKeysPassword123!",
            "full_name": "List Keys User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "listkeys@example.com",
            "password": "ListKeysPassword123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create multiple API keys
        for i in range(3):
            api_key_data = {
                "name": f"Test Key {i+1}",
                "scopes": ["runs:create", "runs:read"]
            }
            await client.post("/api/v1/auth/api-keys", json=api_key_data, headers=headers)
        
        # Test listing keys
        response = await client.get("/api/v1/auth/api-keys", headers=headers)
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) >= 3

    @pytest.mark.asyncio
    async def test_delete_api_key(self, client: AsyncClient):
        """Test deleting an API key."""
        # Setup user and create API key
        user_data = {
            "email": "deletekey@example.com",
            "password": "DeleteKeyPassword123!",
            "full_name": "Delete Key User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "deletekey@example.com",
            "password": "DeleteKeyPassword123!"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create API key
        api_key_data = {"name": "Key to Delete", "scopes": ["runs:read"]}
        create_response = await client.post("/api/v1/auth/api-keys", json=api_key_data, headers=headers)
        key_id = create_response.json()["key_info"]["id"]
        
        # Delete API key
        delete_response = await client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=headers)
        assert delete_response.status_code == 204
        
        # Verify key is deleted
        list_response = await client.get("/api/v1/auth/api-keys", headers=headers)
        remaining_keys = list_response.json()
        assert not any(k["id"] == key_id for k in remaining_keys)


@pytest.mark.e2e
class TestRunManagement:
    """Test run creation and management."""

    async def _setup_user_with_api_key(self, client: AsyncClient) -> str:
        """Helper to setup user and return API key."""
        user_data = {
            "email": f"runuser_{asyncio.get_event_loop().time()}@example.com",
            "password": "RunUserPassword123!",
            "full_name": "Run User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        api_key_data = {"name": "Test Run Key", "scopes": ["runs:create", "runs:read"]}
        key_response = await client.post("/api/v1/auth/api-keys", json=api_key_data, 
                                       headers={"Authorization": f"Bearer {token}"})
        return key_response.json()["api_key"]

    @pytest.mark.asyncio
    async def test_create_run(self, client: AsyncClient):
        """Test creating a new run."""
        api_key = await self._setup_user_with_api_key(client)
        headers = {"X-API-Key": api_key}
        
        run_data = {
            "github_url": "https://github.com/fastapi/fastapi",
            "prompt": "Analyze the main.py file and suggest improvements",
            "variations": 2,
            "agent_config": {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }
        
        response = await client.post("/api/v1/runs", json=run_data, headers=headers)
        assert response.status_code == 202
        run_response = response.json()
        assert "run_id" in run_response
        assert "stream_url" in run_response
        assert run_response["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_create_run_validation(self, client: AsyncClient):
        """Test run creation validation."""
        api_key = await self._setup_user_with_api_key(client)
        headers = {"X-API-Key": api_key}
        
        # Test invalid GitHub URL
        invalid_run_data = {
            "github_url": "not-a-url",
            "prompt": "Test prompt",
            "variations": 1
        }
        response = await client.post("/api/v1/runs", json=invalid_run_data, headers=headers)
        assert response.status_code == 422

        # Test invalid variations count
        invalid_variations_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt",
            "variations": 0
        }
        response = await client.post("/api/v1/runs", json=invalid_variations_data, headers=headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_run_details(self, client: AsyncClient):
        """Test getting run details."""
        api_key = await self._setup_user_with_api_key(client)
        headers = {"X-API-Key": api_key}
        
        # Create a run
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for details",
            "variations": 1
        }
        create_response = await client.post("/api/v1/runs", json=run_data, headers=headers)
        run_id = create_response.json()["run_id"]
        
        # Get run details
        response = await client.get(f"/api/v1/runs/{run_id}", headers=headers)
        assert response.status_code == 200
        run_details = response.json()
        assert run_details["id"] == run_id
        assert run_details["github_url"] == run_data["github_url"]
        assert run_details["prompt"] == run_data["prompt"]

    @pytest.mark.asyncio
    async def test_list_runs(self, client: AsyncClient):
        """Test listing user's runs."""
        api_key = await self._setup_user_with_api_key(client)
        headers = {"X-API-Key": api_key}
        
        # Create multiple runs
        run_ids = []
        for i in range(3):
            run_data = {
                "github_url": "https://github.com/test/repo",
                "prompt": f"Test prompt {i+1}",
                "variations": 1
            }
            create_response = await client.post("/api/v1/runs", json=run_data, headers=headers)
            run_ids.append(create_response.json()["run_id"])
        
        # List runs
        response = await client.get("/api/v1/runs", headers=headers)
        assert response.status_code == 200
        runs_data = response.json()
        assert "items" in runs_data
        assert "total" in runs_data
        assert len(runs_data["items"]) >= 3
        
        # Verify all created runs are in the list
        listed_ids = [run["id"] for run in runs_data["items"]]
        for run_id in run_ids:
            assert run_id in listed_ids

    @pytest.mark.asyncio
    async def test_select_winning_variation(self, client: AsyncClient):
        """Test selecting a winning variation."""
        api_key = await self._setup_user_with_api_key(client)
        headers = {"X-API-Key": api_key}
        
        # Create a run
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for selection",
            "variations": 2
        }
        create_response = await client.post("/api/v1/runs", json=run_data, headers=headers)
        run_id = create_response.json()["run_id"]
        
        # Select winning variation
        selection_data = {
            "variation_id": 0,
            "feedback": "This variation provided better analysis"
        }
        response = await client.post(f"/api/v1/runs/{run_id}/select", 
                                   json=selection_data, headers=headers)
        assert response.status_code == 200
        selection_response = response.json()
        assert "selected_variation" in selection_response

    @pytest.mark.asyncio
    async def test_cancel_run(self, client: AsyncClient):
        """Test canceling a run."""
        api_key = await self._setup_user_with_api_key(client)
        headers = {"X-API-Key": api_key}
        
        # Create a run
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for cancellation",
            "variations": 1
        }
        create_response = await client.post("/api/v1/runs", json=run_data, headers=headers)
        run_id = create_response.json()["run_id"]
        
        # Cancel the run
        response = await client.delete(f"/api/v1/runs/{run_id}", headers=headers)
        assert response.status_code == 200
        cancel_response = response.json()
        assert "status" in cancel_response


@pytest.mark.e2e
class TestStreamingEndpoints:
    """Test streaming functionality."""

    @pytest.mark.asyncio
    async def test_stream_endpoint_access(self, client: AsyncClient):
        """Test streaming endpoint access and basic functionality."""
        # Setup user and create run
        user_data = {
            "email": "streamuser@example.com",
            "password": "StreamPassword123!",
            "full_name": "Stream User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "streamuser@example.com",
            "password": "StreamPassword123!"
        })
        token = login_response.json()["access_token"]
        
        api_key_data = {"name": "Stream Key", "scopes": ["runs:create", "runs:read"]}
        key_response = await client.post("/api/v1/auth/api-keys", json=api_key_data, 
                                       headers={"Authorization": f"Bearer {token}"})
        api_key = key_response.json()["api_key"]
        
        # Create a run
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test streaming",
            "variations": 1
        }
        create_response = await client.post("/api/v1/runs", json=run_data, 
                                          headers={"X-API-Key": api_key})
        run_id = create_response.json()["run_id"]
        
        # Test streaming endpoint access
        stream_response = await client.get(f"/api/v1/runs/{run_id}/stream", 
                                         headers={"X-API-Key": api_key})
        # Stream should be accessible (may not have content yet, but should connect)
        assert stream_response.status_code == 200

    @pytest.mark.asyncio
    async def test_debug_logs_endpoint(self, client: AsyncClient):
        """Test debug logs streaming endpoint."""
        # Setup user and run
        user_data = {
            "email": "debuguser@example.com", 
            "password": "DebugPassword123!",
            "full_name": "Debug User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "debuguser@example.com",
            "password": "DebugPassword123!"
        })
        token = login_response.json()["access_token"]
        
        api_key_data = {"name": "Debug Key", "scopes": ["runs:create", "runs:read"]}
        key_response = await client.post("/api/v1/auth/api-keys", json=api_key_data,
                                       headers={"Authorization": f"Bearer {token}"})
        api_key = key_response.json()["api_key"]
        
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test debug logs",
            "variations": 1
        }
        create_response = await client.post("/api/v1/runs", json=run_data,
                                          headers={"X-API-Key": api_key})
        run_id = create_response.json()["run_id"]
        
        # Test debug logs endpoint
        response = await client.get(f"/api/v1/runs/{run_id}/debug-logs",
                                  headers={"X-API-Key": api_key})
        # Debug endpoint may be disabled in non-debug mode
        assert response.status_code in [200, 404, 405]


@pytest.mark.e2e
class TestModelCatalog:
    """Test model catalog and provider management."""

    async def _get_auth_token(self, client: AsyncClient) -> str:
        """Helper to get auth token."""
        user_data = {
            "email": f"modeluser_{asyncio.get_event_loop().time()}@example.com",
            "password": "ModelPassword123!",
            "full_name": "Model User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_get_model_catalog(self, client: AsyncClient):
        """Test getting the complete model catalog."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/api/v1/models/catalog", headers=headers)
        assert response.status_code == 200
        catalog = response.json()
        assert "models" in catalog
        assert "providers" in catalog
        assert "total_models" in catalog

    @pytest.mark.asyncio
    async def test_get_available_models(self, client: AsyncClient):
        """Test getting available models based on configured credentials."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/api/v1/models/available", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "providers" in data
        assert "total_models" in data
        assert "available_providers" in data

    @pytest.mark.asyncio
    async def test_get_models_with_filters(self, client: AsyncClient):
        """Test getting models with various filters."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test filtering by provider
        response = await client.get("/api/v1/models/models?provider=openai", headers=headers)
        assert response.status_code == 200
        
        # Test filtering by capability
        response = await client.get("/api/v1/models/models?capability=chat", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_model_details(self, client: AsyncClient):
        """Test getting details for a specific model."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # First get available models to find a valid model ID
        models_response = await client.get("/api/v1/models/models", headers=headers)
        models = models_response.json()
        
        if models and len(models) > 0:
            model_id = models[0]["model_name"]
            response = await client.get(f"/api/v1/models/models/{model_id}", headers=headers)
            assert response.status_code == 200
            model_details = response.json()
            assert model_details["model_name"] == model_id

    @pytest.mark.asyncio
    async def test_get_model_recommendations(self, client: AsyncClient):
        """Test getting model recommendations."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        recommendation_request = {
            "task_type": "code_analysis",
            "requirements": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "response_format": "structured"
            }
        }
        
        response = await client.post("/api/v1/models/recommendations", 
                                   json=recommendation_request, headers=headers)
        assert response.status_code == 200
        recommendations = response.json()
        assert "recommended_models" in recommendations

    @pytest.mark.asyncio
    async def test_get_providers(self, client: AsyncClient):
        """Test getting provider information."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/api/v1/models/providers", headers=headers)
        assert response.status_code == 200
        providers = response.json()
        assert isinstance(providers, list)
        for provider in providers:
            assert "provider" in provider
            assert "status" in provider

    @pytest.mark.asyncio
    async def test_get_capabilities(self, client: AsyncClient):
        """Test getting model capabilities."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/api/v1/models/capabilities", headers=headers)
        assert response.status_code == 200
        capabilities = response.json()
        assert isinstance(capabilities, list)


@pytest.mark.e2e
class TestCredentialsManagement:
    """Test provider credentials management."""

    async def _get_auth_token(self, client: AsyncClient) -> str:
        """Helper to get auth token."""
        user_data = {
            "email": f"creduser_{asyncio.get_event_loop().time()}@example.com",
            "password": "CredPassword123!",
            "full_name": "Credentials User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return login_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_create_credential(self, client: AsyncClient):
        """Test creating provider credentials."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        credential_data = {
            "provider": "openai",
            "api_key": "sk-test-key-for-testing",
            "name": "Test OpenAI Credential",
            "description": "API key for testing"
        }
        
        response = await client.post("/api/v1/credentials/", json=credential_data, headers=headers)
        assert response.status_code == 201
        credential = response.json()
        assert credential["provider"] == "openai"
        assert credential["name"] == "Test OpenAI Credential"
        assert "api_key" not in credential  # Should not return raw API key

    @pytest.mark.asyncio
    async def test_list_credentials(self, client: AsyncClient):
        """Test listing user credentials."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create some credentials first
        providers = ["openai", "anthropic", "gemini"]
        created_ids = []
        
        for provider in providers:
            credential_data = {
                "provider": provider,
                "api_key": f"test-key-{provider}",
                "name": f"Test {provider.title()} Key"
            }
            create_response = await client.post("/api/v1/credentials/", 
                                              json=credential_data, headers=headers)
            if create_response.status_code == 201:
                created_ids.append(create_response.json()["id"])
        
        # List credentials
        response = await client.get("/api/v1/credentials/", headers=headers)
        assert response.status_code == 200
        credentials = response.json()
        assert len(credentials) >= len(created_ids)

    @pytest.mark.asyncio
    async def test_get_credential_details(self, client: AsyncClient):
        """Test getting credential details."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a credential
        credential_data = {
            "provider": "openai",
            "api_key": "sk-test-detail-key",
            "name": "Detail Test Key"
        }
        create_response = await client.post("/api/v1/credentials/", 
                                          json=credential_data, headers=headers)
        credential_id = create_response.json()["id"]
        
        # Get credential details
        response = await client.get(f"/api/v1/credentials/{credential_id}", headers=headers)
        assert response.status_code == 200
        credential = response.json()
        assert credential["id"] == credential_id
        assert credential["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_update_credential(self, client: AsyncClient):
        """Test updating a credential."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a credential
        credential_data = {
            "provider": "openai",
            "api_key": "sk-test-update-key",
            "name": "Update Test Key"
        }
        create_response = await client.post("/api/v1/credentials/", 
                                          json=credential_data, headers=headers)
        credential_id = create_response.json()["id"]
        
        # Update the credential
        update_data = {
            "name": "Updated Test Key",
            "description": "Updated description"
        }
        response = await client.put(f"/api/v1/credentials/{credential_id}", 
                                  json=update_data, headers=headers)
        assert response.status_code == 200
        updated_credential = response.json()
        assert updated_credential["name"] == "Updated Test Key"

    @pytest.mark.asyncio
    async def test_delete_credential(self, client: AsyncClient):
        """Test deleting a credential."""
        token = await self._get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a credential
        credential_data = {
            "provider": "openai",
            "api_key": "sk-test-delete-key",
            "name": "Delete Test Key"
        }
        create_response = await client.post("/api/v1/credentials/", 
                                          json=credential_data, headers=headers)
        credential_id = create_response.json()["id"]
        
        # Delete the credential
        response = await client.delete(f"/api/v1/credentials/{credential_id}", headers=headers)
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(f"/api/v1/credentials/{credential_id}", headers=headers)
        assert get_response.status_code == 404


@pytest.mark.e2e
class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_authentication_required_endpoints(self, client: AsyncClient):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/api-keys"),
            ("GET", "/api/v1/auth/api-keys"),
            ("GET", "/api/v1/models/catalog"),
            ("POST", "/api/v1/credentials/"),
            ("GET", "/api/v1/credentials/"),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})
            
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_required_endpoints(self, client: AsyncClient):
        """Test that run endpoints require API key."""
        api_key_endpoints = [
            ("POST", "/api/v1/runs"),
            ("GET", "/api/v1/runs"),
        ]
        
        for method, endpoint in api_key_endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})
            
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, client: AsyncClient):
        """Test handling of invalid JSON in requests."""
        response = await client.post("/api/v1/auth/register", 
                                   content="invalid json", 
                                   headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_resource_handling(self, client: AsyncClient):
        """Test handling of requests for nonexistent resources."""
        # Setup user and API key
        user_data = {
            "email": "notfound@example.com",
            "password": "NotFoundPassword123!",
            "full_name": "Not Found User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "notfound@example.com",
            "password": "NotFoundPassword123!"
        })
        token = login_response.json()["access_token"]
        
        api_key_data = {"name": "Not Found Key", "scopes": ["runs:read"]}
        key_response = await client.post("/api/v1/auth/api-keys", json=api_key_data,
                                       headers={"Authorization": f"Bearer {token}"})
        api_key = key_response.json()["api_key"]
        
        # Test nonexistent run
        response = await client.get("/api/v1/runs/nonexistent-run-id", 
                                  headers={"X-API-Key": api_key})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, client: AsyncClient):
        """Test rate limiting behavior (if enabled)."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for _ in range(10):
            response = await client.get("/health")
            responses.append(response.status_code)
        
        # Should either get 200s (rate limiting disabled) or some 429s (rate limiting enabled)
        assert all(status in [200, 429] for status in responses)

    @pytest.mark.asyncio
    async def test_large_payload_handling(self, client: AsyncClient):
        """Test handling of large payloads."""
        # Test with very long prompt
        large_prompt = "A" * 10000  # 10k character prompt
        
        user_data = {
            "email": "largepayload@example.com",
            "password": "LargePayloadPassword123!",
            "full_name": "Large Payload User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "largepayload@example.com",
            "password": "LargePayloadPassword123!"
        })
        token = login_response.json()["access_token"]
        
        api_key_data = {"name": "Large Payload Key", "scopes": ["runs:create"]}
        key_response = await client.post("/api/v1/auth/api-keys", json=api_key_data,
                                       headers={"Authorization": f"Bearer {token}"})
        api_key = key_response.json()["api_key"]
        
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": large_prompt,
            "variations": 1
        }
        
        response = await client.post("/api/v1/runs", json=run_data, 
                                   headers={"X-API-Key": api_key})
        # Should either accept (if within limits) or reject with 422
        assert response.status_code in [202, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])