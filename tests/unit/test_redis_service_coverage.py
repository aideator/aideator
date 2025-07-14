"""Tests for RedisService to improve coverage."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.redis_service import RedisService


class TestRedisServiceCoverage:
    """Test RedisService methods for coverage."""

    @pytest.fixture
    def service(self):
        """Create RedisService instance."""
        return RedisService()

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        return AsyncMock()

    def test_init(self):
        """Test service initialization."""
        service = RedisService()
        assert service.redis_url is not None
        assert service._client is None

    @patch("app.services.redis_service.redis.from_url")
    async def test_connect_success(self, mock_from_url, service):
        """Test successful Redis connection."""
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True

        await service.connect()

        assert service._client == mock_client
        mock_client.ping.assert_called_once()

    @patch("app.services.redis_service.redis.from_url")
    async def test_connect_failure(self, mock_from_url, service):
        """Test Redis connection failure."""
        mock_from_url.side_effect = Exception("Connection failed")

        # Should raise the exception
        with pytest.raises(Exception, match="Connection failed"):
            await service.connect()

        assert service._client is None

    async def test_disconnect(self, service, mock_redis_client):
        """Test Redis disconnection."""
        service._client = mock_redis_client

        await service.disconnect()

        mock_redis_client.close.assert_called_once()
        # _client is NOT set to None in the actual implementation

    async def test_disconnect_no_client(self, service):
        """Test disconnect when no client exists."""
        service._client = None

        # Should not raise exception
        await service.disconnect()

    async def test_health_check_success(self, service, mock_redis_client):
        """Test successful health check."""
        service._client = mock_redis_client
        mock_redis_client.ping.return_value = True

        result = await service.health_check()

        assert result is True
        mock_redis_client.ping.assert_called_once()

    async def test_health_check_no_client(self, service):
        """Test health check with no client."""
        service._client = None

        # Should return False since health_check catches the exception
        result = await service.health_check()
        assert result is False

    async def test_health_check_ping_fails(self, service, mock_redis_client):
        """Test health check when ping fails."""
        service._client = mock_redis_client
        mock_redis_client.ping.side_effect = Exception("Ping failed")

        result = await service.health_check()

        assert result is False

    async def test_add_llm_output(self, service, mock_redis_client):
        """Test adding LLM output to stream."""
        service._client = mock_redis_client

        await service.add_llm_output("run-123", "0", "Hello world", {"tokens": 50})

        # Should call xadd with correct stream and data
        mock_redis_client.xadd.assert_called_once()
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:run-123:llm"
        assert "content" in call_args[0][1]
        assert call_args[0][1]["content"] == "Hello world"

    async def test_add_stdout_log(self, service, mock_redis_client):
        """Test adding stdout log to stream."""
        service._client = mock_redis_client

        await service.add_stdout_log("run-456", "1", "Debug message", "INFO")

        mock_redis_client.xadd.assert_called_once()
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:run-456:stdout"
        assert call_args[0][1]["content"] == "Debug message"
        assert call_args[0][1]["level"] == "INFO"

    async def test_add_status_update(self, service, mock_redis_client):
        """Test adding status update to stream."""
        service._client = mock_redis_client

        await service.add_status_update("run-789", "completed", {"job_count": 3})

        mock_redis_client.xadd.assert_called_once()
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:run-789:status"
        assert call_args[0][1]["status"] == "completed"

    async def test_trim_streams(self, service, mock_redis_client):
        """Test trimming streams."""
        service._client = mock_redis_client

        await service.trim_streams("run-123", max_length=500)

        # Should call xtrim for each stream
        assert mock_redis_client.xtrim.call_count == 4

    async def test_delete_run_streams(self, service, mock_redis_client):
        """Test deleting run streams."""
        service._client = mock_redis_client

        await service.delete_run_streams("run-456")

        # Should call delete for each stream
        assert mock_redis_client.delete.call_count == 4

    async def test_read_run_streams_no_client(self, service):
        """Test reading streams with no Redis client."""
        service._client = None

        # Should raise RuntimeError since client property raises when None
        with pytest.raises(RuntimeError, match="Redis not connected"):
            async for _ in service.read_run_streams("run-123", {}):
                break

    async def test_read_run_streams_with_data(self, service, mock_redis_client):
        """Test reading streams with data."""
        service._client = mock_redis_client

        # Mock xread response - returns list of tuples
        mock_redis_client.xread.return_value = [
            (
                "run:run-123:llm",
                [
                    (
                        "123-0",
                        {
                            "content": "Hello",
                            "variation_id": "0",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "metadata": "{}",
                        },
                    )
                ],
            )
        ]

        messages = []
        count = 0
        async for msg in service.read_run_streams("run-123", {}):
            messages.append(msg)
            count += 1
            if count >= 1:  # Only test one iteration
                break

        assert len(messages) == 1
        assert messages[0]["type"] == "llm"
        assert messages[0]["data"]["content"] == "Hello"

    async def test_read_run_streams_exception(self, service, mock_redis_client):
        """Test reading streams with exception."""
        service._client = mock_redis_client
        mock_redis_client.xread.side_effect = Exception("Read failed")

        # Should raise the exception
        with pytest.raises(Exception, match="Read failed"):
            async for _ in service.read_run_streams("run-123", {}):
                break

    async def test_get_stream_info(self, service, mock_redis_client):
        """Test getting stream info."""
        service._client = mock_redis_client
        mock_redis_client.xinfo_stream.return_value = {
            "length": 5,
            "first-entry": ["123-0", {"content": "first"}],
            "last-entry": ["456-0", {"content": "last"}],
        }

        result = await service.get_stream_info("run-123")

        assert "run:run-123:llm" in result
        assert result["run:run-123:llm"]["length"] == 5
        mock_redis_client.xinfo_stream.assert_called()

    async def test_get_stream_info_no_client(self, service):
        """Test getting stream info with no client."""
        service._client = None

        # Should handle the exception and return error info
        result = await service.get_stream_info("run-123")

        # All streams should have error info
        for stream_name in [
            "run:run-123:llm",
            "run:run-123:stdout",
            "run:run-123:status",
        ]:
            assert stream_name in result
            assert result[stream_name]["length"] == 0
            assert "error" in result[stream_name]

    async def test_get_stream_info_exception(self, service, mock_redis_client):
        """Test getting stream info with exception."""
        service._client = mock_redis_client
        mock_redis_client.xinfo_stream.side_effect = Exception("Stream not found")

        result = await service.get_stream_info("run-123")

        # Should handle exceptions gracefully and include error info
        assert "run:run-123:llm" in result
        assert result["run:run-123:llm"]["length"] == 0
        assert "error" in result["run:run-123:llm"]

    async def test_trim_streams_exception(self, service, mock_redis_client):
        """Test trimming streams with exception."""
        service._client = mock_redis_client
        mock_redis_client.xtrim.side_effect = Exception("Trim failed")

        # Should handle exceptions gracefully - doesn't raise
        await service.trim_streams("run-123")

        # Should still try to trim all streams despite exceptions
        assert mock_redis_client.xtrim.call_count == 4

    async def test_delete_run_streams_exception(self, service, mock_redis_client):
        """Test deleting run streams with exception."""
        service._client = mock_redis_client
        mock_redis_client.delete.side_effect = Exception("Delete failed")

        # Should handle exceptions gracefully - doesn't raise
        await service.delete_run_streams("run-456")

        # Should still try to delete all streams despite exceptions
        assert mock_redis_client.delete.call_count == 4
