"""
Unit Tests for Health API endpoints

This test suite covers the health check endpoints
to increase test coverage for app/api/v1/health.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.health import router


class MockSettings:
    """Mock settings for testing."""
    version = "1.0.0"
    debug = True


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def app():
    """Create FastAPI app with health router."""
    app = FastAPI()
    app.include_router(router)
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


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @patch('app.api.v1.health.settings', MockSettings())
    def test_health_check_development(self, client):
        """Test basic health check in development mode."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
    
    @patch('app.api.v1.health.settings')
    def test_health_check_production(self, mock_settings, client):
        """Test basic health check in production mode."""
        # Configure for production
        mock_settings.version = "2.0.0"
        mock_settings.debug = False
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert data["environment"] == "production"
    
    @patch('app.api.v1.health.settings', MockSettings())
    @patch('app.api.v1.health.get_session')
    @pytest.mark.asyncio
    async def test_detailed_health_check_success(self, mock_get_session, client):
        """Test detailed health check with working database."""
        # Mock successful database query
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=MagicMock())
        
        # Configure dependency override
        app = client.app
        app.dependency_overrides[mock_get_session] = lambda: mock_session
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["checks"]["database"] is True
        assert data["checks"]["kubernetes"] == "Not implemented"
        
        # Verify database was checked
        mock_session.execute.assert_called_once_with("SELECT 1")
    
    @patch('app.api.v1.health.settings', MockSettings())
    @patch('app.api.v1.health.get_session')
    @pytest.mark.asyncio
    async def test_detailed_health_check_database_failure(self, mock_get_session, client):
        """Test detailed health check with database failure."""
        # Mock database query failure
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(side_effect=Exception("Database connection failed"))
        
        # Configure dependency override
        app = client.app
        app.dependency_overrides[mock_get_session] = lambda: mock_session
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["version"] == "1.0.0"
        assert data["checks"]["database"] == "Database connection failed"
        assert data["checks"]["kubernetes"] == "Not implemented"
    
    def test_health_routes_registered(self, app):
        """Test that health routes are properly registered."""
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/health/detailed" in routes
    
    def test_health_endpoint_methods(self, client):
        """Test that health endpoints only accept GET requests."""
        # Test /health endpoint
        response = client.post("/health")
        assert response.status_code == 405  # Method not allowed
        
        response = client.put("/health")
        assert response.status_code == 405
        
        response = client.delete("/health")
        assert response.status_code == 405
        
        # Test /health/detailed endpoint
        response = client.post("/health/detailed")
        assert response.status_code == 405
        
        response = client.put("/health/detailed")
        assert response.status_code == 405
        
        response = client.delete("/health/detailed")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])