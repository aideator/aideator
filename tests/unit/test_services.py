import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_orchestrator import AgentOrchestrator
from app.services.sse_manager import EventType, SSEEvent, SSEManager


class TestSSEManager:
    """Test SSE manager functionality."""

    @pytest.mark.asyncio
    async def test_sse_event_formatting(self):
        """Test SSE event formatting."""
        event = SSEEvent(
            event_type=EventType.AGENT_OUTPUT,
            data={"variation_id": 0, "content": "Test output"},
            id="123",
            retry=3000,
        )
        
        formatted = event.format()
        assert "id: 123" in formatted
        assert "event: agent_output" in formatted
        assert "retry: 3000" in formatted
        assert '"variation_id": 0' in formatted

    @pytest.mark.asyncio
    async def test_sse_manager_broadcast(self, sse_manager):
        """Test broadcasting events to connected clients."""
        run_id = "test_run"
        
        # Create a connection
        connection_task = asyncio.create_task(
            sse_manager.connect(run_id).__anext__()
        )
        
        # Give connection time to establish
        await asyncio.sleep(0.1)
        
        # Send an event
        await sse_manager.send_agent_output(run_id, 0, "Test output")
        
        # Get the event
        event_data = await connection_task
        assert "agent_output" in event_data
        assert "Test output" in event_data

    @pytest.mark.asyncio
    async def test_sse_manager_multiple_connections(self, sse_manager):
        """Test multiple clients receiving broadcasts."""
        run_id = "test_run"
        events_received = []
        
        async def client_connection(client_id: int):
            """Simulate a client connection."""
            async for event in sse_manager.connect(run_id):
                if "agent_output" in event:
                    events_received.append((client_id, event))
                    break
        
        # Start multiple clients
        tasks = [
            asyncio.create_task(client_connection(i))
            for i in range(3)
        ]
        
        # Give connections time to establish
        await asyncio.sleep(0.1)
        
        # Broadcast event
        await sse_manager.send_agent_output(run_id, 0, "Broadcast test")
        
        # Wait for clients to receive
        await asyncio.gather(*tasks)
        
        # Verify all clients received the event
        assert len(events_received) == 3
        for client_id, event in events_received:
            assert "Broadcast test" in event

    @pytest.mark.asyncio
    async def test_sse_heartbeat(self, sse_manager):
        """Test heartbeat functionality."""
        # Mock settings for faster heartbeat
        with patch("app.services.sse_manager.settings.sse_ping_interval", 0.1):
            run_id = "test_run"
            heartbeats = []
            
            async for event in sse_manager.connect(run_id):
                if "heartbeat" in event:
                    heartbeats.append(event)
                if len(heartbeats) >= 2:
                    break
            
            assert len(heartbeats) >= 2


class TestAgentOrchestrator:
    """Test agent orchestrator functionality."""

    @pytest.mark.asyncio
    async def test_execute_variations(self, mock_dagger_service):
        """Test executing multiple agent variations."""
        orchestrator = AgentOrchestrator(mock_dagger_service)
        
        # Mock SSE manager
        with patch("app.services.agent_orchestrator.sse_manager") as mock_sse:
            mock_sse.send_agent_output = AsyncMock()
            mock_sse.send_agent_complete = AsyncMock()
            mock_sse.send_run_complete = AsyncMock()
            
            await orchestrator.execute_variations(
                run_id="test_run",
                repo_url="https://github.com/test/repo",
                prompt="Test prompt",
                variations=3,
            )
            
            # Verify agents were executed
            assert mock_sse.send_agent_output.call_count > 0
            assert mock_sse.send_agent_complete.call_count == 3
            assert mock_sse.send_run_complete.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_single_agent_success(self, mock_dagger_service):
        """Test successful single agent execution."""
        orchestrator = AgentOrchestrator(mock_dagger_service)
        
        with patch("app.services.agent_orchestrator.sse_manager") as mock_sse:
            mock_sse.send_agent_output = AsyncMock()
            mock_sse.send_agent_complete = AsyncMock()
            
            await orchestrator._execute_single_agent(
                run_id="test_run",
                repo_url="https://github.com/test/repo",
                prompt="Test prompt",
                variation_id=0,
            )
            
            # Verify output was sent
            assert mock_sse.send_agent_output.call_count == 5  # Mock produces 5 lines
            mock_sse.send_agent_complete.assert_called_once_with("test_run", 0)

    @pytest.mark.asyncio
    async def test_execute_single_agent_error(self, mock_dagger_service):
        """Test agent execution with error."""
        orchestrator = AgentOrchestrator(mock_dagger_service)
        
        # Make execute_container raise an error
        mock_dagger_service.execute_container = AsyncMock(
            side_effect=Exception("Container failed")
        )
        
        with patch("app.services.agent_orchestrator.sse_manager") as mock_sse:
            mock_sse.send_agent_error = AsyncMock()
            
            with pytest.raises(Exception):
                await orchestrator._execute_single_agent(
                    run_id="test_run",
                    repo_url="https://github.com/test/repo",
                    prompt="Test prompt",
                    variation_id=0,
                )
            
            mock_sse.send_agent_error.assert_called_once()