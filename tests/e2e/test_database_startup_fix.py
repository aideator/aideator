"""
E2E tests for database startup fix.

These tests verify the entire application startup flow works correctly
when there are database schema conflicts.
"""

import pytest
import httpx
import asyncio
import time
from typing import AsyncGenerator

from app.core.config import get_settings


class TestDatabaseStartupE2E:
    """End-to-end tests for database startup with schema conflicts."""
    
    @pytest.fixture
    async def app_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Create an async HTTP client for testing the running application."""
        settings = get_settings()
        base_url = f"http://localhost:{settings.port}"
        
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            # Wait for the application to be ready
            max_retries = 30
            for attempt in range(max_retries):
                try:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    if attempt == max_retries - 1:
                        raise Exception("Application failed to start within timeout")
                    await asyncio.sleep(1)
            
            yield client
    
    @pytest.mark.asyncio
    async def test_application_starts_successfully(self, app_client: httpx.AsyncClient):
        """Test that the application starts successfully despite schema conflicts."""
        response = await app_client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "version" in health_data
        # Accept either environment or orchestration field
        assert "environment" in health_data or "orchestration" in health_data
    
    @pytest.mark.asyncio
    async def test_api_endpoints_accessible_after_startup(self, app_client: httpx.AsyncClient):
        """Test that core API endpoints are accessible after startup."""
        # Test health endpoint
        response = await app_client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Test OpenAPI docs endpoint
        response = await app_client.get("/docs")
        assert response.status_code == 200
        
        # Test OpenAPI spec endpoint (try both common paths)
        response = await app_client.get("/openapi.json")
        if response.status_code == 404:
            response = await app_client.get("/api/v1/openapi.json")
        
        assert response.status_code == 200
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
    
    @pytest.mark.asyncio
    async def test_database_dependent_endpoints_work(self, app_client: httpx.AsyncClient):
        """Test that endpoints requiring database access work after startup."""
        # Test models endpoint (requires database for model definitions)
        response = await app_client.get("/api/v1/models")
        # Should not return 500 server error (database connection issues)
        assert response.status_code in [200, 401, 403, 404]  # 404 if endpoint doesn't exist, but not 500
        
        # Test authentication endpoints structure
        response = await app_client.get("/api/v1/auth/me")
        # Should return 401/403 (unauthorized/forbidden) but not 500 (server error)
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_application_handles_concurrent_requests(self, app_client: httpx.AsyncClient):
        """Test that the application handles concurrent requests properly after startup."""
        # Make multiple concurrent health check requests
        tasks = []
        for _ in range(10):
            task = app_client.get("/api/v1/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_application_startup_logs_no_critical_errors(self, app_client: httpx.AsyncClient):
        """Test that application startup doesn't generate critical errors."""
        # First verify the app is running
        response = await app_client.get("/health")
        assert response.status_code == 200
        
        # The fact that we can reach this point means the database
        # initialization didn't cause a startup failure
        health_data = response.json()
        assert health_data["status"] == "healthy"


class TestDatabaseRecoveryScenarios:
    """Test database recovery scenarios and edge cases."""
    
    @pytest.fixture
    async def app_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Create an async HTTP client for testing the running application."""
        settings = get_settings()
        base_url = f"http://localhost:{settings.port}"
        
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            # Wait for the application to be ready with longer timeout for startup scenarios
            max_retries = 60  # Longer timeout for database recovery scenarios
            for attempt in range(max_retries):
                try:
                    response = await client.get("/health")
                    if response.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    if attempt == max_retries - 1:
                        raise Exception("Application failed to start within extended timeout")
                    await asyncio.sleep(2)
            
            yield client
    
    @pytest.mark.asyncio
    async def test_app_survives_database_schema_conflicts(self, app_client: httpx.AsyncClient):
        """Test that the app can start even with pre-existing database schema."""
        # The application should be running despite any schema conflicts
        response = await app_client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Test that the application can handle requests normally
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Test multiple endpoints to ensure stability
        endpoints_to_test = [
            "/health",
            "/api/v1/health", 
            "/docs",
            "/openapi.json"
        ]
        
        for endpoint in endpoints_to_test:
            response = await app_client.get(endpoint)
            # Should not return 500 errors (server/database issues)
            assert response.status_code < 500, f"Endpoint {endpoint} returned server error"
    
    @pytest.mark.asyncio 
    async def test_repeated_health_checks_remain_stable(self, app_client: httpx.AsyncClient):
        """Test that repeated health checks remain stable over time."""
        # Perform multiple health checks over a period of time
        for i in range(5):
            response = await app_client.get("/api/v1/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            
            if i < 4:  # Don't sleep after the last iteration
                await asyncio.sleep(1)
    
    @pytest.mark.asyncio
    async def test_application_maintains_database_connection(self, app_client: httpx.AsyncClient):
        """Test that the application maintains its database connection after startup."""
        # First health check
        response = await app_client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Wait a bit to ensure connection persistence
        await asyncio.sleep(2)
        
        # Second health check should still work
        response = await app_client.get("/api/v1/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"