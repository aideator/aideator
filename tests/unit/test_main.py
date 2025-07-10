"""
Unit Tests for Main Application Module

This test suite covers the main FastAPI application setup
to increase test coverage for app/main.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.main import create_application, lifespan


class MockSettings:
    """Mock settings for testing."""
    project_name = "Test Project"
    version = "1.0.0"
    api_v1_prefix = "/api/v1"
    debug = True
    allowed_origins = ["http://localhost:3000"]
    allowed_hosts = ["*"]
    rate_limit_enabled = True
    enable_metrics = True
    host = "0.0.0.0"
    port = 8000
    reload = False
    log_level = "info"


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def mock_logger():
    """Provide mock logger."""
    return MagicMock()


class TestLifespan:
    """Test lifespan context manager."""
    
    @pytest.mark.asyncio
    @patch('app.main.logger')
    @patch('app.main.model_sync_task')
    @patch('app.main.create_db_and_tables')
    @patch('app.main.settings', MockSettings())
    async def test_lifespan_startup_and_shutdown(self, mock_create_db, mock_sync_task, mock_logger):
        """Test lifespan startup and shutdown."""
        # Mock the database creation
        mock_create_db.return_value = None
        
        # Mock the model sync task
        mock_sync_task.start = AsyncMock()
        mock_sync_task.stop = AsyncMock()
        
        # Create a mock app
        app = MagicMock(spec=FastAPI)
        
        # Test the lifespan context manager
        async with lifespan(app):
            # Verify startup logs and actions
            mock_logger.info.assert_any_call("Starting Test Project v1.0.0")
            mock_create_db.assert_called_once()
            mock_logger.info.assert_any_call("Database initialized")
            mock_sync_task.start.assert_called_once()
            mock_logger.info.assert_any_call("Model sync task started")
        
        # Verify shutdown log and actions
        mock_logger.info.assert_any_call("Shutting down application")
        mock_sync_task.stop.assert_called_once()
        mock_logger.info.assert_any_call("Model sync task stopped")


class TestCreateApplication:
    """Test application creation."""
    
    @patch('app.main.settings', MockSettings())
    @patch('app.main.custom_openapi')
    @patch('app.main.make_asgi_app')
    def test_create_application_with_debug(self, mock_metrics_app, mock_custom_openapi):
        """Test application creation with debug mode enabled."""
        # Mock custom openapi
        mock_custom_openapi.return_value = lambda: {"openapi": "3.0.0"}
        
        # Mock metrics app
        mock_metrics = MagicMock()
        mock_metrics_app.return_value = mock_metrics
        
        # Create app
        app = create_application()
        
        # Verify FastAPI configuration
        assert app.title == "Test Project"
        assert app.version == "1.0.0"
        assert app.openapi_url == "/api/v1/openapi.json"
        assert app.docs_url == "/docs"  # Should be present in debug mode
        assert app.redoc_url == "/redoc"  # Should be present in debug mode
        assert app.debug is True
        
        # Verify custom openapi was set
        mock_custom_openapi.assert_called_once_with(app)
        
        # Verify metrics app was mounted
        mock_metrics_app.assert_called_once()
        
        # Verify routes exist
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
    
    @patch('app.main.settings')
    @patch('app.main.custom_openapi')
    def test_create_application_production_mode(self, mock_custom_openapi, mock_settings):
        """Test application creation in production mode (debug=False)."""
        # Configure mock settings for production
        mock_settings.project_name = "Prod Project"
        mock_settings.version = "2.0.0"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.debug = False
        mock_settings.allowed_origins = ["https://app.example.com"]
        mock_settings.allowed_hosts = ["api.example.com"]
        mock_settings.rate_limit_enabled = True
        mock_settings.enable_metrics = False
        
        # Mock custom openapi
        mock_custom_openapi.return_value = lambda: {"openapi": "3.0.0"}
        
        # Create app
        app = create_application()
        
        # Verify production configuration
        assert app.docs_url is None  # Should be None in production
        assert app.redoc_url is None  # Should be None in production
        assert app.debug is False
    
    @patch('app.main.settings')
    def test_create_application_with_trusted_hosts(self, mock_settings):
        """Test application creation with trusted host middleware."""
        # Configure specific allowed hosts
        mock_settings.project_name = "Test"
        mock_settings.version = "1.0.0"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.debug = True
        mock_settings.allowed_origins = ["*"]
        mock_settings.allowed_hosts = ["example.com", "*.example.com"]
        mock_settings.rate_limit_enabled = False
        mock_settings.enable_metrics = False
        
        # Create app
        app = create_application()
        
        # Verify TrustedHostMiddleware was added
        # Check middleware stack contains TrustedHostMiddleware
        middleware_types = []
        current = app.middleware_stack
        while hasattr(current, 'cls'):
            middleware_types.append(current.cls.__name__)
            if hasattr(current, 'app'):
                current = current.app
            else:
                break
        
        assert "TrustedHostMiddleware" in middleware_types
    
    @patch('app.main.settings')
    def test_create_application_without_rate_limit(self, mock_settings):
        """Test application creation without rate limiting."""
        # Configure without rate limiting
        mock_settings.project_name = "Test"
        mock_settings.version = "1.0.0"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.debug = True
        mock_settings.allowed_origins = ["*"]
        mock_settings.allowed_hosts = ["*"]
        mock_settings.rate_limit_enabled = False
        mock_settings.enable_metrics = False
        
        # Create app
        app = create_application()
        
        # Verify RateLimitMiddleware was not added
        middleware_types = []
        current = app.middleware_stack
        while hasattr(current, 'cls'):
            middleware_types.append(current.cls.__name__)
            if hasattr(current, 'app'):
                current = current.app
            else:
                break
        
        assert "RateLimitMiddleware" not in middleware_types


class TestEndpoints:
    """Test application endpoints."""
    
    @patch('app.main.settings', MockSettings())
    @patch('app.main.create_db_and_tables', AsyncMock())
    def test_root_endpoint(self):
        """Test root endpoint returns API information."""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["openapi"] == "/api/v1/openapi.json"
        assert data["health"] == "/health"
    
    @patch('app.main.settings', MockSettings())
    @patch('app.main.create_db_and_tables', AsyncMock())
    def test_health_endpoint(self):
        """Test health check endpoint."""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["orchestration"] == "kubernetes"
    
    @patch('app.main.settings')
    @patch('app.main.create_db_and_tables', AsyncMock())
    def test_root_endpoint_production(self, mock_settings):
        """Test root endpoint in production mode (no docs)."""
        # Configure for production
        mock_settings.project_name = "Prod"
        mock_settings.version = "1.0.0"
        mock_settings.api_v1_prefix = "/api/v1"
        mock_settings.debug = False
        mock_settings.allowed_origins = ["*"]
        mock_settings.allowed_hosts = ["*"]
        mock_settings.rate_limit_enabled = False
        mock_settings.enable_metrics = False
        
        # Need to reimport to get fresh app instance
        import importlib
        import app.main
        importlib.reload(app.main)
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["docs"] is None  # Should be None in production


class TestMainModule:
    """Test main module execution."""
    
    @patch('app.main.uvicorn')
    @patch('app.main.settings', MockSettings())
    def test_main_module_execution(self, mock_uvicorn):
        """Test that main module runs uvicorn when executed directly."""
        # Execute the main block
        import app.main
        
        # Simulate __name__ == "__main__"
        with patch.object(app.main, '__name__', '__main__'):
            # Re-execute the module code
            exec(compile(open('app/main.py').read(), 'app/main.py', 'exec'), 
                 {'__name__': '__main__'})
        
        # Verify uvicorn.run was called
        mock_uvicorn.run.assert_called_with(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
            access_log=True,
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])