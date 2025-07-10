"""
Integration tests for parallel execution functionality.

These tests verify:
1. Simultaneous job creation for multiple models
2. Stream aggregation from parallel jobs
3. Partial failure handling
4. Performance under load
5. Resource management and cleanup
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.kubernetes_service import KubernetesService

settings = get_settings()


class TestParallelExecution:
    """Test suite for parallel execution functionality."""

    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture(scope="class")
    def test_models(self):
        """Test models for parallel execution."""
        return [
            "gpt-4o-mini",
            "claude-3-haiku-20240307",
            "gemini-1.5-flash",
            "llama-3.1-8b-instant"
        ]

    @pytest.fixture(scope="class")
    def sample_prompt(self):
        """Sample prompt for testing."""
        return "Write a Python function to calculate the factorial of a number."

    @pytest.fixture(scope="class")
    def mock_kubernetes_service(self):
        """Mock Kubernetes service for testing."""
        mock_service = MagicMock(spec=KubernetesService)
        mock_service.create_model_job = AsyncMock()
        mock_service.stream_job_logs = AsyncMock()
        mock_service.get_job_status = AsyncMock()
        mock_service.delete_job = AsyncMock()
        return mock_service

    @pytest.mark.asyncio
    async def test_simultaneous_job_creation(self, test_models, sample_prompt, mock_kubernetes_service):
        """Test creating multiple Kubernetes jobs simultaneously."""
        # Mock job creation to return unique job names
        mock_kubernetes_service.create_model_job.side_effect = lambda **kwargs: f"job-{kwargs['model_id']}-{kwargs['run_id']}"

        # Create orchestrator
        orchestrator = AgentOrchestrator(mock_kubernetes_service, None)

        # Start parallel execution
        run_id = "test-run-parallel"

        # Track job creation times
        job_creation_times = []

        async def create_job_with_timing(model_id: int, model_name: str):
            start_time = time.time()
            job_name = await mock_kubernetes_service.create_model_job(
                run_id=run_id,
                model_id=model_id,
                model_name=model_name,
                prompt=sample_prompt
            )
            end_time = time.time()
            job_creation_times.append(end_time - start_time)
            return job_name

        # Create jobs in parallel
        tasks = [
            create_job_with_timing(i, model)
            for i, model in enumerate(test_models)
        ]

        start_time = time.time()
        job_names = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all jobs were created
        assert len(job_names) == len(test_models)
        assert all(job_name.startswith("job-") for job_name in job_names)

        # Verify jobs were created in parallel (total time should be less than sequential)
        sequential_time = sum(job_creation_times)
        assert total_time < sequential_time * 0.8  # At least 20% faster than sequential

        # Verify correct number of job creation calls
        assert mock_kubernetes_service.create_model_job.call_count == len(test_models)

    @pytest.mark.asyncio
    async def test_stream_aggregation(self, test_models, mock_kubernetes_service):
        """Test aggregating streams from multiple parallel jobs."""
        # Mock streaming logs for each model
        async def mock_stream_logs(job_name: str, model_id: int):
            """Mock streaming logs for a job."""
            model_name = test_models[model_id]

            # Simulate streaming output
            outputs = [
                f"Starting {model_name}",
                f"Processing with {model_name}",
                f"Completed by {model_name}"
            ]

            for output in outputs:
                yield json.dumps({
                    "model_id": model_id,
                    "model_name": model_name,
                    "content": output,
                    "timestamp": time.time()
                })
                await asyncio.sleep(0.1)  # Simulate processing time

        mock_kubernetes_service.stream_job_logs.side_effect = mock_stream_logs

        # Create stream aggregator
        aggregated_streams = {}

        async def aggregate_stream(job_name: str, model_id: int):
            """Aggregate stream from a single job."""
            aggregated_streams[model_id] = []
            async for log_line in mock_kubernetes_service.stream_job_logs(job_name, model_id):
                data = json.loads(log_line)
                aggregated_streams[model_id].append(data)

        # Start parallel streaming
        tasks = [
            aggregate_stream(f"job-{i}", i)
            for i in range(len(test_models))
        ]

        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all streams were aggregated
        assert len(aggregated_streams) == len(test_models)

        # Verify each stream has expected number of messages
        for model_id in range(len(test_models)):
            assert len(aggregated_streams[model_id]) == 3  # 3 messages per model
            assert all("content" in msg for msg in aggregated_streams[model_id])
            assert all("timestamp" in msg for msg in aggregated_streams[model_id])

        # Verify streaming was parallel (should be faster than sequential)
        expected_sequential_time = len(test_models) * 3 * 0.1  # 3 messages * 0.1s delay
        assert total_time < expected_sequential_time * 0.8

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, test_models, mock_kubernetes_service):
        """Test handling of partial failures in parallel execution."""
        # Mock mixed success/failure scenarios
        async def mock_stream_with_failures(job_name: str, model_id: int):
            """Mock streaming with some failures."""
            if model_id == 1:  # Simulate failure for second model
                yield json.dumps({
                    "model_id": model_id,
                    "type": "error",
                    "error": "Model temporarily unavailable",
                    "timestamp": time.time()
                })
                return

            # Successful streaming for other models
            for i in range(3):
                yield json.dumps({
                    "model_id": model_id,
                    "content": f"Output {i} from model {model_id}",
                    "timestamp": time.time()
                })
                await asyncio.sleep(0.1)

        mock_kubernetes_service.stream_job_logs.side_effect = mock_stream_with_failures

        # Track results and failures
        results = {}
        failures = {}

        async def handle_stream_with_error_handling(job_name: str, model_id: int):
            """Handle stream with error handling."""
            try:
                results[model_id] = []
                async for log_line in mock_kubernetes_service.stream_job_logs(job_name, model_id):
                    data = json.loads(log_line)
                    if data.get("type") == "error":
                        failures[model_id] = data["error"]
                        return
                    results[model_id].append(data)
            except Exception as e:
                failures[model_id] = str(e)

        # Start parallel execution with error handling
        tasks = [
            handle_stream_with_error_handling(f"job-{i}", i)
            for i in range(len(test_models))
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Verify partial success/failure
        assert len(results) == len(test_models) - 1  # All except the failed one
        assert len(failures) == 1  # Only one failure
        assert 1 in failures  # Model 1 failed
        assert failures[1] == "Model temporarily unavailable"

        # Verify successful models completed normally
        for model_id in [0, 2, 3]:
            assert model_id in results
            assert len(results[model_id]) == 3

    @pytest.mark.asyncio
    async def test_high_concurrency_performance(self, mock_kubernetes_service):
        """Test performance under high concurrency."""
        num_models = 10  # High number of concurrent models

        # Mock fast job creation
        mock_kubernetes_service.create_model_job.side_effect = lambda **kwargs: f"job-{kwargs['model_id']}"

        # Mock fast streaming
        async def mock_fast_stream(job_name: str, model_id: int):
            """Mock fast streaming."""
            for i in range(5):
                yield json.dumps({
                    "model_id": model_id,
                    "content": f"Fast output {i}",
                    "timestamp": time.time()
                })
                await asyncio.sleep(0.01)  # Very fast

        mock_kubernetes_service.stream_job_logs.side_effect = mock_fast_stream

        # Create high-concurrency workload
        async def create_and_stream_model(model_id: int):
            """Create job and stream for a model."""
            job_name = await mock_kubernetes_service.create_model_job(
                run_id="high-concurrency-test",
                model_id=model_id,
                model_name=f"model-{model_id}",
                prompt="Test prompt"
            )

            outputs = []
            async for log_line in mock_kubernetes_service.stream_job_logs(job_name, model_id):
                outputs.append(json.loads(log_line))

            return outputs

        # Test high concurrency
        start_time = time.time()
        tasks = [create_and_stream_model(i) for i in range(num_models)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify all models completed
        assert len(results) == num_models
        assert all(len(result) == 5 for result in results)

        # Verify performance (should complete in reasonable time)
        assert total_time < 2.0  # Should complete within 2 seconds

        # Verify resource usage
        assert mock_kubernetes_service.create_model_job.call_count == num_models

    @pytest.mark.asyncio
    async def test_stream_synchronization(self, test_models, mock_kubernetes_service):
        """Test synchronization of multiple streams."""
        # Mock synchronized streaming
        sync_point = asyncio.Event()

        async def mock_synchronized_stream(job_name: str, model_id: int):
            """Mock synchronized streaming."""
            # Initial output
            yield json.dumps({
                "model_id": model_id,
                "content": f"Model {model_id} ready",
                "timestamp": time.time()
            })

            # Wait for sync point
            await sync_point.wait()

            # Synchronized output
            yield json.dumps({
                "model_id": model_id,
                "content": f"Model {model_id} synchronized",
                "timestamp": time.time()
            })

        mock_kubernetes_service.stream_job_logs.side_effect = mock_synchronized_stream

        # Start streaming tasks
        stream_results = {}

        async def collect_stream(job_name: str, model_id: int):
            """Collect stream results."""
            stream_results[model_id] = []
            async for log_line in mock_kubernetes_service.stream_job_logs(job_name, model_id):
                data = json.loads(log_line)
                stream_results[model_id].append(data)

        # Start all streams
        tasks = [
            collect_stream(f"job-{i}", i)
            for i in range(len(test_models))
        ]

        # Let them start
        await asyncio.sleep(0.1)

        # Verify all streams are waiting
        assert len(stream_results) == len(test_models)
        assert all(len(results) == 1 for results in stream_results.values())

        # Release sync point
        sync_point.set()

        # Wait for completion
        await asyncio.gather(*tasks)

        # Verify synchronized completion
        assert all(len(results) == 2 for results in stream_results.values())
        assert all("synchronized" in results[1]["content"] for results in stream_results.values())

    def test_parallel_execution_api_endpoint(self, test_client, test_models, sample_prompt):
        """Test parallel execution through API endpoint."""
        with patch.object(KubernetesService, "create_model_job") as mock_create_job:
            with patch.object(KubernetesService, "stream_job_logs") as mock_stream_logs:
                # Mock job creation
                mock_create_job.side_effect = lambda **kwargs: f"job-{kwargs['model_id']}"

                # Mock streaming
                async def mock_api_stream(job_name: str, model_id: int):
                    for i in range(3):
                        yield json.dumps({
                            "model_id": model_id,
                            "content": f"API output {i}",
                            "timestamp": time.time()
                        })

                mock_stream_logs.side_effect = mock_api_stream

                # Create multi-model run
                response = test_client.post("/api/v1/prompts", json={
                    "prompt": sample_prompt,
                    "models": test_models
                })

                assert response.status_code == 200
                data = response.json()
                assert "prompt_id" in data
                assert data["models"] == test_models

                # Test streaming endpoint
                prompt_id = data["prompt_id"]
                stream_response = test_client.get(f"/api/v1/prompts/{prompt_id}/stream")

                assert stream_response.status_code == 200
                assert "text/event-stream" in stream_response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_resource_cleanup(self, test_models, mock_kubernetes_service):
        """Test proper resource cleanup after parallel execution."""
        # Mock job lifecycle
        created_jobs = []
        deleted_jobs = []

        async def mock_create_job(**kwargs):
            job_name = f"job-{kwargs['model_id']}"
            created_jobs.append(job_name)
            return job_name

        async def mock_delete_job(job_name: str):
            deleted_jobs.append(job_name)

        mock_kubernetes_service.create_model_job.side_effect = mock_create_job
        mock_kubernetes_service.delete_job.side_effect = mock_delete_job

        # Mock streaming that completes quickly
        async def mock_cleanup_stream(job_name: str, model_id: int):
            yield json.dumps({
                "model_id": model_id,
                "content": "Completed",
                "timestamp": time.time()
            })

        mock_kubernetes_service.stream_job_logs.side_effect = mock_cleanup_stream

        # Simulate orchestrator cleanup
        async def run_with_cleanup():
            # Create jobs
            jobs = []
            for i, model in enumerate(test_models):
                job_name = await mock_kubernetes_service.create_model_job(
                    run_id="cleanup-test",
                    model_id=i,
                    model_name=model,
                    prompt="Test"
                )
                jobs.append(job_name)

            # Stream from jobs
            tasks = [
                mock_kubernetes_service.stream_job_logs(job, i)
                for i, job in enumerate(jobs)
            ]

            # Wait for completion
            await asyncio.gather(*[
                asyncio.create_task(self._consume_stream(stream))
                for stream in tasks
            ])

            # Clean up jobs
            for job in jobs:
                await mock_kubernetes_service.delete_job(job)

        await run_with_cleanup()

        # Verify cleanup
        assert len(created_jobs) == len(test_models)
        assert len(deleted_jobs) == len(test_models)
        assert set(created_jobs) == set(deleted_jobs)

    async def _consume_stream(self, stream):
        """Helper to consume a stream."""
        async for item in stream:
            pass

    @pytest.mark.asyncio
    async def test_failure_recovery(self, test_models, mock_kubernetes_service):
        """Test recovery from job failures."""
        # Mock job failures and retries
        failure_count = {}

        async def mock_failing_job(**kwargs):
            model_id = kwargs["model_id"]
            failure_count[model_id] = failure_count.get(model_id, 0) + 1

            # Fail first two attempts
            if failure_count[model_id] <= 2:
                raise Exception(f"Job creation failed for model {model_id}")

            return f"job-{model_id}-retry-{failure_count[model_id]}"

        mock_kubernetes_service.create_model_job.side_effect = mock_failing_job

        # Implement retry logic
        async def create_job_with_retry(model_id: int, model_name: str, max_retries: int = 3):
            """Create job with retry logic."""
            for attempt in range(max_retries):
                try:
                    return await mock_kubernetes_service.create_model_job(
                        run_id="retry-test",
                        model_id=model_id,
                        model_name=model_name,
                        prompt="Test"
                    )
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(0.1)  # Brief delay before retry

        # Test retry mechanism
        tasks = [
            create_job_with_retry(i, model)
            for i, model in enumerate(test_models)
        ]

        job_names = await asyncio.gather(*tasks)

        # Verify all jobs eventually succeeded
        assert len(job_names) == len(test_models)
        assert all(job_name.startswith("job-") for job_name in job_names)
        assert all("retry-3" in job_name for job_name in job_names)

        # Verify retry counts
        assert all(failure_count[i] == 3 for i in range(len(test_models)))

    @pytest.mark.asyncio
    async def test_load_balancing(self, mock_kubernetes_service):
        """Test load balancing across multiple models."""
        # Mock resource-aware job creation
        node_loads = {"node-1": 0, "node-2": 0, "node-3": 0}

        async def mock_load_balanced_job(**kwargs):
            # Select least loaded node
            selected_node = min(node_loads.keys(), key=lambda k: node_loads[k])
            node_loads[selected_node] += 1

            return f"job-{kwargs['model_id']}-{selected_node}"

        mock_kubernetes_service.create_model_job.side_effect = mock_load_balanced_job

        # Create many jobs to test load balancing
        num_jobs = 12  # Should distribute across 3 nodes

        tasks = [
            mock_kubernetes_service.create_model_job(
                run_id="load-balance-test",
                model_id=i,
                model_name=f"model-{i}",
                prompt="Test"
            )
            for i in range(num_jobs)
        ]

        job_names = await asyncio.gather(*tasks)

        # Verify load distribution
        assert len(job_names) == num_jobs

        # Check load balancing
        node_job_counts = {}
        for job_name in job_names:
            node = job_name.split("-")[-1]
            node_job_counts[node] = node_job_counts.get(node, 0) + 1

        # Should be roughly evenly distributed
        expected_per_node = num_jobs // 3
        for node, count in node_job_counts.items():
            assert abs(count - expected_per_node) <= 1  # Allow for rounding differences

    @pytest.mark.asyncio
    async def test_timeout_handling(self, test_models, mock_kubernetes_service):
        """Test timeout handling in parallel execution."""
        # Mock jobs with different completion times
        async def mock_timed_stream(job_name: str, model_id: int):
            # Some models take longer
            delay = 0.1 if model_id < 2 else 0.5

            for i in range(3):
                yield json.dumps({
                    "model_id": model_id,
                    "content": f"Output {i}",
                    "timestamp": time.time()
                })
                await asyncio.sleep(delay)

        mock_kubernetes_service.stream_job_logs.side_effect = mock_timed_stream

        # Test with timeout
        timeout = 0.3  # Short timeout

        async def stream_with_timeout(job_name: str, model_id: int):
            """Stream with timeout."""
            try:
                outputs = []
                async for log_line in asyncio.wait_for(
                    mock_kubernetes_service.stream_job_logs(job_name, model_id),
                    timeout=timeout
                ):
                    outputs.append(json.loads(log_line))
                return outputs
            except TimeoutError:
                return {"timeout": True, "model_id": model_id}

        # Run with timeout
        tasks = [
            stream_with_timeout(f"job-{i}", i)
            for i in range(len(test_models))
        ]

        results = await asyncio.gather(*tasks)

        # Verify timeout behavior
        fast_results = [r for r in results if not isinstance(r, dict) or "timeout" not in r]
        timeout_results = [r for r in results if isinstance(r, dict) and "timeout" in r]

        assert len(fast_results) == 2  # Fast models completed
        assert len(timeout_results) == 2  # Slow models timed out
        assert all(len(r) == 3 for r in fast_results)  # Fast models completed fully
