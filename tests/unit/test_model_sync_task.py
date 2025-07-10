"""
Test model sync background task.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import timedelta

from app.tasks.model_sync_task import ModelSyncTask
from app.models.model_definition import ModelSyncLog


class TestModelSyncTask:
    """Test cases for model sync background task."""
    
    @pytest.fixture
    def sync_task(self):
        """Create model sync task instance."""
        return ModelSyncTask(sync_interval_minutes=1)  # 1 minute for testing
    
    @pytest.mark.asyncio
    async def test_start_stop(self, sync_task):
        """Test starting and stopping the sync task."""
        # Mock the sync operation
        with patch.object(sync_task, '_sync_once', new_callable=AsyncMock) as mock_sync:
            # Start the task
            await sync_task.start()
            assert sync_task.is_running is True
            assert sync_task._task is not None
            
            # Wait a bit to ensure task is running
            await asyncio.sleep(0.1)
            
            # Stop the task
            await sync_task.stop()
            assert sync_task.is_running is False
            
            # Verify sync was called at least once (initial sync)
            assert mock_sync.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_start_already_running(self, sync_task):
        """Test starting when already running."""
        sync_task.is_running = True
        
        with patch('app.tasks.model_sync_task.logger') as mock_logger:
            await sync_task.start()
            mock_logger.warning.assert_called_with("Model sync task is already running")
    
    @pytest.mark.asyncio
    async def test_sync_loop_initial_sync(self, sync_task):
        """Test that sync runs immediately on start."""
        call_count = 0
        
        async def mock_sync():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                sync_task.is_running = False  # Stop after first sync
        
        sync_task._sync_once = mock_sync
        
        # Run the sync loop
        await sync_task._run_sync_loop()
        
        # Verify initial sync happened
        assert call_count >= 1
    
    @pytest.mark.asyncio
    async def test_sync_loop_error_handling(self, sync_task):
        """Test error handling in sync loop."""
        sync_task.sync_interval = timedelta(seconds=0.1)  # Fast interval for testing
        
        call_count = 0
        
        async def mock_sync():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Test error")
            else:
                sync_task.is_running = False  # Stop after second call
        
        sync_task._sync_once = mock_sync
        
        with patch('app.tasks.model_sync_task.logger') as mock_logger:
            # Run the sync loop
            await sync_task._run_sync_loop()
            
            # Verify error was logged but loop continued
            assert mock_logger.error.called
            assert call_count >= 2  # Should continue after error
    
    @pytest.mark.asyncio
    async def test_sync_once_success(self, sync_task):
        """Test successful single sync operation."""
        mock_sync_log = ModelSyncLog(
            status="success",
            models_discovered=10,
            models_added=5,
            models_updated=3,
            models_deactivated=2
        )
        
        with patch('app.tasks.model_sync_task.get_sync_session') as mock_get_session, \
             patch('app.tasks.model_sync_task.model_sync_service') as mock_service, \
             patch('app.tasks.model_sync_task.logger') as mock_logger:
            
            # Setup mocks
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])
            mock_service.sync_models = AsyncMock(return_value=mock_sync_log)
            
            # Run sync
            await sync_task._sync_once()
            
            # Verify
            mock_service.sync_models.assert_called_once_with(mock_session)
            mock_logger.info.assert_any_call("Starting model sync from LiteLLM proxy")
            mock_logger.info.assert_any_call(
                "Model sync completed: discovered=10, added=5, updated=3, deactivated=2"
            )
    
    @pytest.mark.asyncio
    async def test_sync_once_error(self, sync_task):
        """Test error handling in single sync."""
        with patch('app.tasks.model_sync_task.get_sync_session') as mock_get_session, \
             patch('app.tasks.model_sync_task.model_sync_service') as mock_service, \
             patch('app.tasks.model_sync_task.logger') as mock_logger:
            
            # Setup mocks to raise error
            mock_service.sync_models = AsyncMock(side_effect=Exception("Database error"))
            mock_get_session.return_value = iter([Mock()])
            
            # Run sync
            await sync_task._sync_once()
            
            # Verify error was logged
            mock_logger.error.assert_called_with("Model sync failed: Database error")
    
    @pytest.mark.asyncio
    async def test_sync_now(self, sync_task):
        """Test manual sync trigger."""
        with patch.object(sync_task, '_sync_once', new_callable=AsyncMock) as mock_sync:
            await sync_task.sync_now()
            mock_sync.assert_called_once()
    
    def test_sync_interval_configuration(self):
        """Test sync interval configuration."""
        # Test default
        task1 = ModelSyncTask()
        assert task1.sync_interval == timedelta(minutes=60)
        
        # Test custom interval
        task2 = ModelSyncTask(sync_interval_minutes=30)
        assert task2.sync_interval == timedelta(minutes=30)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])