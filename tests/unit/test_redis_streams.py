"""Tests for Redis Streams service."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.redis_service import RedisService


class TestRedisService:
    """Test Redis Streams service."""

    @pytest.fixture
    def redis_service(self):
        """Redis service instance."""
        return RedisService()

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_add_llm_output(self, redis_service, mock_redis_client):
        """Test adding LLM output to stream."""
        redis_service._client = mock_redis_client
        mock_redis_client.xadd.return_value = "123-0"

        result = await redis_service.add_llm_output(
            "run-123", "0", "Hello world", {"tokens": 10}
        )

        assert result == "123-0"
        mock_redis_client.xadd.assert_called_once()
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:run-123:llm"
        fields = call_args[0][1]
        assert fields["variation_id"] == "0"
        assert fields["content"] == "Hello world"
        assert json.loads(fields["metadata"]) == {"tokens": 10}

    @pytest.mark.asyncio
    async def test_add_stdout_log(self, redis_service, mock_redis_client):
        """Test adding stdout log to stream."""
        redis_service._client = mock_redis_client
        mock_redis_client.xadd.return_value = "124-0"

        result = await redis_service.add_stdout_log(
            "run-123", "0", "Debug message", "DEBUG"
        )

        assert result == "124-0"
        mock_redis_client.xadd.assert_called_once()
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:run-123:stdout"
        fields = call_args[0][1]
        assert fields["variation_id"] == "0"
        assert fields["content"] == "Debug message"
        assert fields["level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_add_status_update(self, redis_service, mock_redis_client):
        """Test adding status update to stream."""
        redis_service._client = mock_redis_client
        mock_redis_client.xadd.return_value = "125-0"

        result = await redis_service.add_status_update(
            "run-123", "completed", {"duration": 30}
        )

        assert result == "125-0"
        mock_redis_client.xadd.assert_called_once()
        call_args = mock_redis_client.xadd.call_args
        assert call_args[0][0] == "run:run-123:status"
        fields = call_args[0][1]
        assert fields["status"] == "completed"
        assert json.loads(fields["metadata"]) == {"duration": 30}

    @pytest.mark.asyncio
    async def test_read_run_streams(self, redis_service, mock_redis_client):
        """Test reading from run streams."""
        redis_service._client = mock_redis_client

        # Mock the xread response
        mock_redis_client.xread.return_value = [
            (
                "run:test-123:llm",
                [
                    (
                        "123-0",
                        {
                            "variation_id": "0",
                            "content": "Hello",
                            "timestamp": "2024-01-01T00:00:00Z",
                            "metadata": '{"tokens": 5}',
                        },
                    )
                ],
            ),
            (
                "run:test-123:stdout",
                [
                    (
                        "124-0",
                        {
                            "variation_id": "0",
                            "content": "Debug message",
                            "level": "DEBUG",
                            "timestamp": "2024-01-01T00:00:01Z",
                        },
                    )
                ],
            ),
        ]

        messages = []
        count = 0
        async for message in redis_service.read_run_streams("test-123"):
            messages.append(message)
            count += 1
            if count >= 2:  # Prevent infinite loop
                break

        assert len(messages) == 2

        # Check LLM message
        llm_msg = messages[0]
        assert llm_msg["type"] == "llm"
        assert llm_msg["message_id"] == "123-0"
        assert llm_msg["data"]["content"] == "Hello"
        assert llm_msg["data"]["metadata"] == {"tokens": 5}

        # Check stdout message
        stdout_msg = messages[1]
        assert stdout_msg["type"] == "stdout"
        assert stdout_msg["message_id"] == "124-0"
        assert stdout_msg["data"]["content"] == "Debug message"
        assert stdout_msg["data"]["level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_trim_streams(self, redis_service, mock_redis_client):
        """Test trimming streams."""
        redis_service._client = mock_redis_client

        await redis_service.trim_streams("run-123", max_length=500)

        assert mock_redis_client.xtrim.call_count == 4
        call_args_list = mock_redis_client.xtrim.call_args_list

        # Check that all four streams are trimmed
        streams_trimmed = [call[0][0] for call in call_args_list]
        assert "run:run-123:llm" in streams_trimmed
        assert "run:run-123:stdout" in streams_trimmed
        assert "run:run-123:status" in streams_trimmed
        assert "run:run-123:debug" in streams_trimmed

    @pytest.mark.asyncio
    async def test_delete_run_streams(self, redis_service, mock_redis_client):
        """Test deleting run streams."""
        redis_service._client = mock_redis_client

        await redis_service.delete_run_streams("run-123")

        assert mock_redis_client.delete.call_count == 4
        call_args_list = mock_redis_client.delete.call_args_list

        # Check that all four streams are deleted
        streams_deleted = [call[0][0] for call in call_args_list]
        assert "run:run-123:llm" in streams_deleted
        assert "run:run-123:stdout" in streams_deleted
        assert "run:run-123:status" in streams_deleted
        assert "run:run-123:debug" in streams_deleted

    @pytest.mark.asyncio
    async def test_health_check(self, redis_service, mock_redis_client):
        """Test Redis health check."""
        redis_service._client = mock_redis_client
        mock_redis_client.ping.return_value = True

        result = await redis_service.health_check()

        assert result is True
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_service, mock_redis_client):
        """Test Redis health check failure."""
        redis_service._client = mock_redis_client
        mock_redis_client.ping.side_effect = Exception("Connection failed")

        result = await redis_service.health_check()

        assert result is False
        mock_redis_client.ping.assert_called_once()
