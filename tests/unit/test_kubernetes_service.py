"""Tests for the Kubernetes service."""

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from app.services.kubernetes_service import KubernetesService


class TestKubernetesService:
    """Test the Kubernetes service."""

    @pytest.fixture
    def service(self):
        """Create a Kubernetes service instance."""
        return KubernetesService(namespace="test-namespace")

    @pytest.fixture
    def mock_subprocess_result(self):
        """Create a mock subprocess result."""
        result = Mock(spec=subprocess.CompletedProcess)
        result.returncode = 0
        result.stdout = b""
        result.stderr = b""
        return result

    def test_init(self):
        """Test service initialization."""
        service = KubernetesService(namespace="custom-namespace")
        assert service.namespace == "custom-namespace"
        assert service.kubectl_timeout == 300
        assert service.helm_chart_path.name == "aideator"
        assert service.job_templates_dir.name == "jobs"

    def test_escape_yaml_string(self, service):
        """Test YAML string escaping."""
        # Test simple string
        assert service._escape_yaml_string("hello") == '"hello"'

        # Test string with quotes
        assert service._escape_yaml_string('hello "world"') == '"hello \\"world\\""'

        # Test string with newlines
        assert service._escape_yaml_string("hello\nworld") == '"hello\\nworld"'

        # Test string with special characters
        assert service._escape_yaml_string("hello: world") == '"hello: world"'

    @pytest.mark.asyncio
    async def test_create_agent_job_success(self, service, mock_subprocess_result):
        """Test successful agent job creation."""
        run_id = "test-run-123"
        variation_id = 0
        repo_url = "https://github.com/test/repo"
        prompt = "Test prompt"

        # Mock file operations
        mock_yaml_content = "job yaml content"
        with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                import os
                import tempfile

                fd, temp_file_path = tempfile.mkstemp(suffix="_agent_test.yaml")
                os.close(fd)
                mock_temp.return_value.__enter__.return_value.name = temp_file_path

                with patch.object(
                    service,
                    "_run_kubectl_command",
                    new=AsyncMock(return_value=mock_subprocess_result),
                ) as mock_kubectl:
                    with patch("os.unlink") as mock_unlink:
                        job_name = await service.create_agent_job(
                            run_id=run_id,
                            variation_id=variation_id,
                            repo_url=repo_url,
                            prompt=prompt,
                        )

        assert job_name == f"agent-{run_id}-{variation_id}"
        mock_kubectl.assert_called_once()
        mock_unlink.assert_called_once_with(temp_file_path)

    @pytest.mark.asyncio
    async def test_create_agent_job_with_agent_config(
        self, service, mock_subprocess_result
    ):
        """Test agent job creation with configuration."""
        agent_config = {"model": "gpt-4", "temperature": 0.7}

        with patch("builtins.open", mock_open(read_data="template")):
            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                import os
                import tempfile

                fd, temp_file_path = tempfile.mkstemp(suffix="_agent_config_test.yaml")
                os.close(fd)
                mock_temp.return_value.__enter__.return_value.name = temp_file_path

                with patch.object(
                    service,
                    "_run_kubectl_command",
                    new=AsyncMock(return_value=mock_subprocess_result),
                ):
                    with patch("os.unlink"):
                        job_name = await service.create_agent_job(
                            run_id="test",
                            variation_id=0,
                            repo_url="https://github.com/test/repo",
                            prompt="test",
                            agent_config=agent_config,
                            agent_mode="claude-cli",
                        )

        assert job_name == "agent-test-0"

    @pytest.mark.asyncio
    async def test_create_agent_job_kubectl_error(self, service):
        """Test agent job creation when kubectl fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = b"kubectl error"

        with patch("builtins.open", mock_open(read_data="template")):
            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                import os
                import tempfile

                fd, temp_file_path = tempfile.mkstemp(suffix="_agent_error_test.yaml")
                os.close(fd)
                mock_temp.return_value.__enter__.return_value.name = temp_file_path

                with patch.object(
                    service,
                    "_run_kubectl_command",
                    new=AsyncMock(return_value=mock_result),
                ):
                    with patch("os.unlink") as mock_unlink:
                        with pytest.raises(RuntimeError, match="Failed to create job"):
                            await service.create_agent_job(
                                run_id="test",
                                variation_id=0,
                                repo_url="https://github.com/test/repo",
                                prompt="test",
                            )

                        # Ensure cleanup happens even on error
                        mock_unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_job_success(self, service, mock_subprocess_result):
        """Test successful job deletion."""
        with patch.object(
            service,
            "_run_kubectl_command",
            new=AsyncMock(return_value=mock_subprocess_result),
        ) as mock_kubectl:
            result = await service.delete_job("test-job")

        assert result is True
        mock_kubectl.assert_called_once()
        cmd = mock_kubectl.call_args[0][0]
        assert "delete" in cmd
        assert "test-job" in cmd
        assert "--ignore-not-found=true" in cmd

    @pytest.mark.asyncio
    async def test_delete_job_failure(self, service):
        """Test job deletion failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = b"delete error"

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            result = await service.delete_job("test-job")

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_run_success(self, service, mock_subprocess_result):
        """Test successfully canceling a run."""
        run_id = "test-run-123"

        # Mock get jobs response
        jobs_data = {
            "items": [
                {"metadata": {"name": "agent-test-run-123-0"}},
                {"metadata": {"name": "agent-test-run-123-1"}},
            ]
        }
        mock_get_result = Mock()
        mock_get_result.returncode = 0
        mock_get_result.stdout = json.dumps(jobs_data).encode()

        with patch.object(
            service,
            "_run_kubectl_command",
            new=AsyncMock(side_effect=[mock_get_result]),
        ):
            with patch.object(
                service, "delete_job", new=AsyncMock(return_value=True)
            ) as mock_delete:
                result = await service.cancel_run(run_id)

        assert result is True
        assert mock_delete.call_count == 2

    @pytest.mark.asyncio
    async def test_cancel_run_no_jobs(self, service):
        """Test canceling a run with no jobs."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"items": []}).encode()

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            result = await service.cancel_run("test-run")

        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_run_kubectl_error(self, service):
        """Test canceling a run when kubectl fails."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            result = await service.cancel_run("test-run")

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_run_json_error(self, service):
        """Test canceling a run with invalid JSON response."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"invalid json"

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            result = await service.cancel_run("test-run")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_job_status_success(self, service):
        """Test getting job status successfully."""
        job_data = {
            "status": {
                "active": 1,
                "succeeded": 0,
                "failed": 0,
                "startTime": "2024-01-01T00:00:00Z",
                "conditions": [{"type": "Complete", "status": "False"}],
            }
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(job_data).encode()

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            status = await service.get_job_status("test-job")

        assert status["status"] == "running"
        assert status["active"] == 1
        assert status["succeeded"] == 0
        assert status["failed"] == 0
        assert "start_time" in status

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, service):
        """Test getting status of non-existent job."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = b"job not found"

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            status = await service.get_job_status("non-existent")

        assert status["status"] == "not_found"
        assert "error" in status

    @pytest.mark.asyncio
    async def test_get_job_status_json_error(self, service):
        """Test getting job status with invalid JSON."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"invalid json"

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            status = await service.get_job_status("test-job")

        assert status["status"] == "error"
        assert "error" in status

    @pytest.mark.asyncio
    async def test_run_kubectl_command_success(self, service):
        """Test running kubectl command successfully."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await service._run_kubectl_command(["kubectl", "get", "pods"])

        assert result.returncode == 0
        assert result.stdout == b"output"
        assert result.stderr == b""

    @pytest.mark.asyncio
    async def test_run_kubectl_command_timeout(self, service):
        """Test kubectl command timeout."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(RuntimeError, match="kubectl command timed out"):
                await service._run_kubectl_command(["kubectl", "get", "pods"])

    @pytest.mark.asyncio
    async def test_wait_for_job_pods_success(self, service):
        """Test waiting for job pods successfully."""
        with patch.object(
            service,
            "_get_job_pods",
            new=AsyncMock(side_effect=[[], ["pod-1", "pod-2"]]),
        ):
            await service._wait_for_job_pods("test-job", timeout=10)

    @pytest.mark.asyncio
    async def test_wait_for_job_pods_timeout(self, service):
        """Test waiting for job pods timeout."""
        with patch.object(service, "_get_job_pods", new=AsyncMock(return_value=[])):
            with patch("asyncio.sleep", new=AsyncMock()):
                with pytest.raises(RuntimeError, match="Timeout waiting for pods"):
                    await service._wait_for_job_pods("test-job", timeout=0.1)

    @pytest.mark.asyncio
    async def test_get_job_pods_success(self, service):
        """Test getting job pods successfully."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"pod-1 pod-2 pod-3"

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            pods = await service._get_job_pods("test-job")

        assert pods == ["pod-1", "pod-2", "pod-3"]

    @pytest.mark.asyncio
    async def test_get_job_pods_empty(self, service):
        """Test getting job pods when none exist."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = b"  "

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            pods = await service._get_job_pods("test-job")

        assert pods == []

    @pytest.mark.asyncio
    async def test_get_job_pods_error(self, service):
        """Test getting job pods when kubectl fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = b"error"

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_result)
        ):
            pods = await service._get_job_pods("test-job")

        assert pods == []

    def test_extract_variation_id_valid(self, service):
        """Test extracting variation ID from valid pod names."""
        assert service._extract_variation_id("agent-run123-0-abc") == 0
        assert service._extract_variation_id("agent-run123-5-xyz") == 5
        assert service._extract_variation_id("batch-run456-3-def") == 3

    def test_extract_variation_id_invalid(self, service):
        """Test extracting variation ID from invalid pod names."""
        assert service._extract_variation_id("invalid-pod") is None
        assert service._extract_variation_id("agent-run123-abc-def") is None
        assert service._extract_variation_id("short") is None

    def test_determine_job_status_succeeded(self, service):
        """Test determining job status as succeeded."""
        status = {"succeeded": 1, "failed": 0, "active": 0}
        assert service._determine_job_status(status) == "completed"

    def test_determine_job_status_failed(self, service):
        """Test determining job status as failed."""
        status = {"succeeded": 0, "failed": 1, "active": 0}
        assert service._determine_job_status(status) == "failed"

    def test_determine_job_status_running(self, service):
        """Test determining job status as running."""
        status = {"succeeded": 0, "failed": 0, "active": 2}
        assert service._determine_job_status(status) == "running"

    def test_determine_job_status_pending(self, service):
        """Test determining job status as pending."""
        status = {"succeeded": 0, "failed": 0, "active": 0}
        assert service._determine_job_status(status) == "pending"

    def test_determine_job_status_empty(self, service):
        """Test determining job status with empty status."""
        assert service._determine_job_status({}) == "pending"

    @pytest.mark.asyncio
    async def test_create_agent_job_special_characters(
        self, service, mock_subprocess_result
    ):
        """Test creating job with special characters in prompt."""
        prompt = 'Test "prompt" with\nnewlines and: special chars'

        with patch("builtins.open", mock_open(read_data="template")):
            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                import os
                import tempfile

                fd, temp_file_path = tempfile.mkstemp(suffix="_agent_special_test.yaml")
                os.close(fd)
                mock_temp.return_value.__enter__.return_value.name = temp_file_path

                with patch.object(
                    service,
                    "_run_kubectl_command",
                    new=AsyncMock(return_value=mock_subprocess_result),
                ):
                    with patch("os.unlink"):
                        job_name = await service.create_agent_job(
                            run_id="test",
                            variation_id=0,
                            repo_url="https://github.com/test/repo",
                            prompt=prompt,
                        )

        assert job_name == "agent-test-0"

    @pytest.mark.asyncio
    async def test_cancel_run_partial_failure(self, service):
        """Test canceling a run when some deletions fail."""
        jobs_data = {
            "items": [
                {"metadata": {"name": "job-1"}},
                {"metadata": {"name": "job-2"}},
            ]
        }
        mock_get_result = Mock()
        mock_get_result.returncode = 0
        mock_get_result.stdout = json.dumps(jobs_data).encode()

        with patch.object(
            service, "_run_kubectl_command", new=AsyncMock(return_value=mock_get_result)
        ):
            with patch.object(
                service, "delete_job", new=AsyncMock(side_effect=[True, False])
            ):
                result = await service.cancel_run("test-run")

        assert result is False  # Partial failure
