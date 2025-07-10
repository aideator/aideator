"""
Unit Tests for Runs API endpoints

This test suite covers the runs endpoints
to increase test coverage for app/api/v1/runs.py
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.runs import router
from app.models.run import Run, RunStatus
from app.models.user import User


class MockSettings:
    """Mock settings for testing."""
    api_v1_prefix = "/api/v1"
    max_variations = 5


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def app():
    """Create FastAPI app with runs router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/runs")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = User(
        id="user-123",
        email="test@example.com",
        username="testuser",
        is_active=True
    )
    return user


@pytest.fixture
def mock_run():
    """Create a mock run."""
    run = Run(
        id="run-123",
        user_id="user-123",
        github_url="https://github.com/test/repo",
        prompt="Test prompt",
        variations=3,
        status=RunStatus.RUNNING,
        created_at=datetime.utcnow()
    )
    return run


class TestRunsEndpoints:
    """Test runs endpoints."""

    @patch("app.api.v1.runs.settings", MockSettings())
    @patch("app.api.v1.runs.get_orchestrator")
    @patch("app.api.v1.runs.get_session")
    @patch("app.api.v1.runs.model_catalog")
    @pytest.mark.asyncio
    async def test_create_run_success(self, mock_catalog, mock_get_session, mock_get_orchestrator, client, mock_user):
        """Test successful run creation."""
        # Mock model catalog validation
        mock_catalog.validate_model_access.return_value = (True, "")

        # Mock orchestrator
        mock_orchestrator = MagicMock()
        mock_get_orchestrator.return_value = mock_orchestrator

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock existing session check
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing session
        mock_session.execute.return_value = mock_result

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Create run request
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Analyze this repository",
            "model_variants": [
                {"model_definition_id": "gpt-4"},
                {"model_definition_id": "claude-3"}
            ]
        }

        response = client.post("/api/v1/runs", json=run_data)

        assert response.status_code == 202
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "PENDING"
        assert data["stream_url"].endswith("/stream")
        assert data["variations"] == 2

        # Verify database operations
        assert mock_session.add.call_count >= 1  # Run and possibly session
        mock_session.commit.assert_called()

    @patch("app.api.v1.runs.settings", MockSettings())
    @patch("app.api.v1.runs.get_session")
    @patch("app.api.v1.runs.model_catalog")
    @pytest.mark.asyncio
    async def test_create_run_invalid_model(self, mock_catalog, mock_get_session, client, mock_user):
        """Test run creation with invalid model."""
        # Mock model catalog validation failure
        mock_catalog.validate_model_access.return_value = (False, "Model 'invalid-model' not found")

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Create run request with invalid model
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Analyze this repository",
            "model_variants": [
                {"model_definition_id": "invalid-model"}
            ]
        }

        response = client.post("/api/v1/runs", json=run_data)

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.runs.settings")
    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_create_run_too_many_variations(self, mock_get_session, mock_settings, client, mock_user):
        """Test run creation with too many variations."""
        # Configure settings
        mock_settings.max_variations = 3

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Create run request with too many variations
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Analyze this repository",
            "model_variants": [
                {"model_definition_id": "gpt-4"},
                {"model_definition_id": "claude-3"},
                {"model_definition_id": "gemini-pro"},
                {"model_definition_id": "llama-2"}
            ]
        }

        response = client.post("/api/v1/runs", json=run_data)

        assert response.status_code == 400
        assert "Too many variations" in response.json()["detail"]

    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_get_run_success(self, mock_get_session, client, mock_user, mock_run):
        """Test successful run retrieval."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = mock_run

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Get run
        response = client.get("/api/v1/runs/run-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "run-123"
        assert data["github_url"] == "https://github.com/test/repo"
        assert data["prompt"] == "Test prompt"
        assert data["status"] == "RUNNING"
        assert data["variations"] == 3

    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_get_run_not_found(self, mock_get_session, client, mock_user):
        """Test getting non-existent run."""
        # Mock database session - run not found
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = None

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Try to get non-existent run
        response = client.get("/api/v1/runs/nonexistent")

        assert response.status_code == 404
        assert "Run not found" in response.json()["detail"]

    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_get_run_wrong_user(self, mock_get_session, client, mock_user):
        """Test getting run belonging to another user."""
        # Create run for different user
        other_run = Run(
            id="run-456",
            user_id="other-user-id",
            github_url="https://github.com/test/repo",
            prompt="Test prompt",
            variations=3,
            status=RunStatus.RUNNING
        )

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = other_run

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Try to get another user's run
        response = client.get("/api/v1/runs/run-456")

        assert response.status_code == 404
        assert "Run not found" in response.json()["detail"]

    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_list_runs_success(self, mock_get_session, client, mock_user):
        """Test listing user's runs."""
        # Create mock runs
        mock_runs = [
            Run(
                id="run-1",
                user_id=mock_user.id,
                github_url="https://github.com/test/repo1",
                prompt="Prompt 1",
                variations=2,
                status=RunStatus.COMPLETED,
                created_at=datetime.utcnow()
            ),
            Run(
                id="run-2",
                user_id=mock_user.id,
                github_url="https://github.com/test/repo2",
                prompt="Prompt 2",
                variations=3,
                status=RunStatus.RUNNING,
                created_at=datetime.utcnow()
            )
        ]

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 2

        # Mock runs query
        runs_result = MagicMock()
        runs_result.scalars.return_value.all.return_value = mock_runs

        # Set up execute to return different results based on query
        mock_session.execute = AsyncMock(side_effect=[count_result, runs_result])

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # List runs
        response = client.get("/api/v1/runs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == "run-1"
        assert data["items"][1]["id"] == "run-2"

    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_select_winner_success(self, mock_get_session, client, mock_user, mock_run):
        """Test successful winner selection."""
        # Set run to completed status
        mock_run.status = RunStatus.COMPLETED

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = mock_run
        mock_session.commit = AsyncMock()

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Select winner
        winner_data = {
            "variation_id": 1,
            "feedback": "This was the best response"
        }

        response = client.post("/api/v1/runs/run-123/select-winner", json=winner_data)

        assert response.status_code == 200
        data = response.json()
        assert data["winner_variation_id"] == 1
        assert data["feedback"] == "This was the best response"

        # Verify run was updated
        assert mock_run.winner_variation_id == 1
        assert mock_run.feedback == "This was the best response"
        mock_session.commit.assert_called_once()

    @patch("app.api.v1.runs.get_session")
    @pytest.mark.asyncio
    async def test_select_winner_run_not_completed(self, mock_get_session, client, mock_user, mock_run):
        """Test selecting winner for non-completed run."""
        # Keep run in running status
        mock_run.status = RunStatus.RUNNING

        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.get.return_value = mock_run

        mock_get_session.return_value = mock_session

        # Mock current user dependency
        from app.core.dependencies import get_current_user_from_api_key
        app = client.app
        app.dependency_overrides[get_current_user_from_api_key] = lambda: mock_user

        # Try to select winner
        winner_data = {
            "variation_id": 1,
            "feedback": "This was the best"
        }

        response = client.post("/api/v1/runs/run-123/select-winner", json=winner_data)

        assert response.status_code == 400
        assert "Run is not completed" in response.json()["detail"]

    def test_runs_routes_registered(self, app):
        """Test that runs routes are properly registered."""
        routes = [route.path for route in app.routes]
        assert "/api/v1/runs" in routes
        assert "/api/v1/runs/{run_id}" in routes
        assert "/api/v1/runs/{run_id}/select-winner" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
