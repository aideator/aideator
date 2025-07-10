"""
Unit Tests for Streams API endpoints

This test suite covers the streaming endpoints
to increase test coverage for app/api/v1/streams.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.api.v1.streams import router
from app.models.run import Run, RunStatus
from app.models.user import User


class MockSettings:
    """Mock settings for testing."""
    debug_agent_container = False
    kubernetes_namespace = "aideator"


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def app():
    """Create FastAPI app with streams router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/runs")
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
        is_active=True
    )
    return user


@pytest.fixture
def mock_run():
    """Create a mock run."""
    run = Run(
        id="run-123",
        user_id="user-123",
        github_url="https://github.com/test/repo",
        prompt="Test prompt",
        variations=3,
        status=RunStatus.RUNNING,
    )
    return run


class TestStreamEndpoints:
    """Test streaming endpoints."""
    
    @patch('app.api.v1.streams.get_session')
    @patch('app.api.v1.streams.sse_manager')
    @pytest.mark.asyncio
    async def test_stream_run_success(self, mock_sse_manager, mock_get_session, client, mock_user, mock_run):
        """Test successful run streaming."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value = mock_session
        
        # Mock SSE manager connect
        async def mock_stream():
            yield "data: test event\n\n"
        
        mock_sse_manager.connect.return_value = mock_stream()
        
        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user
        
        # Stream run
        response = client.get("/api/v1/runs/run-123/stream", stream=True)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"
        
        # Read some stream data
        data = next(response.iter_lines())
        assert b"data: test event" in data
        
        # Verify SSE manager was called
        mock_sse_manager.connect.assert_called_once_with("run-123")
    
    @patch('app.api.v1.streams.get_session')
    @pytest.mark.asyncio
    async def test_stream_run_not_found(self, mock_get_session, client, mock_user):
        """Test streaming non-existent run."""
        # Mock database session - run not found
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value = mock_session
        
        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user
        
        # Try to stream non-existent run
        response = client.get("/api/v1/runs/nonexistent/stream")
        
        assert response.status_code == 404
        assert "Run not found" in response.json()["detail"]
    
    @patch('app.api.v1.streams.get_session')
    @pytest.mark.asyncio
    async def test_stream_run_wrong_user(self, mock_get_session, client, mock_user):
        """Test streaming run belonging to another user."""
        # Create run for different user
        other_run = Run(
            id="run-456",
            user_id="other-user-id",
            github_url="https://github.com/test/repo",
            prompt="Test prompt",
            variations=3,
            status=RunStatus.RUNNING,
        )
        
        # Mock database session - returns other user's run but filtered query returns None
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Filtered by user_id
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value = mock_session
        
        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user
        
        # Try to stream another user's run
        response = client.get("/api/v1/runs/run-456/stream")
        
        assert response.status_code == 404
        assert "Run not found" in response.json()["detail"]
    
    @patch('app.api.v1.streams.get_settings')
    @patch('app.api.v1.streams.get_session')
    @pytest.mark.asyncio
    async def test_debug_logs_disabled(self, mock_get_session, mock_get_settings, client):
        """Test debug logs when debug mode is disabled."""
        # Configure settings with debug disabled
        mock_settings = MockSettings()
        mock_settings.debug_agent_container = False
        mock_get_settings.return_value = mock_settings
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_get_session.return_value = mock_session
        
        # Try to access debug logs
        response = client.get("/api/v1/runs/run-123/debug-logs")
        
        assert response.status_code == 403
        assert "Debug mode is not enabled" in response.json()["detail"]
    
    @patch('app.api.v1.streams.get_settings')
    @patch('app.api.v1.streams.get_session')
    @patch('app.api.v1.streams.KubernetesService')
    @pytest.mark.asyncio
    async def test_debug_logs_success(self, mock_k8s_class, mock_get_session, mock_get_settings, client, mock_user, mock_run):
        """Test successful debug log streaming."""
        # Configure settings with debug enabled
        mock_settings = MockSettings()
        mock_settings.debug_agent_container = True
        mock_settings.kubernetes_namespace = "test-namespace"
        mock_get_settings.return_value = mock_settings
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value = mock_session
        
        # Mock Kubernetes service
        mock_k8s = MagicMock()
        async def mock_debug_logs():
            yield "[2024-01-01] Starting agent..."
            yield "[2024-01-01] Processing repository..."
            yield "[2024-01-01] Complete."
        
        mock_k8s.stream_raw_debug_logs.return_value = mock_debug_logs()
        mock_k8s_class.return_value = mock_k8s
        
        # Mock current user dependency (optional for debug logs)
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user
        
        # Stream debug logs
        response = client.get("/api/v1/runs/run-123/debug-logs?variation_id=1", stream=True)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Read stream data
        lines = list(response.iter_lines())
        assert b"Debug logs for agent-run-123-1" in lines[0]
        assert b"[2024-01-01] Starting agent..." in lines[1]
        
        # Verify Kubernetes service was initialized correctly
        mock_k8s_class.assert_called_once_with(namespace="test-namespace")
        mock_k8s.stream_raw_debug_logs.assert_called_once_with("agent-run-123-1")
    
    @patch('app.api.v1.streams.get_settings')
    @patch('app.api.v1.streams.get_session')
    @patch('app.api.v1.streams.KubernetesService')
    @pytest.mark.asyncio
    async def test_debug_logs_error_handling(self, mock_k8s_class, mock_get_session, mock_get_settings, client, mock_user, mock_run):
        """Test debug log streaming with Kubernetes error."""
        # Configure settings with debug enabled
        mock_settings = MockSettings()
        mock_settings.debug_agent_container = True
        mock_settings.kubernetes_namespace = "test-namespace"
        mock_get_settings.return_value = mock_settings
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value = mock_session
        
        # Mock Kubernetes service with error
        mock_k8s = MagicMock()
        async def mock_debug_logs_error():
            yield "Starting logs..."
            raise Exception("Pod not found")
        
        mock_k8s.stream_raw_debug_logs.return_value = mock_debug_logs_error()
        mock_k8s_class.return_value = mock_k8s
        
        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user
        
        # Stream debug logs
        response = client.get("/api/v1/runs/run-123/debug-logs", stream=True)
        
        assert response.status_code == 200
        
        # Read stream data
        lines = list(response.iter_lines())
        assert b"Debug logs for agent-run-123-0" in lines[0]
        assert b"Starting logs..." in lines[1]
        assert b"[ERROR] Error streaming debug logs: Pod not found" in lines[2]
    
    @patch('app.api.v1.streams.get_settings')
    @patch('app.api.v1.streams.get_session')
    @pytest.mark.asyncio
    async def test_debug_logs_unauthenticated_access(self, mock_get_session, mock_get_settings, client, mock_run):
        """Test debug logs can be accessed without authentication (if run exists)."""
        # Configure settings with debug enabled
        mock_settings = MockSettings()
        mock_settings.debug_agent_container = True
        mock_get_settings.return_value = mock_settings
        
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value = mock_session
        
        # No user dependency override - should work without auth
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: None
        
        # Access debug logs without authentication
        with patch('app.api.v1.streams.KubernetesService') as mock_k8s_class:
            mock_k8s = MagicMock()
            async def mock_logs():
                yield "Log line 1"
            mock_k8s.stream_raw_debug_logs.return_value = mock_logs()
            mock_k8s_class.return_value = mock_k8s
            
            response = client.get("/api/v1/runs/run-123/debug-logs", stream=True)
            
            assert response.status_code == 200
    
    def test_stream_routes_registered(self, app):
        """Test that stream routes are properly registered."""
        routes = [route.path for route in app.routes]
        assert "/api/v1/runs/{run_id}/stream" in routes
        assert "/api/v1/runs/{run_id}/debug-logs" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])