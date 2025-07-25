"""
Test admin API endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.admin import (
    get_sync_history,
    get_sync_status,
    trigger_model_sync,
)
from app.models.model_definition import ModelSyncLog
from app.models.user import User


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Test cases for admin endpoints."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return User(id=1, email="admin@aideator.com", username="admin", is_active=True)

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock()
        session.exec = Mock()
        return session

    @pytest.mark.asyncio
    async def test_trigger_model_sync_success(self):
        """Test successful model sync trigger."""
        with patch("app.api.v1.endpoints.admin.model_sync_task") as mock_task:
            mock_task.sync_now = AsyncMock()

            result = await trigger_model_sync()

            mock_task.sync_now.assert_called_once()
            assert result["status"] == "success"
            assert "triggered" in result["message"]

    @pytest.mark.asyncio
    async def test_trigger_model_sync_error(self):
        """Test error handling in sync trigger."""
        with patch("app.api.v1.endpoints.admin.model_sync_task") as mock_task:
            mock_task.sync_now = AsyncMock(side_effect=Exception("Connection failed"))

            with pytest.raises(HTTPException) as exc_info:
                await trigger_model_sync()

            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == 500
            assert "Connection failed" in str(exc.detail)

    @pytest.mark.asyncio
    async def test_get_sync_history(self, mock_session):
        """Test getting sync history."""
        # Create mock sync logs
        sync_logs = [
            ModelSyncLog(
                id=1,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="success",
                models_discovered=10,
                models_added=5,
                models_updated=3,
                models_deactivated=1,
            ),
            ModelSyncLog(
                id=2,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="failed",
                error_message="Connection timeout",
            ),
        ]

        mock_session.exec.return_value.all.return_value = sync_logs

        result = await get_sync_history(session=mock_session)

        assert len(result) == 2
        assert result[0].status == "success"
        assert result[1].status == "failed"

    @pytest.mark.asyncio
    async def test_get_sync_history_with_limit(self, mock_session):
        """Test sync history with limit."""
        mock_session.exec.return_value.all.return_value = []

        await get_sync_history(session=mock_session, limit=5)

        # Verify limit was applied
        exec_call = mock_session.exec.call_args[0][0]
        assert "LIMIT :param_1" in str(exec_call)

    @pytest.mark.asyncio
    async def test_get_sync_status(self, mock_session):
        """Test getting sync status."""
        # Mock last sync log
        last_sync = ModelSyncLog(
            id=1,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status="success",
            models_discovered=15,
        )

        # Create separate mock results for each query
        mock_sync_result = Mock()
        mock_sync_result.first.return_value = last_sync
        mock_models_result = Mock()
        mock_models_result.all.return_value = [
            Mock() for _ in range(25)
        ]  # 25 mock models

        # Mock session.exec to return different results based on call order
        mock_session.exec.side_effect = [mock_sync_result, mock_models_result]

        with patch("app.api.v1.endpoints.admin.model_sync_task") as mock_task:
            mock_task.is_running = True
            mock_task.sync_interval.total_seconds.return_value = 3600  # 60 minutes

            result = await get_sync_status(session=mock_session)

            assert result["sync_task_running"] is True
            assert result["last_sync"] == last_sync
            assert result["active_models_count"] == 25
            assert result["sync_interval_minutes"] == 60

    @pytest.mark.asyncio
    async def test_get_sync_status_no_sync_history(self, mock_session):
        """Test sync status when no sync has run yet."""
        # Create separate mock results for each query
        mock_sync_result = Mock()
        mock_sync_result.first.return_value = None
        mock_models_result = Mock()
        mock_models_result.all.return_value = []  # No models

        # Mock session.exec to return different results based on call order
        mock_session.exec.side_effect = [mock_sync_result, mock_models_result]

        with patch("app.api.v1.endpoints.admin.model_sync_task") as mock_task:
            mock_task.is_running = False
            mock_task.sync_interval.total_seconds.return_value = 3600

            result = await get_sync_status(session=mock_session)

            assert result["sync_task_running"] is False
            assert result["last_sync"] is None
            assert result["active_models_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
