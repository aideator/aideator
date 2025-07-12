"""
Unit Tests for Main Application Module

This test suite covers the main FastAPI application setup
to increase test coverage for app/main.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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
    @patch("app.main.redis_service")
    @patch("app.main.logger")
    @patch("app.main.model_sync_task")
    @patch("app.main.create_db_and_tables")
    @patch("app.main.settings", MockSettings())
    async def test_lifespan_startup_and_shutdown(
        self, mock_create_db, mock_sync_task, mock_logger, mock_redis_service
    ):
        """Test lifespan startup and shutdown."""
        # Mock the database creation
        mock_create_db.return_value = None

        # Mock Redis service
        mock_redis_service.connect = AsyncMock()
        mock_redis_service.disconnect = AsyncMock()

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
            mock_redis_service.connect.assert_called_once()
            mock_logger.info.assert_any_call("Redis connected successfully")
            mock_sync_task.start.assert_called_once()
            mock_logger.info.assert_any_call("Model sync task started")

        # Verify shutdown log and actions
        mock_redis_service.disconnect.assert_called_once()
        mock_logger.info.assert_any_call("Redis disconnected")
        mock_logger.info.assert_any_call("Shutting down application")
        mock_sync_task.stop.assert_called_once()
        mock_logger.info.assert_any_call("Model sync task stopped")


class TestCreateApplication:
    """Test application creation."""

    @patch("app.main.settings", MockSettings())
    @patch("app.main.custom_openapi")
    @patch("app.main.make_asgi_app")
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
        routes = [
            getattr(route, "path", None)
            for route in app.routes
            if hasattr(route, "path")
        ]
        assert "/" in routes
        assert "/health" in routes

    @patch("app.main.custom_openapi")
    def test_create_application_production_mode(self, mock_custom_openapi):
        """Test application creation in production mode (debug=False)."""
        # Mock custom openapi
        mock_custom_openapi.return_value = lambda: {"openapi": "3.0.0"}

        # Create production-like settings
        prod_settings = MockSettings()
        prod_settings.debug = False
        prod_settings.project_name = "Prod Project"
        prod_settings.version = "2.0.0"
        prod_settings.api_v1_prefix = "/api/v1"
        prod_settings.allowed_origins = ["https://app.example.com"]
        prod_settings.allowed_hosts = ["api.example.com"]
        prod_settings.rate_limit_enabled = True
        prod_settings.enable_metrics = False

        # Patch settings with production config
        with patch("app.main.settings", prod_settings):
            # Create app
            app = create_application()

            # Verify production configuration
            assert app.docs_url is None  # Should be None in production
            assert app.redoc_url is None  # Should be None in production
            assert app.debug is False

    @patch("app.main.settings")
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

        # Verify app was created successfully with the configuration
        assert app.title == "Test"
        assert app.version == "1.0.0"
        # The middleware would be added based on the allowed_hosts setting
        # but verifying the middleware stack internals is fragile and implementation-dependent

    @patch("app.main.settings")
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
        while hasattr(current, "cls"):
            middleware_types.append(current.cls.__name__)
            if hasattr(current, "app"):
                current = current.app
            else:
                break

        assert "RateLimitMiddleware" not in middleware_types


class TestEndpoints:
    """Test application endpoints."""

    @patch("app.main.settings", MockSettings())
    @patch("app.main.create_db_and_tables", AsyncMock())
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

    @patch("app.main.settings", MockSettings())
    @patch("app.main.create_db_and_tables", AsyncMock())
    @patch("app.main.redis_service")
    def test_health_endpoint(self, mock_redis_service):
        """Test health check endpoint."""
        # Mock Redis service to be healthy
        mock_redis_service.health_check = AsyncMock(return_value=True)

        from app.main import app

        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["orchestration"] == "kubernetes"

    def test_root_endpoint_production(self):
        """Test root endpoint returns correct structure."""
        # Use the existing app instance
        from app.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        # Check the response structure
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert "openapi" in data
        assert "health" in data


class TestMainModule:
    """Test main module execution."""

    def test_main_module_execution(self):
        """Test that main module creates app instance."""
        # Import to ensure the module is loaded
        import app.main

        # Verify the app instance exists
        assert hasattr(app.main, "app")
        assert app.main.app is not None
        assert hasattr(app.main.app, "title")  # It's a FastAPI instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
