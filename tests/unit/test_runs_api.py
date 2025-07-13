"""Tests for runs API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.runs import router
from app.core.deps import get_orchestrator
from app.models.run import Run, RunStatus
from app.models.user import User
from app.schemas.runs import CreateRunRequest, SelectWinnerRequest
from app.services.agent_orchestrator import AgentOrchestrator


class TestRunsEndpoints:
    """Test runs API endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = "test-user-123"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock orchestrator."""
        orchestrator = Mock(spec=AgentOrchestrator)
        orchestrator.create_run = AsyncMock()
        orchestrator.cancel_run = AsyncMock()
        return orchestrator

    @pytest.fixture
    def mock_run(self):
        """Create a mock run."""
        run = Mock(spec=Run)
        run.id = "test-run-123"
        run.user_id = "test-user-123"
        run.github_url = "https://github.com/test/repo"
        run.prompt = "Test prompt"
        run.variations = 3
        run.model_count = 3  # Required for RunListItem schema
        run.variations = 3  # Original field name in model
        run.models_config = {
            "0": {"model": "gpt-4"},
            "1": {"model": "claude-3"},
            "2": {"model": "gemini-pro"},
        }
        run.status = RunStatus.RUNNING
        run.created_at = datetime.utcnow()
        run.started_at = datetime.utcnow()
        run.completed_at = None
        run.winning_variation_id = None
        run.error_message = None
        return run

    @pytest.mark.asyncio
    async def test_create_run_success(self, mock_db, mock_user, mock_orchestrator):
        """Test successful run creation."""
        request = CreateRunRequest(
            github_url="https://github.com/test/repo",
            prompt="Analyze this repository",
            model_variants=[
                {
                    "model_definition_id": "gpt-4",
                    "provider_credential_id": None,
                    "model_parameters": {},
                },
                {
                    "model_definition_id": "claude-3",
                    "provider_credential_id": None,
                    "model_parameters": {},
                },
                {
                    "model_definition_id": "gemini-pro",
                    "provider_credential_id": None,
                    "model_parameters": {},
                },
            ],
        )

        # Mock the created run
        created_run = Mock(spec=Run)
        created_run.id = "new-run-123"
        created_run.user_id = mock_user.id
        created_run.github_url = request.github_url
        created_run.prompt = request.prompt
        created_run.model_variants = len(request.model_variants)
        created_run.status = RunStatus.PENDING
        created_run.created_at = datetime.utcnow()
        created_run.started_at = None
        created_run.completed_at = None
        created_run.winning_variation_id = None
        created_run.error_message = None

        mock_orchestrator.create_run.return_value = created_run

        from app.api.v1.runs import create_run

        # Mock database queries for session/turn creation
        mock_db.execute.return_value.scalar = Mock(return_value=0)  # turn count
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock the model catalog
        with patch("app.api.v1.runs.model_catalog") as mock_catalog:
            mock_catalog.validate_model_access.return_value = (True, None)

            mock_background_tasks = Mock()
            result = await create_run(
                request=request,
                background_tasks=mock_background_tasks,
                current_user=mock_user,
                db=mock_db,
                orchestrator=mock_orchestrator,
            )

        assert result.run_id.startswith("run-")  # Auto-generated run ID
        assert result.websocket_url.startswith("ws://")
        assert result.status == "accepted"
        # Check that background task was added (orchestrator.execute_variations is called via background_tasks)
        mock_background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_run_with_different_prompt(
        self, mock_db, mock_user, mock_orchestrator
    ):
        """Test run creation with a different prompt."""
        request = CreateRunRequest(
            github_url="https://github.com/test/repo",
            prompt="Fix the bug",
            model_variants=[
                {
                    "model_definition_id": "gpt-4",
                    "provider_credential_id": None,
                    "model_parameters": {},
                },
                {
                    "model_definition_id": "claude-3",
                    "provider_credential_id": None,
                    "model_parameters": {},
                },
            ],
        )

        created_run = Mock(spec=Run)
        created_run.id = "new-run-123"
        created_run.status = RunStatus.PENDING
        created_run.github_url = request.github_url
        created_run.prompt = request.prompt
        created_run.model_variants = len(request.model_variants)
        created_run.user_id = mock_user.id
        created_run.created_at = datetime.utcnow()
        created_run.started_at = None
        created_run.completed_at = None
        created_run.winning_variation_id = None
        created_run.error_message = None

        mock_orchestrator.create_run.return_value = created_run

        from app.api.v1.runs import create_run

        # Mock database queries for session/turn creation
        mock_db.execute.return_value.scalar = Mock(return_value=0)  # turn count
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock the model catalog
        with patch("app.api.v1.runs.model_catalog") as mock_catalog:
            mock_catalog.validate_model_access.return_value = (True, None)

            mock_background_tasks = Mock()
            result = await create_run(
                request=request,
                background_tasks=mock_background_tasks,
                current_user=mock_user,
                db=mock_db,
                orchestrator=mock_orchestrator,
            )

        assert result.status == "accepted"

    @pytest.mark.asyncio
    async def test_list_runs(self, mock_db, mock_user, mock_run):
        """Test listing user runs with pagination."""
        # Mock database queries
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=1)),  # total count
            Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_run])))
            ),  # runs
        ]

        from app.api.v1.runs import list_runs

        result = await list_runs(
            status=None, page=1, per_page=10, current_user=mock_user, db=mock_db
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == "test-run-123"
        assert result.page == 1
        assert result.per_page == 10

    @pytest.mark.asyncio
    async def test_list_runs_with_status_filter(self, mock_db, mock_user, mock_run):
        """Test listing runs filtered by status."""
        mock_run.status = RunStatus.COMPLETED

        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=1)),
            Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_run])))),
        ]

        from app.api.v1.runs import list_runs

        result = await list_runs(
            status=RunStatus.COMPLETED,
            page=1,
            per_page=10,
            current_user=mock_user,
            db=mock_db,
        )

        assert len(result.items) == 1
        assert result.items[0].status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_run_by_id(self, mock_db, mock_user, mock_run):
        """Test getting a specific run."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result

        from app.api.v1.runs import get_run

        result = await get_run(
            run_id="test-run-123", current_user=mock_user, db=mock_db
        )

        assert result.id == "test-run-123"
        assert result.github_url == "https://github.com/test/repo"

    @pytest.mark.asyncio
    async def test_get_run_not_found(self, mock_db, mock_user):
        """Test getting non-existent run."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.api.v1.runs import get_run

        with pytest.raises(HTTPException) as exc_info:
            await get_run(run_id="non-existent", current_user=mock_user, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Run not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_select_winner(self, mock_db, mock_user, mock_run):
        """Test selecting winning variation."""
        mock_run.status = RunStatus.COMPLETED
        mock_run.variations = 3

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        request = SelectWinnerRequest(winning_variation_id=1)

        from app.api.v1.runs import select_winner

        await select_winner(
            run_id="test-run-123", request=request, current_user=mock_user, db=mock_db
        )

        assert mock_run.winning_variation_id == 1
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_winner_not_completed(self, mock_db, mock_user, mock_run):
        """Test selecting winner for non-completed run."""
        mock_run.status = RunStatus.RUNNING

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result

        request = SelectWinnerRequest(winning_variation_id=1)

        from app.api.v1.runs import select_winner

        with pytest.raises(HTTPException) as exc_info:
            await select_winner(
                run_id="test-run-123",
                request=request,
                current_user=mock_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Can only select winner for completed runs" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_select_winner_invalid_variation(self, mock_db, mock_user, mock_run):
        """Test selecting invalid variation ID."""
        mock_run.status = RunStatus.COMPLETED
        mock_run.variations = 3

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result

        request = SelectWinnerRequest(
            winning_variation_id=5
        )  # Invalid - only 0,1,2 are valid

        from app.api.v1.runs import select_winner

        with pytest.raises(HTTPException) as exc_info:
            await select_winner(
                run_id="test-run-123",
                request=request,
                current_user=mock_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid variation ID" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_cancel_run(self, mock_db, mock_user, mock_run, mock_orchestrator):
        """Test canceling a run."""
        mock_run.status = RunStatus.RUNNING

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        from app.api.v1.runs import cancel_run

        await cancel_run(
            run_id="test-run-123",
            current_user=mock_user,
            db=mock_db,
        )

        # The current implementation doesn't actually call the orchestrator
        # It just updates the database status to cancelled
        assert mock_run.status == RunStatus.CANCELLED
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_run_already_completed(
        self, mock_db, mock_user, mock_run, mock_orchestrator
    ):
        """Test canceling already completed run."""
        mock_run.status = RunStatus.COMPLETED

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_db.execute.return_value = mock_result

        from app.api.v1.runs import cancel_run

        with pytest.raises(HTTPException) as exc_info:
            await cancel_run(
                run_id="test-run-123",
                current_user=mock_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot cancel run with status" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_run_outputs(self, mock_db, mock_user):
        """Test getting run outputs."""
        # Mock outputs
        mock_output1 = Mock()
        mock_output1.id = "output-1"
        mock_output1.run_id = "test-run-123"
        mock_output1.variation_id = 0
        mock_output1.content = "Output from model 0"
        mock_output1.output_type = "agent"
        mock_output1.timestamp = datetime.utcnow()

        mock_output2 = Mock()
        mock_output2.id = "output-2"
        mock_output2.run_id = "test-run-123"
        mock_output2.variation_id = 1
        mock_output2.content = "Output from model 1"
        mock_output2.output_type = "agent"
        mock_output2.timestamp = datetime.utcnow()

        # Mock run existence check first, then outputs
        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=Mock())),  # run exists
            Mock(
                scalars=Mock(
                    return_value=Mock(
                        all=Mock(return_value=[mock_output1, mock_output2])
                    )
                )
            ),  # outputs
        ]

        from app.api.v1.runs import get_agent_outputs

        result = await get_agent_outputs(
            run_id="test-run-123",
            since=None,
            variation_id=None,
            output_type=None,
            limit=100,
            current_user=mock_user,
            db=mock_db,
        )

        assert len(result) == 2
        assert any(output["variation_id"] == 0 for output in result)
        assert any(output["variation_id"] == 1 for output in result)

    @pytest.mark.asyncio
    async def test_get_run_outputs_filtered(self, mock_db, mock_user):
        """Test getting run outputs for specific variation."""
        mock_output = Mock()
        mock_output.id = "output-1"
        mock_output.run_id = "test-run-123"
        mock_output.variation_id = 1
        mock_output.content = "Filtered output"
        mock_output.output_type = "agent"
        mock_output.timestamp = datetime.utcnow()

        # Mock run existence check first, then outputs
        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=Mock())),  # run exists
            Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_output])))
            ),  # outputs
        ]

        from app.api.v1.runs import get_agent_outputs

        result = await get_agent_outputs(
            run_id="test-run-123",
            since=None,
            variation_id=1,
            output_type=None,
            limit=100,
            current_user=mock_user,
            db=mock_db,
        )

        assert len(result) == 1
        assert result[0]["variation_id"] == 1

    def test_router_exists(self):
        """Test that router is properly configured."""
        assert router is not None
        routes = [route.path for route in router.routes]
        assert "" in routes  # Root route for list_runs and create_run
        assert "/{run_id}" in routes
        assert "/{run_id}/select" in routes
        assert "/{run_id}/outputs" in routes
