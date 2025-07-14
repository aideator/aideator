"""Tests for agent streaming functionality."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_publish_output_dual_write_success():
    """Test successful dual write to both Redis and database."""
    # Set up environment
    env_vars = {
        "REDIS_URL": "redis://test",
        "DATABASE_URL_ASYNC": "postgresql://test",
        "RUN_ID": "test-run-123",
        "VARIATION_ID": "0",
    }

    with patch.dict(os.environ, env_vars):
        with (
            patch("agent.main.AIdeatorAgent._setup_file_logging"),
            patch(
                "agent.main.AIdeatorAgent._check_available_api_keys", return_value={}
            ),
            patch("tempfile.mkdtemp", return_value="/tmp/test"),  # noqa: S108
        ):
            from agent.main import AIdeatorAgent

            # Create agent instance
            agent = AIdeatorAgent()

            # Verify environment was set correctly
            assert agent.run_id == "test-run-123"
            assert agent.variation_id == 0

            # Mock connections
            agent.redis_client = AsyncMock()
            agent.db_service = AsyncMock()
            agent.log = MagicMock()

            # Mock successful Redis and DB writes
            agent.redis_client.xadd.return_value = "test-message-id"
            agent.db_service.write_agent_output = AsyncMock()

            # Test content
            test_content = "This is a test LLM output"

            # Call the method
            await agent.publish_output(test_content)

            # Verify Redis write
            agent.redis_client.xadd.assert_called_once()
            call_args = agent.redis_client.xadd.call_args
            assert call_args[0][0] == "run:test-run-123:llm"
            fields = call_args[0][1]
            assert fields["variation_id"] == "0"
            assert fields["content"] == test_content
            assert "timestamp" in fields

            # Verify database write
            agent.db_service.write_agent_output.assert_called_once_with(
                run_id="test-run-123",
                variation_id=0,
                content=test_content,
                output_type="llm",
                metadata={"content_length": len(test_content)},
            )


@pytest.mark.asyncio
async def test_publish_output_redis_fails_db_succeeds():
    """Test case where Redis fails but database succeeds."""
    env_vars = {
        "REDIS_URL": "redis://test",
        "DATABASE_URL_ASYNC": "postgresql://test",
        "RUN_ID": "test-run-456",
        "VARIATION_ID": "1",
    }

    with patch.dict(os.environ, env_vars):
        with (
            patch("agent.main.AIdeatorAgent._setup_file_logging"),
            patch(
                "agent.main.AIdeatorAgent._check_available_api_keys", return_value={}
            ),
            patch("tempfile.mkdtemp", return_value="/tmp/test"),  # noqa: S108
        ):
            from agent.main import AIdeatorAgent

            agent = AIdeatorAgent()
            agent.redis_client = AsyncMock()
            agent.db_service = AsyncMock()
            agent.log = MagicMock()

            # Mock Redis failure
            agent.redis_client.xadd.side_effect = Exception("Redis connection failed")
            # Mock DB success
            agent.db_service.write_agent_output = AsyncMock()

            test_content = "Test content"

            # Should not raise exception
            await agent.publish_output(test_content)

            # Verify DB write still happened
            agent.db_service.write_agent_output.assert_called_once()

            # Verify warning was logged
            agent.log.assert_any_call(
                "[DUAL-WRITE] LLM output written to DB only (Redis failed)",
                "WARNING",
            )
