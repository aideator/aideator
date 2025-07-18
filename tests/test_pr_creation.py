"""
Tests for PR creation API endpoints and functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.task import Task, TaskOutput, TaskStatus
from app.services.github_pr_service import GitHubPRService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_task():
    return Task(
        id=1,
        github_url="https://github.com/test/repo",
        prompt="Test prompt",
        status=TaskStatus.COMPLETED,
        user_id="test-user",
        variations=1
    )


@pytest.fixture
def mock_task_output():
    return TaskOutput(
        id=1,
        task_id=1,
        variation_id=0,
        content='{"summary": "Test summary", "file_changes": [{"name": "test.py", "additions": 5, "deletions": 2}]}',
        output_type="job_summary"
    )


@pytest.fixture
def mock_diff_output():
    return TaskOutput(
        id=2,
        task_id=1,
        variation_id=0,
        content="<diff>test diff content</diff>",
        output_type="diffs"
    )


class TestPRCreationAPI:
    """Test PR creation API endpoints."""

    @pytest.mark.asyncio
    async def test_create_pr_with_valid_data(self, client, mock_task, mock_task_output, mock_diff_output):
        """Test successful PR creation with valid data."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session, \
             patch('app.api.v1.pull_requests.GitHubPRService') as mock_pr_service:
            
            # Mock database session
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            
            # Mock task query
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_task,  # Task query
                mock_task_output,  # Summary query
                mock_diff_output   # Diff query
            ]
            
            # Mock GitHub PR service
            mock_service_instance = MagicMock()
            mock_service_instance.create_pr.return_value = "https://github.com/test/repo/pull/123"
            mock_pr_service.return_value = mock_service_instance
            
            # Mock authentication
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    json={
                        "title": "Custom PR Title",
                        "description": "Custom PR description"
                    },
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert "pr_url" in data
                assert data["pr_url"] == "https://github.com/test/repo/pull/123"
                
                # Verify GitHub service was called with correct parameters
                mock_service_instance.create_pr.assert_called_once_with(
                    repo_http_url="https://github.com/test/repo",
                    title="Custom PR Title",
                    body="Custom PR description",
                    diff_content="<diff>test diff content</diff>"
                )

    @pytest.mark.asyncio
    async def test_create_pr_with_default_values(self, client, mock_task, mock_task_output, mock_diff_output):
        """Test PR creation with default title and description."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session, \
             patch('app.api.v1.pull_requests.GitHubPRService') as mock_pr_service:
            
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_task, mock_task_output, mock_diff_output
            ]
            
            mock_service_instance = MagicMock()
            mock_service_instance.create_pr.return_value = "https://github.com/test/repo/pull/123"
            mock_pr_service.return_value = mock_service_instance
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 201
                
                # Verify default values were used
                mock_service_instance.create_pr.assert_called_once_with(
                    repo_http_url="https://github.com/test/repo",
                    title="AIdeator – Task 1 Variation 1",
                    body="Test summary",
                    diff_content="<diff>test diff content</diff>"
                )

    @pytest.mark.asyncio
    async def test_create_pr_task_not_found(self, client):
        """Test PR creation with non-existent task."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/999/variations/0/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 404
                assert "Task not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_pr_access_denied(self, client, mock_task):
        """Test PR creation with insufficient access."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "different-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 403
                assert "Forbidden" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_pr_no_github_url(self, client):
        """Test PR creation for task without GitHub repository."""
        task_no_github = Task(
            id=1,
            github_url="",  # No GitHub URL
            prompt="Test prompt",
            status=TaskStatus.COMPLETED,
            user_id="test-user",
            variations=1
        )
        
        with patch('app.api.v1.pull_requests.get_session') as mock_session:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = task_no_github
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 400
                assert "not associated with a GitHub repository" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_pr_no_diff_data(self, client, mock_task, mock_task_output):
        """Test PR creation without diff data."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_task,      # Task query
                mock_task_output,  # Summary query
                None            # No diff data
            ]
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 400
                assert "No diff data found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_pr_github_service_error(self, client, mock_task, mock_task_output, mock_diff_output):
        """Test PR creation when GitHub service fails."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session, \
             patch('app.api.v1.pull_requests.GitHubPRService') as mock_pr_service:
            
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_task, mock_task_output, mock_diff_output
            ]
            
            # Mock GitHub service to raise an exception
            mock_service_instance = MagicMock()
            mock_service_instance.create_pr.side_effect = Exception("GitHub API error")
            mock_pr_service.return_value = mock_service_instance
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 500
                assert "Failed to create pull request" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_pr_invalid_variation_id(self, client, mock_task):
        """Test PR creation with invalid variation ID."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/999/pull-request",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 400
                assert "No diff data found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_pr_missing_authentication(self, client):
        """Test PR creation without authentication."""
        response = client.post("/api/v1/tasks/1/variations/0/pull-request")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_pr_invalid_request_body(self, client):
        """Test PR creation with invalid request body."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                # Test with invalid JSON
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    data="invalid json",
                    headers={"Authorization": "Bearer test-token", "Content-Type": "application/json"}
                )
                
                assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_pr_empty_title_and_description(self, client, mock_task, mock_task_output, mock_diff_output):
        """Test PR creation with empty title and description."""
        with patch('app.api.v1.pull_requests.get_session') as mock_session, \
             patch('app.api.v1.pull_requests.GitHubPRService') as mock_pr_service:
            
            mock_db = AsyncMock(spec=AsyncSession)
            mock_session.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_task, mock_task_output, mock_diff_output
            ]
            
            mock_service_instance = MagicMock()
            mock_service_instance.create_pr.return_value = "https://github.com/test/repo/pull/123"
            mock_pr_service.return_value = mock_service_instance
            
            with patch('app.api.v1.pull_requests.CurrentUser') as mock_user:
                mock_user.return_value.id = "test-user"
                
                response = client.post(
                    "/api/v1/tasks/1/variations/0/pull-request",
                    json={
                        "title": "",
                        "description": ""
                    },
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 201
                
                # Verify default values were used when empty strings provided
                mock_service_instance.create_pr.assert_called_once_with(
                    repo_http_url="https://github.com/test/repo",
                    title="AIdeator – Task 1 Variation 1",
                    body="Test summary",
                    diff_content="<diff>test diff content</diff>"
                )


class TestPRRequestValidation:
    """Test PR request validation."""

    def test_valid_pr_request(self):
        """Test valid PR request model."""
        from app.api.v1.pull_requests import PRCreateRequest
        
        request = PRCreateRequest(
            title="Test PR Title",
            description="Test PR description"
        )
        
        assert request.title == "Test PR Title"
        assert request.description == "Test PR description"

    def test_pr_request_with_none_values(self):
        """Test PR request with None values."""
        from app.api.v1.pull_requests import PRCreateRequest
        
        request = PRCreateRequest(
            title=None,
            description=None
        )
        
        assert request.title is None
        assert request.description is None

    def test_pr_request_default_values(self):
        """Test PR request with default values."""
        from app.api.v1.pull_requests import PRCreateRequest
        
        request = PRCreateRequest()
        
        assert request.title is None
        assert request.description is None


class TestGitHubPRServiceIntegration:
    """Test GitHub PR service integration."""

    @pytest.mark.asyncio
    async def test_github_service_initialization(self):
        """Test GitHub PR service initialization."""
        service = GitHubPRService("test-token")
        assert service.token == "test-token"
        assert "Authorization" in service._headers
        assert service._headers["Authorization"] == "token test-token"

    @pytest.mark.asyncio
    async def test_extract_owner_repo(self):
        """Test repository URL parsing."""
        # Test standard GitHub URL
        owner, repo = GitHubPRService._extract_owner_repo("https://github.com/test/repo")
        assert owner == "test"
        assert repo == "repo"
        
        # Test URL with .git extension
        owner, repo = GitHubPRService._extract_owner_repo("https://github.com/test/repo.git")
        assert owner == "test"
        assert repo == "repo"
        
        # Test URL with trailing slash
        owner, repo = GitHubPRService._extract_owner_repo("https://github.com/test/repo/")
        assert owner == "test"
        assert repo == "repo"

    @pytest.mark.asyncio
    async def test_extract_owner_repo_invalid_url(self):
        """Test repository URL parsing with invalid URL."""
        with pytest.raises(ValueError, match="Unable to parse repository owner/name from URL"):
            GitHubPRService._extract_owner_repo("invalid-url")

    @pytest.mark.asyncio
    async def test_build_patch_markdown(self):
        """Test markdown patch building."""
        title = "Test PR"
        summary = "Test summary"
        diff_block = "test diff"
        
        markdown = GitHubPRService._build_patch_markdown(title, summary, diff_block)
        
        assert title in markdown
        assert summary in markdown
        assert diff_block in markdown
        assert "```diff" in markdown
        assert "```" in markdown

    @pytest.mark.asyncio
    async def test_build_patch_markdown_with_empty_values(self):
        """Test markdown patch building with empty values."""
        title = "Test PR"
        summary = ""
        diff_block = ""
        
        markdown = GitHubPRService._build_patch_markdown(title, summary, diff_block)
        
        assert title in markdown
        assert "No summary available." in markdown
        assert "No diff available." in markdown