import asyncio
import json

import pytest
from httpx import AsyncClient

from app.models.run import RunStatus


class TestHealthAPI:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test basic health check."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client: AsyncClient):
        """Test detailed health check."""
        response = await client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "checks" in data
        assert "database" in data["checks"]


class TestAuthAPI:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_user_registration(self, client: AsyncClient):
        """Test user registration flow."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_user_registration_duplicate(self, client: AsyncClient, make_user):
        """Test duplicate email registration."""
        # Create existing user
        user = await make_user(email="existing@example.com")
        
        # Try to register with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_user_login(self, client: AsyncClient, make_user):
        """Test user login."""
        # Create user
        user = await make_user(email="logintest@example.com")
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_create_api_key(self, client: AsyncClient, make_user, auth_headers):
        """Test API key creation."""
        # Create user and login
        user = await make_user()
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": "TestPassword123",
            },
        )
        token = login_response.json()["access_token"]
        
        # Create API key
        response = await client.post(
            "/api/v1/auth/api-keys",
            json={
                "name": "Test API Key",
                "scopes": ["runs:create", "runs:read"],
                "expires_in_days": 30,
            },
            headers=auth_headers(token),
        )
        assert response.status_code == 201
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("aid_sk_")
        assert data["key_info"]["name"] == "Test API Key"


class TestRunsAPI:
    """Test runs endpoints."""

    @pytest.mark.asyncio
    async def test_create_run(self, client: AsyncClient, sample_run_request):
        """Test creating a new run."""
        response = await client.post("/api/v1/runs", json=sample_run_request)
        assert response.status_code == 202
        data = response.json()
        assert "run_id" in data
        assert "stream_url" in data
        assert data["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_create_run_with_api_key(
        self, client: AsyncClient, make_user, make_api_key, sample_run_request
    ):
        """Test creating run with API key authentication."""
        # Create user and API key
        user = await make_user()
        api_key, _ = await make_api_key(user)
        
        # Create run
        response = await client.post(
            "/api/v1/runs",
            json=sample_run_request,
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_list_runs(self, client: AsyncClient, make_run):
        """Test listing runs."""
        # Create some runs
        for i in range(3):
            await make_run(prompt=f"Test prompt {i}")
        
        # List runs
        response = await client.get("/api/v1/runs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 3
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_get_run_details(self, client: AsyncClient, make_run):
        """Test getting run details."""
        # Create run
        run = await make_run()
        
        # Get details
        response = await client.get(f"/api/v1/runs/{run.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run.id
        assert data["prompt"] == run.prompt

    @pytest.mark.asyncio
    async def test_select_winner(self, client: AsyncClient, make_run):
        """Test selecting winning variation."""
        # Create completed run
        run = await make_run(status=RunStatus.COMPLETED, variations=3)
        
        # Select winner
        response = await client.post(
            f"/api/v1/runs/{run.id}/select",
            json={"winning_variation_id": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["winning_variation_id"] == 1

    @pytest.mark.asyncio
    async def test_cancel_run(self, client: AsyncClient, make_run):
        """Test cancelling a run."""
        # Create pending run
        run = await make_run(status=RunStatus.PENDING)
        
        # Cancel it
        response = await client.delete(f"/api/v1/runs/{run.id}")
        assert response.status_code == 204


class TestStreamingAPI:
    """Test SSE streaming endpoints."""

    @pytest.mark.asyncio
    async def test_stream_connection(self, client: AsyncClient, make_run):
        """Test SSE stream connection."""
        # Create run
        run = await make_run()
        
        # Connect to stream
        async with client.stream("GET", f"/api/v1/runs/{run.id}/stream") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            
            # Read first event (should be heartbeat)
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    assert "heartbeat" in line
                    break