"""Tests for WebSocket streaming endpoints."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.websocket import format_stream_message


class TestWebSocketLogic:
    """Test WebSocket endpoint logic without full integration."""

    def test_format_stream_message_llm(self):
        """Test formatting LLM stream messages."""
        message = {
            "type": "llm",
            "message_id": "123-456",
            "data": {
                "variation_id": "0",
                "content": "Hello world",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": "{}",
            },
        }

        result = format_stream_message(message)
        expected = {
            "type": "llm_output",
            "data": {
                "variation_id": "0",
                "content": "Hello world",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": {},
                "message_id": "123-456",
            },
        }
        assert result == expected

    def test_format_stream_message_stdout(self):
        """Test formatting stdout stream messages."""
        message = {
            "type": "stdout",
            "message_id": "123-456",
            "data": {
                "variation_id": "1",
                "content": "Debug log line",
                "level": "INFO",
                "timestamp": "2024-01-01T00:00:00",
            },
        }

        result = format_stream_message(message)
        expected = {
            "type": "stdout_log",
            "data": {
                "variation_id": "1",
                "content": "Debug log line",
                "level": "INFO",
                "timestamp": "2024-01-01T00:00:00",
                "message_id": "123-456",
            },
        }
        assert result == expected

    def test_format_stream_message_status(self):
        """Test formatting status stream messages."""
        message = {
            "type": "status",
            "message_id": "123-456",
            "data": {
                "status": "completed",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": '{"job_count": 3}',
            },
        }

        result = format_stream_message(message)
        expected = {
            "type": "status_update",
            "data": {
                "status": "completed",
                "timestamp": "2024-01-01T00:00:00",
                "metadata": {"job_count": 3},
                "message_id": "123-456",
            },
        }
        assert result == expected

    def test_format_stream_message_unknown_type(self):
        """Test handling unknown message types."""
        message = {"type": "unknown", "message_id": "123-456", "data": {"test": "data"}}

        result = format_stream_message(message)
        expected = {
            "type": "unknown",
            "data": {"test": "data", "message_id": "123-456"},
        }
        assert result == expected

    def test_stream_message_format_with_json_metadata(self):
        """Test message formatting with JSON metadata strings."""
        message = {
            "type": "llm",
            "message_id": "456-789",
            "data": {
                "variation_id": "2",
                "content": "Test response",
                "timestamp": "2024-01-01T12:00:00",
                "metadata": '{"tokens": 150, "model": "gpt-4"}',
            },
        }

        result = format_stream_message(message)
        expected = {
            "type": "llm_output",
            "data": {
                "variation_id": "2",
                "content": "Test response",
                "timestamp": "2024-01-01T12:00:00",
                "metadata": {"tokens": 150, "model": "gpt-4"},
                "message_id": "456-789",
            },
        }
        assert result == expected

    def test_stream_message_format_with_invalid_json(self):
        """Test message formatting with invalid JSON metadata."""
        message = {
            "type": "status",
            "message_id": "789-012",
            "data": {
                "status": "running",
                "timestamp": "2024-01-01T12:00:00",
                "metadata": "invalid-json{",
            },
        }

        result = format_stream_message(message)
        expected = {
            "type": "status_update",
            "data": {
                "status": "running",
                "timestamp": "2024-01-01T12:00:00",
                "metadata": "invalid-json{",  # Kept as string
                "message_id": "789-012",
            },
        }
        assert result == expected
