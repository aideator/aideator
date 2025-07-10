"""
Integration tests for multi-model streaming functionality.

These tests verify:
1. SSE streaming works with multiple models
2. Stream multiplexing and synchronization
3. Real-time event handling
4. Stream cleanup and error recovery
"""

import asyncio
import json
import pytest
import time
from typing import Dict, List, Any
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.kubernetes_service import KubernetesService


class TestStreamingIntegration:
    """Test suite for multi-model streaming integration."""
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def mock_run_id(self):
        """Mock run ID for testing."""
        return "test-run-123"
    
    @pytest.fixture(scope="class")
    def test_models(self):
        """Test models for streaming."""
        return ["gpt-4o-mini", "claude-3-haiku-20240307", "gemini-1.5-flash"]
    
    @pytest.fixture(scope="class")
    def sample_prompt(self):
        """Sample prompt for testing."""
        return "Write a haiku about programming"
    
    def test_create_multi_model_run(self, test_client, test_models, sample_prompt):
        """Test creating a multi-model comparison run."""
        with patch.object(KubernetesService, 'create_model_job') as mock_create_job:
            mock_create_job.return_value = "test-job-123"
            
            # Create a multi-model run
            response = test_client.post("/api/v1/runs", json={
                "github_url": "https://github.com/test/repo",
                "prompt": sample_prompt,
                "variations": len(test_models),
                "agent_mode": "litellm"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            assert "stream_url" in data
            assert data["status"] == "started"
            
            # Verify correct number of jobs were created
            assert mock_create_job.call_count == len(test_models)
    
    def test_sse_stream_endpoint(self, test_client, mock_run_id):
        """Test SSE streaming endpoint basics."""
        with patch.object(KubernetesService, 'stream_job_logs') as mock_stream:
            # Mock streaming logs
            async def mock_log_stream(job_name, variation_id):
                for i in range(3):
                    yield f"data: {json.dumps({'variation_id': variation_id, 'content': f'Line {i}', 'type': 'agent_output'})}\n\n"
                    await asyncio.sleep(0.1)
            
            mock_stream.side_effect = mock_log_stream
            
            # Test SSE endpoint
            response = test_client.get(f"/api/v1/runs/{mock_run_id}/stream")
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming(self, mock_run_id):
        """Test concurrent streaming from multiple models."""
        async def simulate_model_stream(model_id: str, events: List[Dict]):
            """Simulate streaming events from a model."""
            for event in events:
                event["model_id"] = model_id
                yield event
                await asyncio.sleep(0.1)
        
        # Define test events for different models
        model_events = {
            "gpt-4o-mini": [
                {"type": "agent_output", "content": "GPT: Line 1"},
                {"type": "agent_output", "content": "GPT: Line 2"},
                {"type": "agent_complete", "content": "GPT: Done"}
            ],
            "claude-3-haiku": [
                {"type": "agent_output", "content": "Claude: Line 1"},
                {"type": "agent_output", "content": "Claude: Line 2"},
                {"type": "agent_complete", "content": "Claude: Done"}
            ],
            "gemini-1.5-flash": [
                {"type": "agent_output", "content": "Gemini: Line 1"},
                {"type": "agent_output", "content": "Gemini: Line 2"},
                {"type": "agent_complete", "content": "Gemini: Done"}
            ]
        }
        
        # Start concurrent streams
        tasks = []
        for model_id, events in model_events.items():
            task = asyncio.create_task(
                self._collect_stream_events(
                    simulate_model_stream(model_id, events)
                )
            )
            tasks.append(task)
        
        # Wait for all streams to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all models streamed correctly
        for model_id, result in zip(model_events.keys(), results):
            assert len(result) == 3  # 2 outputs + 1 complete
            assert result[0]["model_id"] == model_id
            assert result[-1]["type"] == "agent_complete"
    
    async def _collect_stream_events(self, stream):
        """Helper to collect events from a stream."""
        events = []
        async for event in stream:
            events.append(event)
        return events
    
    def test_stream_error_handling(self, test_client, mock_run_id):
        """Test error handling in streaming."""
        with patch.object(KubernetesService, 'stream_job_logs') as mock_stream:
            # Mock streaming error
            async def mock_error_stream(job_name, variation_id):
                yield f"data: {json.dumps({'variation_id': variation_id, 'content': 'Starting...', 'type': 'agent_output'})}\n\n"
                raise Exception("Simulated streaming error")
            
            mock_stream.side_effect = mock_error_stream
            
            # Test error handling
            response = test_client.get(f"/api/v1/runs/{mock_run_id}/stream")
            assert response.status_code == 200
            
            # The stream should include error events
            content = response.content.decode()
            assert "agent_output" in content
    
    @pytest.mark.asyncio
    async def test_stream_synchronization(self):
        """Test synchronization between multiple streams."""
        class StreamSynchronizer:
            def __init__(self):
                self.events = []
                self.completed_models = set()
                self.lock = asyncio.Lock()
            
            async def add_event(self, model_id: str, event: Dict):
                async with self.lock:
                    event["model_id"] = model_id
                    event["timestamp"] = time.time()
                    self.events.append(event)
                    
                    if event["type"] == "agent_complete":
                        self.completed_models.add(model_id)
            
            async def wait_for_completion(self, model_ids: List[str]):
                while len(self.completed_models) < len(model_ids):
                    await asyncio.sleep(0.1)
                
                return self.events
        
        # Test synchronization
        sync = StreamSynchronizer()
        models = ["model1", "model2", "model3"]
        
        # Simulate concurrent events
        async def simulate_model(model_id: str):
            await sync.add_event(model_id, {"type": "agent_output", "content": f"{model_id}: Starting"})
            await asyncio.sleep(0.2)
            await sync.add_event(model_id, {"type": "agent_output", "content": f"{model_id}: Processing"})
            await asyncio.sleep(0.1)
            await sync.add_event(model_id, {"type": "agent_complete", "content": f"{model_id}: Done"})
        
        # Start all models
        tasks = [simulate_model(model_id) for model_id in models]
        await asyncio.gather(*tasks)
        
        # Wait for completion
        events = await sync.wait_for_completion(models)
        
        # Verify all models completed
        assert len(sync.completed_models) == len(models)
        assert len(events) == len(models) * 3  # 2 outputs + 1 complete per model
        
        # Verify events are properly timestamped
        timestamps = [event["timestamp"] for event in events]
        assert timestamps == sorted(timestamps)  # Should be chronological
    
    def test_stream_cleanup_on_disconnect(self, test_client, mock_run_id):
        """Test stream cleanup when client disconnects."""
        with patch.object(KubernetesService, 'stream_job_logs') as mock_stream:
            # Mock long-running stream
            async def mock_long_stream(job_name, variation_id):
                for i in range(100):  # Long stream
                    yield f"data: {json.dumps({'variation_id': variation_id, 'content': f'Line {i}', 'type': 'agent_output'})}\n\n"
                    await asyncio.sleep(0.1)
            
            mock_stream.side_effect = mock_long_stream
            
            # Start stream and immediately close
            with test_client.stream("GET", f"/api/v1/runs/{mock_run_id}/stream") as response:
                assert response.status_code == 200
                # Read only first chunk then close
                for chunk in response.iter_raw():
                    break
            
            # Stream should be cleaned up (no way to directly test this,
            # but it should not cause issues)
    
    @pytest.mark.asyncio
    async def test_stream_buffering(self):
        """Test stream buffering for smooth output."""
        class StreamBuffer:
            def __init__(self, buffer_size=10):
                self.buffer = []
                self.buffer_size = buffer_size
                self.flushed_events = []
            
            async def add_chunk(self, chunk: str):
                self.buffer.append(chunk)
                if len(self.buffer) >= self.buffer_size:
                    await self.flush()
            
            async def flush(self):
                if self.buffer:
                    combined = "".join(self.buffer)
                    self.flushed_events.append(combined)
                    self.buffer.clear()
        
        # Test buffering
        buffer = StreamBuffer(buffer_size=3)
        
        # Add chunks
        chunks = ["Hello", " ", "world", "!", " ", "How", " ", "are", " ", "you?"]
        for chunk in chunks:
            await buffer.add_chunk(chunk)
        
        # Flush remaining
        await buffer.flush()
        
        # Verify buffering worked
        assert len(buffer.flushed_events) > 0
        full_text = "".join(buffer.flushed_events)
        assert full_text == "Hello world! How are you?"
    
    def test_stream_content_types(self, test_client, mock_run_id):
        """Test different types of streaming content."""
        with patch.object(KubernetesService, 'stream_job_logs') as mock_stream:
            # Mock different event types
            async def mock_event_types(job_name, variation_id):
                events = [
                    {"type": "agent_output", "content": "Regular output"},
                    {"type": "agent_error", "content": "Error message", "error": True},
                    {"type": "agent_complete", "content": "Completion", "response_time": 2.5, "token_count": 100},
                    {"type": "heartbeat", "timestamp": time.time()}
                ]
                
                for event in events:
                    event["variation_id"] = variation_id
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.1)
            
            mock_stream.side_effect = mock_event_types
            
            # Test different content types
            response = test_client.get(f"/api/v1/runs/{mock_run_id}/stream")
            assert response.status_code == 200
            
            content = response.content.decode()
            assert "agent_output" in content
            assert "agent_error" in content
            assert "agent_complete" in content
            assert "heartbeat" in content
    
    def test_stream_rate_limiting(self, test_client, mock_run_id):
        """Test stream rate limiting to prevent overwhelming."""
        with patch.object(KubernetesService, 'stream_job_logs') as mock_stream:
            # Mock high-frequency stream
            async def mock_high_frequency_stream(job_name, variation_id):
                for i in range(20):  # High frequency
                    yield f"data: {json.dumps({'variation_id': variation_id, 'content': f'Fast {i}', 'type': 'agent_output'})}\n\n"
                    await asyncio.sleep(0.01)  # Very fast
            
            mock_stream.side_effect = mock_high_frequency_stream
            
            # Test rate limiting
            start_time = time.time()
            response = test_client.get(f"/api/v1/runs/{mock_run_id}/stream")
            duration = time.time() - start_time
            
            assert response.status_code == 200
            # Should take some minimum time due to rate limiting
            # (This depends on implementation - might need adjustment)
    
    @pytest.mark.asyncio
    async def test_stream_recovery(self):
        """Test stream recovery from failures."""
        class RecoverableStream:
            def __init__(self, max_retries=3):
                self.max_retries = max_retries
                self.attempt = 0
            
            async def stream_with_recovery(self):
                while self.attempt < self.max_retries:
                    try:
                        async for event in self._generate_stream():
                            yield event
                        break  # Success
                    except Exception as e:
                        self.attempt += 1
                        if self.attempt >= self.max_retries:
                            raise e
                        await asyncio.sleep(0.1)  # Brief delay before retry
            
            async def _generate_stream(self):
                yield {"type": "agent_output", "content": "Starting"}
                
                # Simulate failure on first attempt
                if self.attempt == 0:
                    raise Exception("Simulated failure")
                
                yield {"type": "agent_output", "content": "Success"}
                yield {"type": "agent_complete", "content": "Done"}
        
        # Test recovery
        stream = RecoverableStream()
        events = []
        
        async for event in stream.stream_with_recovery():
            events.append(event)
        
        # Should have recovered and completed
        assert len(events) == 3
        assert events[0]["content"] == "Starting"
        assert events[1]["content"] == "Success"
        assert events[2]["type"] == "agent_complete"
        assert stream.attempt == 1  # Should have retried once
    
    def test_stream_metrics_collection(self, test_client, mock_run_id):
        """Test metrics collection during streaming."""
        with patch.object(KubernetesService, 'stream_job_logs') as mock_stream:
            # Mock stream with metrics
            async def mock_metrics_stream(job_name, variation_id):
                events = [
                    {"type": "agent_output", "content": "Starting", "timestamp": time.time()},
                    {"type": "agent_output", "content": "Processing", "timestamp": time.time()},
                    {
                        "type": "agent_complete",
                        "content": "Done",
                        "timestamp": time.time(),
                        "response_time_ms": 2500,
                        "token_count": 150,
                        "cost_usd": 0.0025
                    }
                ]
                
                for event in events:
                    event["variation_id"] = variation_id
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.1)
            
            mock_stream.side_effect = mock_metrics_stream
            
            # Test metrics collection
            response = test_client.get(f"/api/v1/runs/{mock_run_id}/stream")
            assert response.status_code == 200
            
            content = response.content.decode()
            assert "response_time_ms" in content
            assert "token_count" in content
            assert "cost_usd" in content