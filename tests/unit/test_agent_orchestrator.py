"""Tests for the agent orchestrator service."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.schemas.runs import AgentConfig
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.kubernetes_service import KubernetesService


class TestAgentOrchestrator:
    """Test the agent orchestrator service."""

    @pytest.fixture
    def mock_kubernetes_service(self):
        """Create a mock Kubernetes service."""
        service = Mock(spec=KubernetesService)
        service.create_agent_job = AsyncMock(
            side_effect=lambda run_id,
            variation_id,
            *_args,
            **_kwargs: f"agent-job-{run_id}-{variation_id}"
        )
        service.get_job_status = AsyncMock(
            return_value={"status": "running", "phase": "Running"}
        )
        service.delete_job = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def mock_redis_service(self):
        """Create a mock Redis service."""
        service = Mock()
        service.health_check = AsyncMock(return_value=True)
        service.connect = AsyncMock()
        service.add_status_update = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_kubernetes_service, mock_redis_service):
        """Create an agent orchestrator instance."""
        with patch("app.services.agent_orchestrator.redis_service", mock_redis_service):
            return AgentOrchestrator(mock_kubernetes_service)

    @pytest.fixture
    def mock_settings(self):
        """Mock settings."""
        with patch("app.services.agent_orchestrator.settings") as mock_settings:
            mock_settings.max_concurrent_runs = 10
            mock_settings.max_concurrent_jobs = 50
            yield mock_settings

    def test_init(self, mock_kubernetes_service):
        """Test orchestrator initialization."""
        orchestrator = AgentOrchestrator(mock_kubernetes_service)
        assert orchestrator.kubernetes == mock_kubernetes_service
        assert orchestrator.active_runs == {}
        assert orchestrator._total_active_jobs == 0

    @pytest.mark.asyncio
    async def test_check_concurrency_limits_within_limits(
        self, orchestrator, mock_settings
    ):
        """Test concurrency checking when within limits."""
        result = await orchestrator._check_concurrency_limits(5)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_concurrency_limits_exceed_runs(
        self, orchestrator, mock_settings
    ):
        """Test concurrency checking when exceeding run limit."""
        # Fill up active runs
        for i in range(10):
            orchestrator.active_runs[f"run_{i}"] = {"status": "running"}

        result = await orchestrator._check_concurrency_limits(1)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_concurrency_limits_exceed_jobs(
        self, orchestrator, mock_settings
    ):
        """Test concurrency checking when exceeding job limit."""
        orchestrator._total_active_jobs = 48
        result = await orchestrator._check_concurrency_limits(5)
        assert result is False

    @pytest.mark.asyncio
    async def test_increment_job_count(self, orchestrator):
        """Test incrementing job count."""
        await orchestrator._increment_job_count(3)
        assert orchestrator._total_active_jobs == 3

        await orchestrator._increment_job_count(2)
        assert orchestrator._total_active_jobs == 5

    @pytest.mark.asyncio
    async def test_decrement_job_count(self, orchestrator):
        """Test decrementing job count."""
        orchestrator._total_active_jobs = 5

        await orchestrator._decrement_job_count(2)
        assert orchestrator._total_active_jobs == 3

        # Test that it doesn't go negative
        await orchestrator._decrement_job_count(5)
        assert orchestrator._total_active_jobs == 0

    @pytest.mark.asyncio
    async def test_execute_variations_basic(
        self, orchestrator, mock_kubernetes_service, mock_redis_service
    ):
        """Test executing variations with basic parameters."""
        run_id = "test-run-123"
        repo_url = "https://github.com/test/repo"
        prompt = "Test prompt"
        variations = 3

        # Mock wait_for_jobs_completion to complete immediately
        with patch.object(orchestrator, "_wait_for_jobs_completion", new=AsyncMock()):
            await orchestrator.execute_variations(
                run_id=run_id,
                repo_url=repo_url,
                prompt=prompt,
                variations=variations,
                user_id="test-user-123",  # Add required user_id parameter
            )

        # Verify run was stored
        assert run_id in orchestrator.active_runs
        assert orchestrator.active_runs[run_id]["repo_url"] == repo_url
        assert orchestrator.active_runs[run_id]["prompt"] == prompt
        assert orchestrator.active_runs[run_id]["variations"] == variations

        # Verify Kubernetes jobs were created
        assert mock_kubernetes_service.create_agent_job.call_count == variations

        # Verify Redis status updates
        mock_redis_service.add_status_update.assert_called()

    @pytest.mark.asyncio
    async def test_execute_variations_with_agent_config(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test executing variations with agent configuration."""
        run_id = "test-run-456"
        agent_config = AgentConfig(
            model="gpt-4",
            max_tokens=4096,
            temperature=0.7,
        )

        with patch.object(orchestrator, "_wait_for_jobs_completion", new=AsyncMock()):
            await orchestrator.execute_variations(
                run_id=run_id,
                repo_url="https://github.com/test/repo",
                prompt="Test prompt",
                variations=2,
                agent_config=agent_config,
                user_id="test-user-456",
            )

        # Verify agent config was stored
        stored_config = orchestrator.active_runs[run_id]["agent_config"]
        assert stored_config["model"] == "gpt-4"
        assert stored_config["max_tokens"] == 4096
        assert stored_config["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_execute_variations_with_db_session(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test executing variations with database session."""
        run_id = "test-run-789"
        mock_session = AsyncMock(spec=AsyncSession)
        mock_run = Mock(spec=Run)
        mock_session.get.return_value = mock_run

        with patch.object(orchestrator, "_wait_for_jobs_completion", new=AsyncMock()):
            await orchestrator.execute_variations(
                run_id=run_id,
                repo_url="https://github.com/test/repo",
                prompt="Test prompt",
                variations=1,
                db_session=mock_session,
                user_id="test-user-789",
            )

        # Verify database was updated
        mock_session.get.assert_called_with(Run, run_id)
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_execute_variations_error_handling(
        self, orchestrator, mock_kubernetes_service, mock_redis_service
    ):
        """Test error handling during variation execution."""
        run_id = "test-run-error"
        mock_kubernetes_service.create_agent_job.side_effect = Exception("K8s error")

        await orchestrator.execute_variations(
            run_id=run_id,
            repo_url="https://github.com/test/repo",
            prompt="Test prompt",
            variations=2,
            user_id="test-user-error",
        )

        # Verify error status was set
        assert orchestrator.active_runs[run_id]["status"] == "failed"

        # Verify Redis was notified of failure
        mock_redis_service.add_status_update.assert_called_with(
            run_id, "failed", {"error": "K8s error"}
        )

    @pytest.mark.asyncio
    async def test_wait_for_jobs_completion_all_complete(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test waiting for jobs when all complete immediately."""
        run_id = "test-run-wait"
        job_names = ["job-1", "job-2", "job-3"]

        # Mock all jobs as completed
        mock_kubernetes_service.get_job_status.return_value = {
            "status": "completed",
            "phase": "Succeeded",
        }

        await orchestrator._wait_for_jobs_completion(run_id, job_names)

        # Should have checked each job status
        assert mock_kubernetes_service.get_job_status.call_count >= len(job_names)

    @pytest.mark.asyncio
    async def test_wait_for_jobs_completion_gradual(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test waiting for jobs that complete gradually."""
        run_id = "test-run-gradual"
        job_names = ["job-1", "job-2"]

        # Mock jobs completing over time
        call_count = 0

        async def mock_get_status(job_name):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return {"status": "running", "phase": "Running"}
            return {"status": "completed", "phase": "Succeeded"}

        mock_kubernetes_service.get_job_status.side_effect = mock_get_status

        # Use a shorter sleep for testing
        with patch("asyncio.sleep", new=AsyncMock()):
            await orchestrator._wait_for_jobs_completion(run_id, job_names)

        assert call_count >= 3

    @pytest.mark.asyncio
    async def test_get_run_status_existing(self, orchestrator, mock_kubernetes_service):
        """Test getting status of an existing run."""
        run_id = "test-run-status"
        orchestrator.active_runs[run_id] = {
            "repo_url": "https://github.com/test/repo",
            "prompt": "Test prompt",
            "variations": 2,
            "status": "running",
            "start_time": datetime.utcnow().isoformat(),
            "jobs": ["job-1", "job-2"],
        }

        result = await orchestrator.get_run_status(run_id)

        assert result["run_id"] == run_id
        assert result["status"] == "running"
        assert result["variations"] == 2
        assert len(result["jobs"]) == 2

    @pytest.mark.asyncio
    async def test_get_run_status_not_found(self, orchestrator):
        """Test getting status of non-existent run."""
        result = await orchestrator.get_run_status("non-existent")

        assert result["status"] == "not_found"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_cancel_run_success(
        self, orchestrator, mock_kubernetes_service, mock_redis_service
    ):
        """Test successfully canceling a run."""
        run_id = "test-run-cancel"
        orchestrator.active_runs[run_id] = {
            "status": "running",
            "jobs": ["job-1", "job-2", "job-3"],
        }

        result = await orchestrator.cancel_run(run_id)

        assert result is True
        assert orchestrator.active_runs[run_id]["status"] == "cancelled"
        assert mock_kubernetes_service.delete_job.call_count == 3
        mock_redis_service.add_status_update.assert_called_with(run_id, "cancelled")

    @pytest.mark.asyncio
    async def test_cancel_run_not_found(self, orchestrator):
        """Test canceling a non-existent run."""
        result = await orchestrator.cancel_run("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_run_partial_failure(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test canceling a run when some job deletions fail."""
        run_id = "test-run-partial"
        orchestrator.active_runs[run_id] = {
            "status": "running",
            "jobs": ["job-1", "job-2"],
        }

        # Make second deletion fail
        mock_kubernetes_service.delete_job.side_effect = [True, False]

        result = await orchestrator.cancel_run(run_id)

        assert result is False  # Overall failure
        assert orchestrator.active_runs[run_id]["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cleanup_run_metadata_completed(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test cleaning up completed run metadata."""
        run_id = "test-run-cleanup"
        orchestrator.active_runs[run_id] = {
            "status": "completed",
            "jobs": ["job-1", "job-2"],
            "variations": 2,
        }
        orchestrator._total_active_jobs = 2

        # Use no delay for testing
        await orchestrator._cleanup_run_metadata(run_id, delay=0)

        # Verify run was cleaned up
        assert run_id not in orchestrator.active_runs
        assert mock_kubernetes_service.delete_job.call_count == 2
        assert orchestrator._total_active_jobs == 0

    @pytest.mark.asyncio
    async def test_cleanup_run_metadata_running(
        self, orchestrator, mock_kubernetes_service
    ):
        """Test that running jobs are not cleaned up."""
        run_id = "test-run-no-cleanup"
        orchestrator.active_runs[run_id] = {
            "status": "running",
            "jobs": ["job-1"],
        }

        await orchestrator._cleanup_run_metadata(run_id, delay=0)

        # Verify run was NOT cleaned up
        assert run_id in orchestrator.active_runs
        mock_kubernetes_service.delete_job.assert_not_called()

    def test_get_active_runs(self, orchestrator):
        """Test getting all active runs."""
        orchestrator.active_runs = {
            "run-1": {"status": "running"},
            "run-2": {"status": "completed"},
        }

        result = orchestrator.get_active_runs()

        assert len(result) == 2
        assert "run-1" in result
        assert "run-2" in result
        # Verify it's a copy, not the original dict
        result["run-3"] = {"status": "test"}
        assert "run-3" not in orchestrator.active_runs

    @pytest.mark.asyncio
    async def test_update_run_status_success(self, orchestrator):
        """Test updating run status in database."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_run = Mock(spec=Run)
        mock_session.get.return_value = mock_run

        await orchestrator._update_run_status(
            mock_session, "test-run", RunStatus.COMPLETED
        )

        assert mock_run.status == RunStatus.COMPLETED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_run_status_not_found(self, orchestrator):
        """Test updating status when run not found in database."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = None

        # Should not raise exception
        await orchestrator._update_run_status(
            mock_session, "non-existent", RunStatus.FAILED
        )

        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_run_status_error(self, orchestrator):
        """Test handling database error when updating status."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_run = Mock(spec=Run)
        mock_session.get.return_value = mock_run
        mock_session.commit.side_effect = Exception("DB error")

        # Should not raise exception
        await orchestrator._update_run_status(
            mock_session, "test-run", RunStatus.FAILED
        )

        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_individual_jobs(
        self, orchestrator, mock_kubernetes_service, mock_redis_service
    ):
        """Test executing individual agent jobs."""
        run_id = "test-run-individual"
        repo_url = "https://github.com/test/repo"
        prompt = "Test prompt"
        variations = 3

        orchestrator.active_runs[run_id] = {
            "status": "starting",
            "jobs": [],
        }

        # Mock wait completion
        with patch.object(orchestrator, "_wait_for_jobs_completion", new=AsyncMock()):
            await orchestrator._execute_individual_jobs(
                run_id, repo_url, prompt, variations, user_id="test-user-individual"
            )

        # Verify jobs were created
        assert mock_kubernetes_service.create_agent_job.call_count == variations
        assert len(orchestrator.active_runs[run_id]["jobs"]) == variations
        assert orchestrator.active_runs[run_id]["status"] == "running"

        # Verify Redis updates
        status_calls = [
            call
            for call in mock_redis_service.add_status_update.call_args_list
            if call[0][1] == "running"
        ]
        assert len(status_calls) >= 1

    @pytest.mark.asyncio
    async def test_execute_variations_redis_not_healthy(
        self, orchestrator, mock_redis_service
    ):
        """Test that Redis connection is initialized if not healthy."""
        mock_redis_service.health_check.return_value = False

        with patch.object(orchestrator, "_wait_for_jobs_completion", new=AsyncMock()):
            await orchestrator.execute_variations(
                run_id="test-run",
                repo_url="https://github.com/test/repo",
                prompt="Test prompt",
                variations=1,
                user_id="test-user-redis",
            )

        # Verify Redis connect was called
        mock_redis_service.connect.assert_called_once()
