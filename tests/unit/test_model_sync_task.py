"""Tests for the model sync task."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.tasks.model_sync_task import ModelSyncTask, model_sync_task


class TestModelSyncTask:
    """Test the model sync task."""

    @pytest.fixture
    def task(self):
        """Create a model sync task instance."""
        return ModelSyncTask(sync_interval_minutes=5)

    @pytest.fixture
    def mock_model_sync_service(self):
        """Create a mock model sync service."""
        mock_service = Mock()
        mock_sync_log = Mock()
        mock_sync_log.models_discovered = 10
        mock_sync_log.models_added = 2
        mock_sync_log.models_updated = 1
        mock_sync_log.models_deactivated = 0
        mock_service.sync_models = AsyncMock(return_value=mock_sync_log)
        return mock_service

    @pytest.fixture
    def mock_get_sync_session(self):
        """Create a mock get_sync_session function."""
        mock_session = Mock()
        return Mock(return_value=[mock_session])

    def test_init(self, task):
        """Test task initialization."""
        assert task.sync_interval == timedelta(minutes=5)
        assert task.is_running is False
        assert task._task is None

    @pytest.mark.asyncio
    async def test_start_task(self, task):
        """Test starting the sync task."""
        with patch.object(task, "_run_sync_loop", new=AsyncMock()) as mock_run:
            await task.start()

            assert task.is_running is True
            assert task._task is not None
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_task_already_running(self, task):
        """Test starting the task when it's already running."""
        task.is_running = True

        with patch.object(task, "_run_sync_loop", new=AsyncMock()) as mock_run:
            await task.start()

            # Should not create a new task
            mock_run.assert_not_called()
            assert task._task is None

    @pytest.mark.asyncio
    async def test_stop_task(self, task):
        """Test stopping the sync task."""

        # Create a real asyncio Task that we can cancel
        async def dummy_coro():
            try:
                await asyncio.sleep(10)  # Long sleep that will be cancelled
            except asyncio.CancelledError:
                pass  # Expected when cancelled

        # Properly create and assign the task
        task._task = asyncio.create_task(dummy_coro())
        task.is_running = True

        await task.stop()

        assert task.is_running is False
        assert task._task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_task_no_task(self, task):
        """Test stopping when no task is running."""
        task.is_running = True
        task._task = None

        await task.stop()

        assert task.is_running is False

    @pytest.mark.asyncio
    async def test_sync_once_success(
        self, task, mock_model_sync_service, mock_get_sync_session
    ):
        """Test successful sync operation."""
        with patch("app.tasks.model_sync_task.get_sync_session", mock_get_sync_session):
            with patch(
                "app.tasks.model_sync_task.model_sync_service", mock_model_sync_service
            ):
                await task._sync_once()

                mock_model_sync_service.sync_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_once_exception(self, task, mock_get_sync_session):
        """Test sync operation with exception."""
        mock_get_sync_session.side_effect = Exception("Sync failed")

        with patch("app.tasks.model_sync_task.get_sync_session", mock_get_sync_session):
            # Should not raise exception
            await task._sync_once()

    @pytest.mark.asyncio
    async def test_sync_now(self, task, mock_model_sync_service, mock_get_sync_session):
        """Test immediate sync trigger."""
        with patch("app.tasks.model_sync_task.get_sync_session", mock_get_sync_session):
            with patch(
                "app.tasks.model_sync_task.model_sync_service", mock_model_sync_service
            ):
                await task.sync_now()

                mock_model_sync_service.sync_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_sync_loop_single_iteration(
        self, task, mock_model_sync_service, mock_get_sync_session
    ):
        """Test sync loop runs initial sync and stops."""
        with patch("app.tasks.model_sync_task.get_sync_session", mock_get_sync_session):
            with patch(
                "app.tasks.model_sync_task.model_sync_service", mock_model_sync_service
            ):
                with patch("asyncio.sleep", side_effect=asyncio.CancelledError()):
                    task.is_running = True

                    # Should not raise exception
                    await task._run_sync_loop()

                    # Initial sync should have been called
                    mock_model_sync_service.sync_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_sync_loop_with_exception(self, task, mock_get_sync_session):
        """Test sync loop continues after exception."""
        mock_get_sync_session.side_effect = [
            Exception("First fail"),
            Exception("Second fail"),
        ]

        call_count = 0

        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError()

        with patch("app.tasks.model_sync_task.get_sync_session", mock_get_sync_session):
            with patch("asyncio.sleep", side_effect=mock_sleep):
                task.is_running = True

                # Should not raise exception
                await task._run_sync_loop()

                # Should have attempted sync multiple times
                assert mock_get_sync_session.call_count >= 2

    @pytest.mark.asyncio
    async def test_run_sync_loop_stops_when_not_running(
        self, task, mock_model_sync_service, mock_get_sync_session
    ):
        """Test sync loop stops when is_running becomes False."""
        call_count = 0

        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                task.is_running = False  # Stop after first iteration

        with patch("app.tasks.model_sync_task.get_sync_session", mock_get_sync_session):
            with patch(
                "app.tasks.model_sync_task.model_sync_service", mock_model_sync_service
            ):
                with patch("asyncio.sleep", side_effect=mock_sleep):
                    task.is_running = True

                    await task._run_sync_loop()

                    # Should have called initial sync plus one iteration
                    assert mock_model_sync_service.sync_models.call_count >= 1

    def test_global_instance_exists(self):
        """Test that the global instance exists."""
        assert model_sync_task is not None
        assert isinstance(model_sync_task, ModelSyncTask)

    def test_default_sync_interval(self):
        """Test default sync interval."""
        task = ModelSyncTask()
        assert task.sync_interval == timedelta(minutes=60)
