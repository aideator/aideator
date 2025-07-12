"""Tests for health API endpoints."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.health import router
from app.services.agent_orchestrator import AgentOrchestrator


class TestHealthEndpoints:
    """Test health API endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator."""
        orchestrator = Mock(spec=AgentOrchestrator)
        orchestrator._total_active_jobs = 5
        orchestrator.get_active_runs.return_value = {
            "run-1": {"variations": 3},
            "run-2": {"variations": 2},
        }
        return orchestrator

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return Mock(
            version="1.0.0",
            debug=False,
            max_concurrent_runs=10,
            max_concurrent_jobs=20,
            max_variations=5,
            redis_url="redis://localhost:6379",
        )

    @pytest.mark.asyncio
    async def test_health_check(self, mock_settings):
        """Test basic health check."""
        with patch("app.api.v1.health.settings", mock_settings):
            from app.api.v1.health import health_check

            result = await health_check()

            assert result["status"] == "healthy"
            assert result["version"] == "1.0.0"
            assert result["environment"] == "production"

    @pytest.mark.asyncio
    async def test_health_check_debug_mode(self, mock_settings):
        """Test health check in debug mode."""
        mock_settings.debug = True

        with patch("app.api.v1.health.settings", mock_settings):
            from app.api.v1.health import health_check

            result = await health_check()

            assert result["environment"] == "development"

    @pytest.mark.asyncio
    async def test_detailed_health_check_success(self, mock_db, mock_settings):
        """Test detailed health check with all services healthy."""
        # Mock successful database query
        mock_db.execute.return_value = None

        with patch("app.api.v1.health.settings", mock_settings):
            from app.api.v1.health import detailed_health_check

            result = await detailed_health_check(db=mock_db)

            assert result["status"] == "healthy"
            assert result["version"] == "1.0.0"
            assert result["checks"]["database"] == "OK"
            assert result["checks"]["kubernetes"] == "Not implemented"

    @pytest.mark.asyncio
    async def test_detailed_health_check_db_failure(self, mock_db, mock_settings):
        """Test detailed health check with database failure."""
        # Mock database error
        mock_db.execute.side_effect = Exception("Connection refused")

        with patch("app.api.v1.health.settings", mock_settings):
            from app.api.v1.health import detailed_health_check

            result = await detailed_health_check(db=mock_db)

            assert result["status"] == "degraded"
            assert result["checks"]["database"] == "Connection refused"

    @pytest.mark.asyncio
    async def test_system_status(self, mock_orchestrator, mock_settings):
        """Test system status endpoint."""
        with patch("app.api.v1.health.settings", mock_settings):
            from app.api.v1.health import system_status

            result = await system_status(orchestrator=mock_orchestrator)

            assert result["status"] == "operational"

            # Check limits
            assert result["limits"]["max_concurrent_runs"] == 10
            assert result["limits"]["max_concurrent_jobs"] == 20
            assert result["limits"]["max_variations_per_run"] == 5

            # Check usage
            assert result["usage"]["active_runs"] == 2
            assert result["usage"]["active_jobs"] == 5
            assert result["usage"]["estimated_jobs"] == 5  # 3 + 2

            # Check capacity
            assert result["capacity"]["runs_available"] == 8  # 10 - 2
            assert result["capacity"]["jobs_available"] == 15  # 20 - 5

            # Check active run IDs
            assert result["active_run_ids"] == ["run-1", "run-2"]

    @pytest.mark.asyncio
    async def test_system_status_empty_runs(self, mock_settings):
        """Test system status with no active runs."""
        mock_orchestrator = Mock(spec=AgentOrchestrator)
        mock_orchestrator._total_active_jobs = 0
        mock_orchestrator.get_active_runs.return_value = {}

        with patch("app.api.v1.health.settings", mock_settings):
            from app.api.v1.health import system_status

            result = await system_status(orchestrator=mock_orchestrator)

            assert result["usage"]["active_runs"] == 0
            assert result["usage"]["active_jobs"] == 0
            assert result["usage"]["estimated_jobs"] == 0
            assert result["active_run_ids"] == []

    @pytest.mark.asyncio
    async def test_redis_test_success(self, mock_settings):
        """Test Redis connectivity test with success."""
        mock_redis_service = AsyncMock()
        mock_redis_service.health_check.return_value = True
        mock_redis_service.publish_agent_output.return_value = 1  # 1 subscriber

        # Mock the async generator for subscribe
        async def mock_subscribe(*args, **kwargs):
            yield {"data": "Test message for subscriber"}

        mock_redis_service.subscribe_to_run = mock_subscribe

        with patch("app.api.v1.health.settings", mock_settings):
            with patch("app.services.redis_service.redis_service", mock_redis_service):
                from app.api.v1.health import test_redis

                result = await test_redis()

                assert result["connected"] is True
                assert result["health_check"] is True
                assert result["publish_test"] is True
                assert result["publish_subscribers"] == 1
                assert result["subscribe_test"] is True
                assert result["messages_received"] == 1
                assert result["error"] is None

    @pytest.mark.asyncio
    async def test_redis_test_health_check_failure(self, mock_settings):
        """Test Redis test with health check failure."""
        mock_redis_service = AsyncMock()
        mock_redis_service.health_check.side_effect = Exception("Connection failed")

        with patch("app.api.v1.health.settings", mock_settings):
            with patch("app.services.redis_service.redis_service", mock_redis_service):
                from app.api.v1.health import test_redis

                result = await test_redis()

                assert result["connected"] is False
                assert result["health_check"] is False
                assert result["publish_test"] is False
                assert result["subscribe_test"] is False
                assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_redis_test_subscribe_timeout(self, mock_settings):
        """Test Redis test with subscribe timeout."""
        mock_redis_service = AsyncMock()
        mock_redis_service.health_check.return_value = True
        mock_redis_service.publish_agent_output.return_value = 0  # No subscribers

        # Mock the async generator that never yields
        async def mock_subscribe(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            yield {"data": "Never received"}

        mock_redis_service.subscribe_to_run = mock_subscribe

        with patch("app.api.v1.health.settings", mock_settings):
            with patch("app.services.redis_service.redis_service", mock_redis_service):
                from app.api.v1.health import test_redis

                result = await test_redis()

                assert result["connected"] is True
                assert result["health_check"] is True
                assert result["publish_test"] is True
                assert result["subscribe_test"] is False
                assert result["messages_received"] == 0

    @pytest.mark.asyncio
    async def test_redis_test_publish_failure(self, mock_settings):
        """Test Redis test with publish failure."""
        mock_redis_service = AsyncMock()
        mock_redis_service.health_check.return_value = True
        mock_redis_service.publish_agent_output.side_effect = Exception(
            "Publish failed"
        )

        with patch("app.api.v1.health.settings", mock_settings):
            with patch("app.services.redis_service.redis_service", mock_redis_service):
                from app.api.v1.health import test_redis

                result = await test_redis()

                assert result["connected"] is True
                assert result["health_check"] is True
                assert result["publish_test"] is False
                assert "Publish failed" in result["error"]

    def test_router_exists(self):
        """Test that router is properly configured."""
        assert router is not None
        # Check that endpoints are registered
        routes = [route.path for route in router.routes]
        assert "/health" in routes
        assert "/health/detailed" in routes
        assert "/system/status" in routes
        assert "/redis/test" in routes
