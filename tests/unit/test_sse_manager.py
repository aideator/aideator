"""
Unit Tests for SSE Manager

This test suite covers the Server-Sent Events manager
to increase test coverage for app/services/sse_manager.py
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.sse_manager import SSEManager, SSEEvent


class TestSSEEvent:
    """Test SSEEvent dataclass."""
    
    def test_sse_event_creation(self):
        """Test creating SSE event."""
        event = SSEEvent(
            event="test_event",
            data={"message": "Hello"},
            id="event-123",
            retry=5000
        )
        
        assert event.event == "test_event"
        assert event.data == {"message": "Hello"}
        assert event.id == "event-123"
        assert event.retry == 5000
    
    def test_sse_event_format_full(self):
        """Test formatting SSE event with all fields."""
        event = SSEEvent(
            event="message",
            data={"text": "Hello World"},
            id="msg-001",
            retry=3000
        )
        
        formatted = event.format()
        
        # Should contain all fields
        assert "event: message\n" in formatted
        assert 'data: {"text": "Hello World"}\n' in formatted
        assert "id: msg-001\n" in formatted
        assert "retry: 3000\n" in formatted
        assert formatted.endswith("\n\n")
    
    def test_sse_event_format_minimal(self):
        """Test formatting SSE event with minimal fields."""
        event = SSEEvent(data={"status": "ok"})
        
        formatted = event.format()
        
        # Should only have data field
        assert formatted == 'data: {"status": "ok"}\n\n'
    
    def test_sse_event_format_string_data(self):
        """Test formatting SSE event with string data."""
        event = SSEEvent(data="Simple message")
        
        formatted = event.format()
        
        assert formatted == 'data: "Simple message"\n\n'


class TestSSEManager:
    """Test SSEManager class."""
    
    @pytest.fixture
    def sse_manager(self):
        """Create SSE manager instance."""
        return SSEManager()
    
    @pytest.mark.asyncio
    async def test_connect_new_run(self, sse_manager):
        """Test connecting to a new run."""
        run_id = "run-123"
        
        # Start connection
        connection = sse_manager.connect(run_id)
        
        # Should yield initial connection event
        event = await anext(connection)
        assert "event: connected" in event
        assert f'"run_id": "{run_id}"' in event
        
        # Run should be in active connections
        assert run_id in sse_manager._connections
        assert len(sse_manager._connections[run_id]) == 1
    
    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self, sse_manager):
        """Test multiple clients connecting to same run."""
        run_id = "run-456"
        
        # Create two connections
        conn1 = sse_manager.connect(run_id)
        conn2 = sse_manager.connect(run_id)
        
        # Get initial events
        event1 = await anext(conn1)
        event2 = await anext(conn2)
        
        assert "connected" in event1
        assert "connected" in event2
        
        # Should have 2 connections for this run
        assert len(sse_manager._connections[run_id]) == 2
    
    @pytest.mark.asyncio
    async def test_send_agent_output(self, sse_manager):
        """Test sending agent output to connected clients."""
        run_id = "run-789"
        
        # Connect a client
        connection = sse_manager.connect(run_id)
        await anext(connection)  # Skip connection event
        
        # Send agent output
        await sse_manager.send_agent_output(
            run_id=run_id,
            variation_id=0,
            content="Processing repository..."
        )
        
        # Should receive the output
        event = await anext(connection)
        assert "event: agent_output" in event
        data = json.loads(event.split("data: ")[1].split("\n")[0])
        assert data["variation_id"] == 0
        assert data["content"] == "Processing repository..."
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_send_agent_error(self, sse_manager):
        """Test sending agent error to connected clients."""
        run_id = "run-error"
        
        # Connect a client
        connection = sse_manager.connect(run_id)
        await anext(connection)  # Skip connection event
        
        # Send agent error
        await sse_manager.send_agent_error(
            run_id=run_id,
            variation_id=1,
            error="Failed to clone repository"
        )
        
        # Should receive the error
        event = await anext(connection)
        assert "event: agent_error" in event
        data = json.loads(event.split("data: ")[1].split("\n")[0])
        assert data["variation_id"] == 1
        assert data["error"] == "Failed to clone repository"
    
    @pytest.mark.asyncio
    async def test_send_agent_complete(self, sse_manager):
        """Test sending agent completion event."""
        run_id = "run-complete"
        
        # Connect a client
        connection = sse_manager.connect(run_id)
        await anext(connection)  # Skip connection event
        
        # Send agent complete
        await sse_manager.send_agent_complete(
            run_id=run_id,
            variation_id=2
        )
        
        # Should receive completion event
        event = await anext(connection)
        assert "event: agent_complete" in event
        data = json.loads(event.split("data: ")[1].split("\n")[0])
        assert data["variation_id"] == 2
        assert data["status"] == "complete"
    
    @pytest.mark.asyncio
    async def test_send_run_complete(self, sse_manager):
        """Test sending run completion event."""
        run_id = "run-done"
        
        # Connect a client
        connection = sse_manager.connect(run_id)
        await anext(connection)  # Skip connection event
        
        # Send run complete
        await sse_manager.send_run_complete(run_id)
        
        # Should receive run completion event
        event = await anext(connection)
        assert "event: run_complete" in event
        data = json.loads(event.split("data: ")[1].split("\n")[0])
        assert data["status"] == "complete"
    
    @pytest.mark.asyncio
    async def test_send_to_no_connections(self, sse_manager):
        """Test sending events when no clients are connected."""
        run_id = "run-no-clients"
        
        # Send events without any connections
        await sse_manager.send_agent_output(run_id, 0, "Test")
        await sse_manager.send_agent_error(run_id, 0, "Error")
        await sse_manager.send_agent_complete(run_id, 0)
        await sse_manager.send_run_complete(run_id)
        
        # Should not raise any errors
        assert run_id not in sse_manager._connections
    
    @pytest.mark.asyncio
    async def test_connection_cleanup_on_disconnect(self, sse_manager):
        """Test that connections are cleaned up when client disconnects."""
        run_id = "run-cleanup"
        
        # Connect a client
        connection = sse_manager.connect(run_id)
        await anext(connection)  # Skip connection event
        
        # Verify connection exists
        assert len(sse_manager._connections[run_id]) == 1
        
        # Close the connection
        await connection.aclose()
        
        # Send an event to trigger cleanup
        await sse_manager.send_agent_output(run_id, 0, "Test")
        
        # Connection should be cleaned up
        assert run_id not in sse_manager._connections or len(sse_manager._connections[run_id]) == 0
    
    @pytest.mark.asyncio
    async def test_heartbeat_functionality(self, sse_manager):
        """Test heartbeat events."""
        run_id = "run-heartbeat"
        
        # Connect with short heartbeat interval
        sse_manager._heartbeat_interval = 0.1  # 100ms for testing
        connection = sse_manager.connect(run_id)
        
        # Get initial connection event
        event1 = await anext(connection)
        assert "connected" in event1
        
        # Wait for heartbeat
        await asyncio.sleep(0.15)
        
        # Should receive heartbeat
        event2 = await anext(connection)
        assert "event: heartbeat" in event2
    
    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self, sse_manager):
        """Test broadcasting to multiple connected clients."""
        run_id = "run-broadcast"
        
        # Connect multiple clients
        connections = []
        for i in range(3):
            conn = sse_manager.connect(run_id)
            await anext(conn)  # Skip connection event
            connections.append(conn)
        
        # Send an event
        await sse_manager.send_agent_output(run_id, 0, "Broadcast message")
        
        # All clients should receive the message
        for conn in connections:
            event = await anext(conn)
            assert "agent_output" in event
            assert "Broadcast message" in event
    
    def test_get_active_connections(self, sse_manager):
        """Test getting count of active connections."""
        # Initially no connections
        assert sse_manager.get_active_connections() == 0
        
        # Add some connections
        sse_manager._connections["run1"] = [MagicMock(), MagicMock()]
        sse_manager._connections["run2"] = [MagicMock()]
        
        # Should count all connections
        assert sse_manager.get_active_connections() == 3
    
    def test_get_run_connections(self, sse_manager):
        """Test getting connections for specific run."""
        # No connections for run
        assert sse_manager.get_run_connections("run-none") == 0
        
        # Add connections
        sse_manager._connections["run-test"] = [MagicMock(), MagicMock(), MagicMock()]
        
        # Should return count for specific run
        assert sse_manager.get_run_connections("run-test") == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])