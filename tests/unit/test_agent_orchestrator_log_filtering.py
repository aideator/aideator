"""
Unit tests for agent orchestrator log filtering functionality.

Tests the fix for streaming completion logs appearing in the chat interface.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from typing import List, Dict, Any

from app.services.agent_orchestrator import AgentOrchestrator
from app.services.kubernetes_service import KubernetesService
from app.services.sse_manager import SSEManager


class TestAgentOrchestratorLogFiltering:
    """Test suite for agent orchestrator log filtering."""
    
    @pytest.fixture
    def mock_kubernetes_service(self):
        """Mock Kubernetes service."""
        return AsyncMock(spec=KubernetesService)
    
    @pytest.fixture
    def mock_sse_manager(self):
        """Mock SSE manager."""
        return AsyncMock(spec=SSEManager)
    
    @pytest.fixture
    def orchestrator(self, mock_kubernetes_service, mock_sse_manager):
        """Agent orchestrator instance."""
        return AgentOrchestrator(mock_kubernetes_service, mock_sse_manager)
    
    @pytest.fixture
    def sample_log_entries(self):
        """Sample log entries for testing."""
        return {
            "streaming_complete_log": {
                "timestamp": "2025-07-10T17:17:08.461143",
                "run_id": "run-7bbffdbd77fa45658023a0a08db2a486",
                "variation_id": "1",
                "level": "INFO",
                "message": "Streaming LLM response complete",
                "step": "streaming_complete",
                "chunks_received": 749,
                "total_length": 3620
            },
            "regular_log": {
                "timestamp": "2025-07-10T17:17:06.123456",
                "run_id": "run-7bbffdbd77fa45658023a0a08db2a486",
                "variation_id": "1",
                "level": "INFO",
                "message": "Starting LLM generation"
            },
            "step_log": {
                "timestamp": "2025-07-10T17:17:07.234567",
                "run_id": "run-7bbffdbd77fa45658023a0a08db2a486",
                "variation_id": "1",
                "level": "DEBUG",
                "message": "Processing repository",
                "step": "repo_analysis"
            },
            "plain_text": "This is plain text output from the agent.",
            "non_log_json": {
                "result": "This is JSON but not a log entry",
                "data": "Some data"
            }
        }
    
    @pytest.mark.asyncio
    async def test_streaming_complete_log_is_filtered(self, orchestrator, sample_log_entries):
        """Test that streaming_complete logs are filtered out."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Mock the log stream to return the streaming_complete log
        streaming_log = json.dumps(sample_log_entries["streaming_complete_log"])
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield streaming_log
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was NOT called (log was filtered)
        orchestrator.sse.send_agent_output.assert_not_called()
        orchestrator.sse.send_agent_error.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_regular_log_is_filtered(self, orchestrator, sample_log_entries):
        """Test that regular logs with timestamp+level are filtered out."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Mock the log stream to return a regular log
        regular_log = json.dumps(sample_log_entries["regular_log"])
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield regular_log
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was NOT called (log was filtered)
        orchestrator.sse.send_agent_output.assert_not_called()
        orchestrator.sse.send_agent_error.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_step_log_is_filtered(self, orchestrator, sample_log_entries):
        """Test that logs with step field are filtered out."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Mock the log stream to return a step log
        step_log = json.dumps(sample_log_entries["step_log"])
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield step_log
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was NOT called (log was filtered)
        orchestrator.sse.send_agent_output.assert_not_called()
        orchestrator.sse.send_agent_error.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_plain_text_passes_through(self, orchestrator, sample_log_entries):
        """Test that plain text content passes through to SSE."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Mock the log stream to return plain text
        plain_text = sample_log_entries["plain_text"]
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield plain_text
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was called with plain text
        orchestrator.sse.send_agent_output.assert_called_once_with(
            run_id, variation_id, plain_text
        )
    
    @pytest.mark.asyncio
    async def test_non_log_json_passes_through(self, orchestrator, sample_log_entries):
        """Test that non-log JSON content passes through to SSE."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Mock the log stream to return non-log JSON
        non_log_json = json.dumps(sample_log_entries["non_log_json"])
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield non_log_json
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was called with JSON content
        orchestrator.sse.send_agent_output.assert_called_once_with(
            run_id, variation_id, non_log_json
        )
    
    @pytest.mark.asyncio
    async def test_mixed_content_filtering(self, orchestrator, sample_log_entries):
        """Test filtering with mixed content types."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Mock the log stream to return mixed content
        mixed_content = [
            json.dumps(sample_log_entries["regular_log"]),  # Should be filtered
            sample_log_entries["plain_text"],  # Should pass through
            json.dumps(sample_log_entries["streaming_complete_log"]),  # Should be filtered
            json.dumps(sample_log_entries["non_log_json"]),  # Should pass through
            json.dumps(sample_log_entries["step_log"]),  # Should be filtered
        ]
        
        async def mock_log_stream(job_name, run_id, variation_id):
            for content in mixed_content:
                yield content
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was called only for non-log content
        assert orchestrator.sse.send_agent_output.call_count == 2
        
        # Check the calls were made with the expected content
        calls = orchestrator.sse.send_agent_output.call_args_list
        assert calls[0][0][2] == sample_log_entries["plain_text"]
        assert calls[1][0][2] == json.dumps(sample_log_entries["non_log_json"])
    
    @pytest.mark.asyncio
    async def test_log_without_step_but_with_timestamp_level_filtered(self, orchestrator):
        """Test that logs with timestamp+level but no step are still filtered."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Create a log with timestamp+level but no step
        log_entry = {
            "timestamp": "2025-07-10T17:17:08.461143",
            "run_id": "run-test",
            "variation_id": "1",
            "level": "INFO",
            "message": "Some regular log message"
            # No step field
        }
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield json.dumps(log_entry)
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was NOT called (log was filtered)
        orchestrator.sse.send_agent_output.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_log_with_step_but_no_timestamp_level_filtered(self, orchestrator):
        """Test that logs with step field but no timestamp+level are still filtered."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Create a log with step but no timestamp+level
        log_entry = {
            "run_id": "run-test",
            "variation_id": "1",
            "message": "Some step message",
            "step": "some_step"
            # No timestamp or level
        }
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield json.dumps(log_entry)
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was NOT called (log was filtered)
        orchestrator.sse.send_agent_output.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_malformed_json_passed_as_plain_text(self, orchestrator):
        """Test that malformed JSON is treated as plain text."""
        run_id = "test-run-123"
        job_name = "test-job"
        variation_id = 1
        
        # Malformed JSON
        malformed_json = '{"incomplete": "json"'
        
        async def mock_log_stream(job_name, run_id, variation_id):
            yield malformed_json
        
        orchestrator.kubernetes.stream_job_logs.side_effect = mock_log_stream
        
        # Execute the streaming
        await orchestrator._stream_job_logs(run_id, job_name, variation_id)
        
        # Verify that SSE send was called with malformed JSON as plain text
        orchestrator.sse.send_agent_output.assert_called_once_with(
            run_id, variation_id, malformed_json
        )
    
    def test_log_filtering_conditions(self, sample_log_entries):
        """Test the log filtering conditions directly."""
        # Helper function to test filtering logic
        def should_filter(log_entry):
            return ('timestamp' in log_entry and 'level' in log_entry) or 'step' in log_entry
        
        # Test cases
        assert should_filter(sample_log_entries["streaming_complete_log"]) == True
        assert should_filter(sample_log_entries["regular_log"]) == True
        assert should_filter(sample_log_entries["step_log"]) == True
        assert should_filter(sample_log_entries["non_log_json"]) == False
        
        # Edge cases
        assert should_filter({"timestamp": "123", "level": "INFO"}) == True
        assert should_filter({"step": "some_step"}) == True
        assert should_filter({"timestamp": "123"}) == False
        assert should_filter({"level": "INFO"}) == False
        assert should_filter({"some": "other", "fields": "here"}) == False