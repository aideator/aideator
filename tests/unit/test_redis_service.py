"""Tests for Redis service."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis
from redis.exceptions import ConnectionError, ResponseError

from app.core.config import get_settings
from app.services.redis_service import RedisService

settings = get_settings()


class TestRedisService:
    """Test the Redis service."""

    @pytest.fixture
    def service(self):
        """Create a Redis service instance."""
        return RedisService()

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        client = AsyncMock(spec=redis.Redis)
        client.ping = AsyncMock()
        client.close = AsyncMock()
        client.xadd = AsyncMock(return_value="1234567890-0")
        client.xread = AsyncMock(return_value=[])
        client.xtrim = AsyncMock()
        client.delete = AsyncMock()
        client.xinfo_stream = AsyncMock()
        return client

    def test_init(self, service):
        """Test service initialization."""
        # In test environment, conftest.py sets REDIS_URL to redis://localhost:6379/1
        # But if settings.redis_url is None, it defaults to redis://localhost:6379/0
        expected_url = settings.redis_url or "redis://localhost:6379/0"
        assert service.redis_url == expected_url
        assert service._client is None

    @pytest.mark.asyncio
    async def test_connect_success(self, service):
        """Test successful Redis connection."""
        with patch("app.services.redis_service.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_from_url.return_value = mock_client

            await service.connect()

            assert service._client == mock_client
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, service):
        """Test Redis connection failure."""
        with patch("app.services.redis_service.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(
                side_effect=ConnectionError("Connection failed")
            )
            mock_from_url.return_value = mock_client

            with pytest.raises(ConnectionError):
                await service.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, service, mock_redis_client):
        """Test Redis disconnection."""
        service._client = mock_redis_client

        await service.disconnect()

        mock_redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self, service):
        """Test disconnect when no client exists."""
        # Should not raise error
        await service.disconnect()

    def test_client_property_not_connected(self, service):
        """Test client property when not connected."""
        with pytest.raises(RuntimeError, match="Redis not connected"):
            _ = service.client

    def test_client_property_connected(self, service, mock_redis_client):
        """Test client property when connected."""
        service._client = mock_redis_client
        assert service.client == mock_redis_client

    @pytest.mark.asyncio
    async def test_add_llm_output(self, service, mock_redis_client):
        """Test adding LLM output to stream."""
        service._client = mock_redis_client

        result = await service.add_llm_output(
            run_id="test-run",
            variation_id="0",
            content="Test LLM output",
            metadata={"tokens": 100, "model": "gpt-4"},
        )

        assert result == "1234567890-0"
        mock_redis_client.xadd.assert_called_once()

        # Verify the stream name and fields
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:test-run:llm"
        fields = call_args[0][1]
        assert fields["variation_id"] == "0"
        assert fields["content"] == "Test LLM output"
        assert "timestamp" in fields
        assert json.loads(fields["metadata"]) == {"tokens": 100, "model": "gpt-4"}

    @pytest.mark.asyncio
    async def test_add_llm_output_no_metadata(self, service, mock_redis_client):
        """Test adding LLM output without metadata."""
        service._client = mock_redis_client

        result = await service.add_llm_output(
            run_id="test-run", variation_id="1", content="Simple output"
        )

        assert result == "1234567890-0"
        call_args = mock_redis_client.xadd.call_args
        fields = call_args[0][1]
        assert json.loads(fields["metadata"]) == {}

    @pytest.mark.asyncio
    async def test_add_stdout_log(self, service, mock_redis_client):
        """Test adding stdout log to stream."""
        service._client = mock_redis_client

        result = await service.add_stdout_log(
            run_id="test-run", variation_id="0", log_line="Debug message", level="DEBUG"
        )

        assert result == "1234567890-0"
        mock_redis_client.xadd.assert_called_once()

        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:test-run:stdout"
        fields = call_args[0][1]
        assert fields["variation_id"] == "0"
        assert fields["content"] == "Debug message"
        assert fields["level"] == "DEBUG"
        assert "timestamp" in fields

    @pytest.mark.asyncio
    async def test_add_stdout_log_default_level(self, service, mock_redis_client):
        """Test adding stdout log with default level."""
        service._client = mock_redis_client

        await service.add_stdout_log(
            run_id="test-run", variation_id="1", log_line="Info message"
        )

        call_args = mock_redis_client.xadd.call_args
        fields = call_args[0][1]
        assert fields["level"] == "INFO"

    @pytest.mark.asyncio
    async def test_add_status_update(self, service, mock_redis_client):
        """Test adding status update to stream."""
        service._client = mock_redis_client

        result = await service.add_status_update(
            run_id="test-run", status="completed", metadata={"duration": 120, "jobs": 3}
        )

        assert result == "1234567890-0"
        mock_redis_client.xadd.assert_called_once()

        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:test-run:status"
        fields = call_args[0][1]
        assert fields["status"] == "completed"
        assert "timestamp" in fields
        assert json.loads(fields["metadata"]) == {"duration": 120, "jobs": 3}

    @pytest.mark.skip(reason="Async generator tests need refactoring")
    @pytest.mark.asyncio
    async def test_read_run_streams_no_messages(self, service, mock_redis_client):
        """Test reading from streams when no messages."""
        service._client = mock_redis_client

        # First call returns empty, second call raises to exit the loop
        mock_redis_client.xread.side_effect = [[], asyncio.CancelledError()]

        messages = []
        try:
            async for msg in service.read_run_streams("test-run", block=100):
                messages.append(msg)
        except asyncio.CancelledError:
            pass  # Expected

        assert len(messages) == 0
        assert mock_redis_client.xread.call_count >= 1

    @pytest.mark.skip(reason="Async generator tests need refactoring")
    @pytest.mark.asyncio
    async def test_read_run_streams_with_messages(self, service, mock_redis_client):
        """Test reading from streams with messages."""
        service._client = mock_redis_client

        # Mock stream messages
        mock_messages = [
            (
                "run:test-run:llm",
                [
                    (
                        "123-0",
                        {
                            "variation_id": "0",
                            "content": "LLM output",
                            "timestamp": "2024-01-01T00:00:00",
                            "metadata": '{"tokens": 50}',
                        },
                    )
                ],
            ),
            (
                "run:test-run:status",
                [
                    (
                        "124-0",
                        {
                            "status": "running",
                            "timestamp": "2024-01-01T00:00:01",
                            "metadata": "{}",
                        },
                    )
                ],
            ),
        ]

        mock_redis_client.xread.side_effect = [
            mock_messages,
            [],
        ]  # Return messages then empty

        messages = []
        async for msg in service.read_run_streams("test-run"):
            messages.append(msg)
            if len(messages) >= 2:  # Stop after 2 messages
                break

        assert len(messages) == 2

        # Check first message (LLM)
        assert messages[0]["type"] == "llm"
        assert messages[0]["message_id"] == "123-0"
        assert messages[0]["data"]["content"] == "LLM output"
        assert messages[0]["data"]["metadata"] == {"tokens": 50}

        # Check second message (status)
        assert messages[1]["type"] == "status"
        assert messages[1]["message_id"] == "124-0"
        assert messages[1]["data"]["status"] == "running"

    @pytest.mark.skip(reason="Async generator tests need refactoring")
    @pytest.mark.asyncio
    async def test_read_run_streams_with_last_ids(self, service, mock_redis_client):
        """Test reading from streams with last IDs for resuming."""
        service._client = mock_redis_client
        mock_redis_client.xread.return_value = []

        last_ids = {"llm": "100-0", "stdout": "101-0", "status": "102-0"}

        messages = []
        async for msg in service.read_run_streams("test-run", last_ids=last_ids):
            messages.append(msg)
            break

        # Check that xread was called with correct last IDs
        call_args = mock_redis_client.xread.call_args
        streams = call_args[0][0]
        assert streams["run:test-run:llm"] == "100-0"
        assert streams["run:test-run:stdout"] == "101-0"
        assert streams["run:test-run:status"] == "102-0"

    @pytest.mark.skip(reason="Async generator tests need refactoring")
    @pytest.mark.asyncio
    async def test_read_run_streams_json_decode_error(self, service, mock_redis_client):
        """Test reading streams with invalid JSON metadata."""
        service._client = mock_redis_client

        mock_messages = [
            (
                "run:test-run:llm",
                [
                    (
                        "123-0",
                        {
                            "variation_id": "0",
                            "content": "output",
                            "timestamp": "2024-01-01T00:00:00",
                            "metadata": "invalid-json",  # Invalid JSON
                        },
                    )
                ],
            )
        ]

        mock_redis_client.xread.side_effect = [mock_messages, []]

        messages = []
        async for msg in service.read_run_streams("test-run"):
            messages.append(msg)
            break

        # Should still process message, keeping metadata as string
        assert len(messages) == 1
        assert messages[0]["data"]["metadata"] == "invalid-json"

    @pytest.mark.skip(reason="Async generator tests need refactoring")
    @pytest.mark.asyncio
    async def test_read_run_streams_error(self, service, mock_redis_client):
        """Test read streams error handling."""
        service._client = mock_redis_client
        mock_redis_client.xread.side_effect = Exception("Redis error")

        with pytest.raises(Exception, match="Redis error"):
            async for _ in service.read_run_streams("test-run"):
                pass

    @pytest.mark.asyncio
    async def test_trim_streams(self, service, mock_redis_client):
        """Test trimming streams."""
        service._client = mock_redis_client

        await service.trim_streams("test-run", max_length=500)

        assert mock_redis_client.xtrim.call_count == 3
        expected_streams = [
            "run:test-run:llm",
            "run:test-run:stdout",
            "run:test-run:status",
        ]

        for i, call in enumerate(mock_redis_client.xtrim.call_args_list):
            assert call[0][0] == expected_streams[i]
            assert call[1]["maxlen"] == 500

    @pytest.mark.asyncio
    async def test_trim_streams_error(self, service, mock_redis_client):
        """Test trim streams error handling."""
        service._client = mock_redis_client
        mock_redis_client.xtrim.side_effect = Exception("Trim error")

        # Should not raise, just log warning
        await service.trim_streams("test-run")

    @pytest.mark.asyncio
    async def test_delete_run_streams(self, service, mock_redis_client):
        """Test deleting run streams."""
        service._client = mock_redis_client

        await service.delete_run_streams("test-run")

        assert mock_redis_client.delete.call_count == 3
        expected_streams = [
            "run:test-run:llm",
            "run:test-run:stdout",
            "run:test-run:status",
        ]

        for i, call in enumerate(mock_redis_client.delete.call_args_list):
            assert call[0][0] == expected_streams[i]

    @pytest.mark.asyncio
    async def test_delete_run_streams_error(self, service, mock_redis_client):
        """Test delete streams error handling."""
        service._client = mock_redis_client
        mock_redis_client.delete.side_effect = Exception("Delete error")

        # Should not raise, just log warning
        await service.delete_run_streams("test-run")

    @pytest.mark.asyncio
    async def test_get_stream_info_success(self, service, mock_redis_client):
        """Test getting stream information."""
        service._client = mock_redis_client

        # Mock stream info responses
        mock_redis_client.xinfo_stream.side_effect = [
            {
                "length": 100,
                "first-entry": ["123-0", {"content": "first"}],
                "last-entry": ["223-0", {"content": "last"}],
            },
            {
                "length": 50,
                "first-entry": ["124-0", {"log": "first log"}],
                "last-entry": ["174-0", {"log": "last log"}],
            },
            {
                "length": 10,
                "first-entry": ["125-0", {"status": "running"}],
                "last-entry": ["135-0", {"status": "completed"}],
            },
        ]

        result = await service.get_stream_info("test-run")

        assert len(result) == 3
        assert result["run:test-run:llm"]["length"] == 100
        assert result["run:test-run:stdout"]["length"] == 50
        assert result["run:test-run:status"]["length"] == 10

    @pytest.mark.asyncio
    async def test_get_stream_info_error(self, service, mock_redis_client):
        """Test get stream info error handling."""
        service._client = mock_redis_client
        mock_redis_client.xinfo_stream.side_effect = ResponseError("no such key")

        result = await service.get_stream_info("test-run")

        # Should return error info for all streams
        for stream_name in result:
            assert result[stream_name]["length"] == 0
            assert "error" in result[stream_name]

    @pytest.mark.asyncio
    async def test_health_check_success(self, service, mock_redis_client):
        """Test successful health check."""
        service._client = mock_redis_client
        mock_redis_client.ping = AsyncMock()

        result = await service.health_check()

        assert result is True
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, service, mock_redis_client):
        """Test failed health check."""
        service._client = mock_redis_client
        mock_redis_client.ping = AsyncMock(
            side_effect=ConnectionError("Connection lost")
        )

        result = await service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_no_client(self, service):
        """Test health check when client not initialized."""
        result = await service.health_check()
        assert result is False

    def test_redis_url_from_settings(self):
        """Test Redis URL configuration from settings."""
        with patch("app.services.redis_service.settings") as mock_settings:
            mock_settings.redis_url = "redis://custom:6380/1"
            mock_settings.redis_password = "secret"
            mock_settings.redis_db = 1
            mock_settings.redis_decode_responses = False

            service = RedisService()
            assert service.redis_url == "redis://custom:6380/1"

    @pytest.mark.asyncio
    async def test_connect_with_custom_settings(self, service):
        """Test connection with custom Redis settings."""
        with patch("app.services.redis_service.redis.from_url") as mock_from_url:
            with patch("app.services.redis_service.settings") as mock_settings:
                mock_settings.redis_password = "mypassword"
                mock_settings.redis_db = 2
                mock_settings.redis_decode_responses = False

                mock_client = AsyncMock()
                mock_from_url.return_value = mock_client

                await service.connect()

                mock_from_url.assert_called_once_with(
                    service.redis_url,
                    decode_responses=False,
                    password="mypassword",
                    db=2,
                )
