"""Tests for admin messaging API endpoints."""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import and_, delete, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin_messaging import router
from app.models.run import AgentOutput, Run, RunStatus
from app.models.user import User


class TestAdminMessagingEndpoints:
    """Test admin messaging API endpoints."""

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
    def mock_run(self):
        """Create a mock run."""
        run = Mock(spec=Run)
        run.id = "test-run-123"
        run.status = RunStatus.RUNNING
        run.github_url = "https://github.com/test/repo"
        run.prompt = "Test prompt"
        run.variations = 3
        run.created_at = datetime.utcnow()
        run.started_at = datetime.utcnow()
        run.winning_variation_id = None
        return run

    @pytest.fixture
    def mock_agent_output(self):
        """Create a mock agent output."""
        output = Mock(spec=AgentOutput)
        output.id = "test-output-123"
        output.run_id = "test-run-123"
        output.variation_id = 1
        output.content = "Test content"
        output.output_type = "agent"
        output.timestamp = datetime.utcnow()
        return output

    @pytest.mark.asyncio
    async def test_get_database_stats(self, mock_db, mock_user):
        """Test getting database statistics."""
        # Mock database queries
        mock_db.scalar.side_effect = [
            10,  # total runs
            25,  # total messages
            3,  # recent runs
            8,  # recent messages
            1024000,  # database size
        ]

        # Mock status counts
        mock_status_result = [
            (RunStatus.COMPLETED, 5),
            (RunStatus.RUNNING, 2),
            (RunStatus.FAILED, 3),
        ]
        mock_db.execute.side_effect = [
            mock_status_result,  # status counts - direct iterable
            [("agent", 20), ("system", 5)],  # message type counts - direct iterable
            Mock(scalar=Mock(return_value=1024000)),  # db size
        ]

        # Import and call endpoint
        from app.api.v1.admin_messaging import get_database_stats

        result = await get_database_stats(db=mock_db, current_user=mock_user)

        # Verify result
        assert result["total_runs"] == 10
        assert result["runs_by_status"] == {
            "completed": 5,
            "running": 2,
            "failed": 3,
        }
        assert result["total_messages"] == 25
        assert result["messages_by_type"] == {"agent": 20, "system": 5}
        assert result["recent_runs_24h"] == 3
        assert result["recent_messages_24h"] == 8
        assert result["database_size_bytes"] == 1024000
        assert result["average_messages_per_run"] == 2.5

    @pytest.mark.asyncio
    async def test_get_database_stats_with_db_error(self, mock_db, mock_user):
        """Test database stats with database size error."""
        # Mock database queries
        mock_db.scalar.side_effect = [
            10,  # total runs
            25,  # total messages
            3,  # recent runs
            8,  # recent messages
        ]

        # Mock execute to raise exception for db size
        mock_db.execute.side_effect = [
            [(RunStatus.COMPLETED, 10)],  # direct iterable
            [("agent", 25)],  # direct iterable
            Exception("Database error"),
        ]

        from app.api.v1.admin_messaging import get_database_stats

        result = await get_database_stats(db=mock_db, current_user=mock_user)

        # Should handle error gracefully
        assert result["database_size_bytes"] == 0

    @pytest.mark.asyncio
    async def test_get_active_runs(self, mock_db, mock_user, mock_run):
        """Test getting active runs with metrics."""
        # Mock runs query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_run]
        mock_db.execute.side_effect = [
            mock_result,  # runs query
            [(1, 10, datetime.utcnow())],  # variation counts (direct iterable)
        ]

        from app.api.v1.admin_messaging import get_active_runs

        result = await get_active_runs(
            limit=20, include_completed=False, db=mock_db, current_user=mock_user
        )

        assert len(result) == 1
        assert result[0]["id"] == "test-run-123"
        assert result[0]["status"] == "running"
        assert result[0]["total_messages"] == 10
        assert "message_rate_per_second" in result[0]

    @pytest.mark.asyncio
    async def test_get_active_runs_include_completed(
        self, mock_db, mock_user, mock_run
    ):
        """Test getting active runs including completed."""
        mock_run.status = RunStatus.COMPLETED

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_run]
        mock_db.execute.side_effect = [
            mock_result,
            [],  # no messages (direct iterable)
        ]

        from app.api.v1.admin_messaging import get_active_runs

        result = await get_active_runs(
            limit=20, include_completed=True, db=mock_db, current_user=mock_user
        )

        assert len(result) == 1
        assert result[0]["message_rate_per_second"] == 0

    @pytest.mark.asyncio
    async def test_get_message_stream(self, mock_db, mock_user, mock_agent_output):
        """Test getting message stream."""
        # Mock count and messages
        mock_db.scalar.return_value = 1  # total count

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_agent_output]
        mock_db.execute.return_value = mock_result

        from app.api.v1.admin_messaging import get_message_stream

        result = await get_message_stream(
            limit=100,
            offset=0,
            run_id=None,
            variation_id=None,
            output_type=None,
            search=None,
            db=mock_db,
            current_user=mock_user,
        )

        assert result["total"] == 1
        assert len(result["messages"]) == 1
        assert result["messages"][0]["id"] == "test-output-123"

    @pytest.mark.asyncio
    async def test_get_message_stream_with_filters(
        self, mock_db, mock_user, mock_agent_output
    ):
        """Test message stream with all filters."""
        mock_db.scalar.return_value = 1

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_agent_output]
        mock_db.execute.return_value = mock_result

        from app.api.v1.admin_messaging import get_message_stream

        result = await get_message_stream(
            limit=50,
            offset=10,
            run_id="test-run-123",
            variation_id=1,
            output_type="agent",
            search="test",
            db=mock_db,
            current_user=mock_user,
        )

        assert result["limit"] == 50
        assert result["offset"] == 10

    @pytest.mark.asyncio
    async def test_search_messages(self, mock_db, mock_user, mock_agent_output):
        """Test searching messages."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_agent_output]
        mock_db.execute.return_value = mock_result

        from app.api.v1.admin_messaging import search_messages

        result = await search_messages(
            query="test",
            limit=50,
            run_id=None,
            output_type=None,
            db=mock_db,
            current_user=mock_user,
        )

        assert len(result) == 1
        assert result[0]["content"] == "Test content"
        assert "match_preview" in result[0]

    @pytest.mark.asyncio
    async def test_search_messages_with_filters(
        self, mock_db, mock_user, mock_agent_output
    ):
        """Test searching messages with filters."""
        # Make content longer to test preview
        mock_agent_output.content = "x" * 300

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_agent_output]
        mock_db.execute.return_value = mock_result

        from app.api.v1.admin_messaging import search_messages

        result = await search_messages(
            query="test",
            limit=20,
            run_id="test-run-123",
            output_type="agent",
            db=mock_db,
            current_user=mock_user,
        )

        assert len(result) == 1
        assert result[0]["match_preview"].endswith("...")
        assert len(result[0]["match_preview"]) == 203

    @pytest.mark.asyncio
    async def test_cleanup_database_dry_run(self, mock_db, mock_user):
        """Test database cleanup in dry run mode."""
        # Mock finding old runs
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([("old-run-1",), ("old-run-2",)]))
        mock_db.execute.return_value = mock_result

        # Mock message count
        mock_db.scalar.return_value = 100

        from app.api.v1.admin_messaging import cleanup_database

        result = await cleanup_database(
            older_than_days=7, dry_run=True, db=mock_db, current_user=mock_user
        )

        assert result["runs_affected"] == 2
        assert result["messages_affected"] == 100
        assert result["dry_run"] is True
        assert "Dry run" in result["message"]

        # Verify no actual deletions
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_database_actual_deletion(self, mock_db, mock_user):
        """Test database cleanup with actual deletion."""
        # Mock finding old runs
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([("old-run-1",)]))
        mock_db.execute.side_effect = [
            mock_result,  # find old runs
            None,  # delete messages
            None,  # delete runs
        ]

        mock_db.scalar.return_value = 50

        from app.api.v1.admin_messaging import cleanup_database

        result = await cleanup_database(
            older_than_days=30, dry_run=False, db=mock_db, current_user=mock_user
        )

        assert result["runs_affected"] == 1
        assert result["messages_affected"] == 50
        assert result["dry_run"] is False
        assert "Cleanup completed" in result["message"]

        # Verify commit was called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_database_no_old_runs(self, mock_db, mock_user):
        """Test cleanup when no old runs found."""
        # Mock no old runs
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_db.execute.return_value = mock_result

        from app.api.v1.admin_messaging import cleanup_database

        result = await cleanup_database(
            older_than_days=1, dry_run=False, db=mock_db, current_user=mock_user
        )

        assert result["runs_affected"] == 0
        assert result["messages_affected"] == 0
        assert "No old runs found" in result["message"]

    @pytest.mark.asyncio
    async def test_database_health(self, mock_db):
        """Test database health check."""
        # Mock successful async operations
        mock_db.execute = AsyncMock(return_value=None)  # SELECT 1
        mock_db.scalar = AsyncMock(return_value=10)  # count runs
        mock_db.flush = AsyncMock()
        mock_db.delete = AsyncMock()
        mock_db.add = Mock()

        from app.api.v1.admin_messaging import database_health

        result = await database_health(db=mock_db)

        assert result["healthy"] is True
        assert result["database_connection"] is True
        assert result["read_test"] is True
        assert result["write_test"] is True
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_database_health_with_failure(self, mock_db):
        """Test database health check with failures."""
        # Mock connection failure
        mock_db.execute.side_effect = Exception("Connection failed")

        from app.api.v1.admin_messaging import database_health

        result = await database_health(db=mock_db)

        assert result["healthy"] is False
        assert result["database_connection"] is False
        assert "error" in result
        assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_long_prompt_truncation(self, mock_db, mock_user, mock_run):
        """Test that long prompts are truncated in active runs."""
        # Make prompt longer than 100 chars
        mock_run.prompt = "x" * 150

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_run]
        mock_db.execute.side_effect = [
            mock_result,
            [],  # no messages (direct iterable)
        ]

        from app.api.v1.admin_messaging import get_active_runs

        result = await get_active_runs(
            limit=20, include_completed=False, db=mock_db, current_user=mock_user
        )

        assert len(result[0]["prompt"]) == 103  # 100 chars + "..."
        assert result[0]["prompt"].endswith("...")

    @pytest.mark.asyncio
    async def test_multiple_variations_metrics(self, mock_db, mock_user, mock_run):
        """Test metrics calculation with multiple variations."""
        # Mock multiple variations with different message counts
        variation_data = [
            (1, 10, datetime.utcnow()),
            (2, 15, datetime.utcnow() - timedelta(seconds=5)),
            (3, 5, datetime.utcnow() - timedelta(seconds=10)),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_run]
        mock_db.execute.side_effect = [
            mock_result,
            variation_data,  # direct iterable
        ]

        from app.api.v1.admin_messaging import get_active_runs

        result = await get_active_runs(
            limit=20, include_completed=False, db=mock_db, current_user=mock_user
        )

        assert result[0]["total_messages"] == 30  # 10 + 15 + 5
        assert len(result[0]["variation_metrics"]) == 3
