"""Tests for the sessions API endpoints."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.sessions import router
from app.models.session import Preference, Session, Turn
from app.models.user import User
from app.schemas.session import (
    PreferenceCreate,
    PreferenceResponse,
    SessionAnalytics,
    SessionCreate,
    SessionExport,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
    TurnCreate,
    TurnResponse,
)


class TestSessionsAPI:
    """Test the sessions API endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = "user_abc123"
        user.email = "developer@aideator.com"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def mock_session(self):
        """Create a mock session model."""
        session = Mock(spec=Session)
        session.id = "session_abc123"
        session.user_id = "user_abc123"
        session.title = "Machine Learning Discussion"
        session.description = "Exploring deep learning techniques"
        session.is_active = True
        session.is_archived = False
        session.models_used = ["gpt-4", "claude-3-sonnet"]
        session.total_turns = 5
        session.total_cost = 10.50
        session.created_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.last_activity_at = datetime.utcnow()
        return session

    @pytest.fixture
    def mock_turn(self):
        """Create a mock turn model."""
        turn = Mock(spec=Turn)
        turn.id = "turn_abc123"
        turn.session_id = "session_abc123"
        turn.user_id = "user_abc123"
        turn.turn_number = 1
        turn.prompt = "Explain neural networks"
        turn.context = "Discussing machine learning fundamentals"
        turn.models_requested = ["gpt-4", "claude-3-sonnet"]
        turn.total_cost = 2.50
        turn.created_at = datetime.utcnow()
        # Required fields for TurnResponse schema
        turn.responses = {
            "gpt-4": "Response from GPT-4",
            "claude-3-sonnet": "Response from Claude",
        }
        turn.started_at = datetime.utcnow()
        turn.completed_at = datetime.utcnow()
        turn.duration_seconds = 15.5
        turn.status = "completed"
        return turn

    @pytest.fixture
    def mock_preference(self):
        """Create a mock preference model."""
        preference = Mock(spec=Preference)
        preference.id = "pref_abc123"
        preference.user_id = "user_abc123"
        preference.session_id = "session_abc123"
        preference.turn_id = "turn_abc123"
        preference.preferred_model = "claude-3-sonnet"
        preference.preferred_response_id = "response_abc123"
        preference.compared_models = ["gpt-4", "claude-3-sonnet"]
        preference.response_quality_scores = {"gpt-4": 4, "claude-3-sonnet": 5}
        preference.confidence_score = 4
        preference.preference_type = "response"
        preference.created_at = datetime.utcnow()
        # Required fields for PreferenceResponse schema
        preference.feedback_text = "Claude provided a clearer explanation"
        return preference

    # Test get_sessions endpoint
    @pytest.mark.asyncio
    async def test_get_sessions_success(self, mock_user, mock_db_session, mock_session):
        """Test successful sessions retrieval."""
        from app.api.v1.sessions import get_sessions

        # Mock database query results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 10

        mock_sessions_result = Mock()
        mock_sessions_result.scalars.return_value.all.return_value = [mock_session]

        mock_db_session.execute.side_effect = [mock_count_result, mock_sessions_result]

        response = await get_sessions(
            current_user=mock_user,
            db=mock_db_session,
            skip=0,
            limit=100,
            active_only=False,
            archived_only=False,
        )

        assert isinstance(response, SessionListResponse)
        assert len(response.sessions) == 1
        assert response.total == 10
        assert response.limit == 100
        assert response.offset == 0

    @pytest.mark.asyncio
    async def test_get_sessions_with_active_filter(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test sessions retrieval with active filter."""
        from app.api.v1.sessions import get_sessions

        # Mock database query results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 5

        mock_sessions_result = Mock()
        mock_sessions_result.scalars.return_value.all.return_value = [mock_session]

        mock_db_session.execute.side_effect = [mock_count_result, mock_sessions_result]

        response = await get_sessions(
            current_user=mock_user,
            db=mock_db_session,
            skip=0,
            limit=100,
            active_only=True,
            archived_only=False,
        )

        assert isinstance(response, SessionListResponse)
        assert response.total == 5

    @pytest.mark.asyncio
    async def test_get_sessions_with_archived_filter(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test sessions retrieval with archived filter."""
        from app.api.v1.sessions import get_sessions

        # Mock database query results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2

        mock_sessions_result = Mock()
        mock_sessions_result.scalars.return_value.all.return_value = []

        mock_db_session.execute.side_effect = [mock_count_result, mock_sessions_result]

        response = await get_sessions(
            current_user=mock_user,
            db=mock_db_session,
            skip=0,
            limit=100,
            active_only=False,
            archived_only=True,
        )

        assert isinstance(response, SessionListResponse)
        assert response.total == 2
        assert len(response.sessions) == 0

    @pytest.mark.asyncio
    async def test_get_sessions_with_pagination(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test sessions retrieval with pagination."""
        from app.api.v1.sessions import get_sessions

        # Mock database query results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 25

        mock_sessions_result = Mock()
        mock_sessions_result.scalars.return_value.all.return_value = [mock_session]

        mock_db_session.execute.side_effect = [mock_count_result, mock_sessions_result]

        response = await get_sessions(
            current_user=mock_user,
            db=mock_db_session,
            skip=10,
            limit=5,
            active_only=False,
            archived_only=False,
        )

        assert isinstance(response, SessionListResponse)
        assert response.total == 25
        assert response.limit == 5
        assert response.offset == 10

    @pytest.mark.asyncio
    async def test_get_sessions_empty_count(self, mock_user, mock_db_session):
        """Test sessions retrieval when count is None."""
        from app.api.v1.sessions import get_sessions

        # Mock database query results with None count
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = None

        mock_sessions_result = Mock()
        mock_sessions_result.scalars.return_value.all.return_value = []

        mock_db_session.execute.side_effect = [mock_count_result, mock_sessions_result]

        response = await get_sessions(
            current_user=mock_user,
            db=mock_db_session,
            skip=0,
            limit=100,
            active_only=False,
            archived_only=False,
        )

        assert isinstance(response, SessionListResponse)
        assert response.total == 0  # Should default to 0 when None

    # Test create_session endpoint
    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_user, mock_db_session):
        """Test successful session creation."""
        from app.api.v1.sessions import create_session

        session_data = SessionCreate(
            title="AI Research Session",
            description="Exploring advanced AI techniques",
            models_used=["gpt-4", "claude-3-sonnet"],
        )

        with patch("app.api.v1.sessions.uuid4") as mock_uuid:
            mock_uuid.return_value = "new_session_id"

            response = await create_session(
                session_data=session_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        # Verify session was added and committed
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

        assert isinstance(response, SessionResponse)

    # Test get_session endpoint
    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_user, mock_db_session, mock_session):
        """Test successful session retrieval."""
        from app.api.v1.sessions import get_session

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        response = await get_session(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, SessionResponse)

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_user, mock_db_session):
        """Test session retrieval when session not found."""
        from app.api.v1.sessions import get_session

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_session(
                session_id="nonexistent_session",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test update_session endpoint
    @pytest.mark.asyncio
    async def test_update_session_success(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test successful session update."""
        from app.api.v1.sessions import update_session

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        session_update = SessionUpdate(
            title="Updated Session Title",
            description="Updated session description",
        )

        with patch("app.api.v1.sessions.datetime") as mock_datetime:
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            response = await update_session(
                session_id="session_abc123",
                session_update=session_update,
                current_user=mock_user,
                db=mock_db_session,
            )

        # Verify session was updated and committed
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

        assert isinstance(response, SessionResponse)

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, mock_user, mock_db_session):
        """Test session update when session not found."""
        from app.api.v1.sessions import update_session

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        session_update = SessionUpdate(title="Updated Title")

        with pytest.raises(HTTPException) as exc_info:
            await update_session(
                session_id="nonexistent_session",
                session_update=session_update,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test delete_session endpoint
    @pytest.mark.asyncio
    async def test_delete_session_success(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test successful session deletion."""
        from app.api.v1.sessions import delete_session

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        response = await delete_session(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        # Verify session was deleted and committed
        mock_db_session.delete.assert_called_once_with(mock_session)
        mock_db_session.commit.assert_called_once()

        assert response == {"message": "Session deleted successfully"}

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, mock_user, mock_db_session):
        """Test session deletion when session not found."""
        from app.api.v1.sessions import delete_session

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await delete_session(
                session_id="nonexistent_session",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test get_session_turns endpoint
    @pytest.mark.asyncio
    async def test_get_session_turns_success(
        self, mock_user, mock_db_session, mock_session, mock_turn
    ):
        """Test successful session turns retrieval."""
        from app.api.v1.sessions import get_session_turns

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_db_session.execute.side_effect = [mock_session_result, mock_turns_result]

        response = await get_session_turns(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], TurnResponse)

    @pytest.mark.asyncio
    async def test_get_session_turns_session_not_found(
        self, mock_user, mock_db_session
    ):
        """Test session turns retrieval when session not found."""
        from app.api.v1.sessions import get_session_turns

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_session_turns(
                session_id="nonexistent_session",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test create_turn endpoint
    @pytest.mark.asyncio
    async def test_create_turn_success(self, mock_user, mock_db_session, mock_session):
        """Test successful turn creation."""
        from app.api.v1.sessions import create_turn

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 2  # Existing turn count

        mock_db_session.execute.side_effect = [mock_session_result, mock_count_result]

        turn_data = TurnCreate(
            prompt="Explain gradient descent algorithms",
            context="Discussing optimization in machine learning",
            models_requested=["gpt-4", "claude-3-sonnet"],
        )

        with (
            patch("app.api.v1.sessions.uuid4") as mock_uuid,
            patch("app.api.v1.sessions.datetime") as mock_datetime,
        ):
            mock_uuid.return_value = "new_turn_id"
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            response = await create_turn(
                session_id="session_abc123",
                turn_data=turn_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        # Verify turn was added and session updated
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

        assert isinstance(response, TurnResponse)

    @pytest.mark.asyncio
    async def test_create_turn_session_not_found(self, mock_user, mock_db_session):
        """Test turn creation when session not found."""
        from app.api.v1.sessions import create_turn

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        turn_data = TurnCreate(
            prompt="Explain neural networks",
            models_requested=["gpt-4"],
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_turn(
                session_id="nonexistent_session",
                turn_data=turn_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_turn_with_zero_existing_turns(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test turn creation when no existing turns."""
        from app.api.v1.sessions import create_turn

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = None  # No existing turns

        mock_db_session.execute.side_effect = [mock_session_result, mock_count_result]

        turn_data = TurnCreate(
            prompt="What is artificial intelligence?",
            models_requested=["gpt-4"],
        )

        with (
            patch("app.api.v1.sessions.uuid4") as mock_uuid,
            patch("app.api.v1.sessions.datetime") as mock_datetime,
        ):
            mock_uuid.return_value = "first_turn_id"
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            response = await create_turn(
                session_id="session_abc123",
                turn_data=turn_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, TurnResponse)

    # Test get_turn endpoint
    @pytest.mark.asyncio
    async def test_get_turn_success(
        self, mock_user, mock_db_session, mock_session, mock_turn
    ):
        """Test successful turn retrieval."""
        from app.api.v1.sessions import get_turn

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turn_result = Mock()
        mock_turn_result.scalar_one_or_none.return_value = mock_turn

        mock_db_session.execute.side_effect = [mock_session_result, mock_turn_result]

        response = await get_turn(
            session_id="session_abc123",
            turn_id="turn_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, TurnResponse)

    @pytest.mark.asyncio
    async def test_get_turn_session_not_found(self, mock_user, mock_db_session):
        """Test turn retrieval when session not found."""
        from app.api.v1.sessions import get_turn

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_turn(
                session_id="nonexistent_session",
                turn_id="turn_abc123",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_turn_not_found(self, mock_user, mock_db_session, mock_session):
        """Test turn retrieval when turn not found."""
        from app.api.v1.sessions import get_turn

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turn_result = Mock()
        mock_turn_result.scalar_one_or_none.return_value = None

        mock_db_session.execute.side_effect = [mock_session_result, mock_turn_result]

        with pytest.raises(HTTPException) as exc_info:
            await get_turn(
                session_id="session_abc123",
                turn_id="nonexistent_turn",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Turn not found" in str(exc_info.value.detail)

    # Test create_preference endpoint
    @pytest.mark.asyncio
    async def test_create_preference_success(
        self, mock_user, mock_db_session, mock_session, mock_turn
    ):
        """Test successful preference creation."""
        from app.api.v1.sessions import create_preference

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turn_result = Mock()
        mock_turn_result.scalar_one_or_none.return_value = mock_turn

        mock_db_session.execute.side_effect = [mock_session_result, mock_turn_result]

        preference_data = PreferenceCreate(
            preferred_model="claude-3-sonnet",
            preferred_response_id="response_abc123",
            compared_models=["gpt-4", "claude-3-sonnet"],
            response_quality_scores={"gpt-4": 4, "claude-3-sonnet": 5},
            confidence_score=4,
        )

        with (
            patch("app.api.v1.sessions.uuid4") as mock_uuid,
            patch("app.api.v1.sessions.datetime") as mock_datetime,
        ):
            mock_uuid.return_value = "new_pref_id"
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            response = await create_preference(
                session_id="session_abc123",
                turn_id="turn_abc123",
                preference_data=preference_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        # Verify preference was added and session updated
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

        assert isinstance(response, PreferenceResponse)

    @pytest.mark.asyncio
    async def test_create_preference_session_not_found(
        self, mock_user, mock_db_session
    ):
        """Test preference creation when session not found."""
        from app.api.v1.sessions import create_preference

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        preference_data = PreferenceCreate(
            preferred_model="gpt-4",
            preferred_response_id="response_def456",
            compared_models=["gpt-4", "claude-3-sonnet"],
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_preference(
                session_id="nonexistent_session",
                turn_id="turn_abc123",
                preference_data=preference_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_preference_turn_not_found(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test preference creation when turn not found."""
        from app.api.v1.sessions import create_preference

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turn_result = Mock()
        mock_turn_result.scalar_one_or_none.return_value = None

        mock_db_session.execute.side_effect = [mock_session_result, mock_turn_result]

        preference_data = PreferenceCreate(
            preferred_model="gpt-4",
            preferred_response_id="response_def456",
            compared_models=["gpt-4", "claude-3-sonnet"],
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_preference(
                session_id="session_abc123",
                turn_id="nonexistent_turn",
                preference_data=preference_data,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Turn not found" in str(exc_info.value.detail)

    # Test get_session_preferences endpoint
    @pytest.mark.asyncio
    async def test_get_session_preferences_success(
        self, mock_user, mock_db_session, mock_session, mock_preference
    ):
        """Test successful session preferences retrieval."""
        from app.api.v1.sessions import get_session_preferences

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = [mock_preference]

        mock_db_session.execute.side_effect = [mock_session_result, mock_prefs_result]

        response = await get_session_preferences(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], PreferenceResponse)

    @pytest.mark.asyncio
    async def test_get_session_preferences_session_not_found(
        self, mock_user, mock_db_session
    ):
        """Test session preferences retrieval when session not found."""
        from app.api.v1.sessions import get_session_preferences

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_session_preferences(
                session_id="nonexistent_session",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test get_session_analytics endpoint
    @pytest.mark.asyncio
    async def test_get_session_analytics_success(
        self, mock_user, mock_db_session, mock_session, mock_turn, mock_preference
    ):
        """Test successful session analytics retrieval."""
        from app.api.v1.sessions import get_session_analytics

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = [mock_preference]

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await get_session_analytics(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, SessionAnalytics)
        assert response.total_sessions == 1
        assert response.total_turns == 1
        assert response.total_cost == 2.50
        assert response.average_cost_per_session == 2.50

    @pytest.mark.asyncio
    async def test_get_session_analytics_no_preferences(
        self, mock_user, mock_db_session, mock_session, mock_turn
    ):
        """Test session analytics when no preferences exist."""
        from app.api.v1.sessions import get_session_analytics

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = []  # No preferences

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await get_session_analytics(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, SessionAnalytics)
        assert response.total_turns == 1
        # Check model preference stats with empty preferences
        for model in mock_session.models_used:
            assert response.model_preference_stats[model]["wins"] == 0
            assert response.model_preference_stats[model]["win_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_session_analytics_session_not_found(
        self, mock_user, mock_db_session
    ):
        """Test session analytics when session not found."""
        from app.api.v1.sessions import get_session_analytics

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_session_analytics(
                session_id="nonexistent_session",
                current_user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test export_session endpoint
    @pytest.mark.asyncio
    async def test_export_session_success(
        self, mock_user, mock_db_session, mock_session, mock_turn, mock_preference
    ):
        """Test successful session export."""
        from app.api.v1.sessions import export_session

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = [mock_preference]

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await export_session(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
            export_format="json",
        )

        assert isinstance(response, SessionExport)
        assert isinstance(response.session, SessionResponse)
        assert len(response.turns) == 1
        assert len(response.preferences) == 1
        assert response.export_format == "json"

    @pytest.mark.asyncio
    async def test_export_session_markdown_format(
        self, mock_user, mock_db_session, mock_session, mock_turn, mock_preference
    ):
        """Test session export with markdown format."""
        from app.api.v1.sessions import export_session

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = [mock_preference]

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await export_session(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
            export_format="markdown",
        )

        assert isinstance(response, SessionExport)
        assert response.export_format == "markdown"

    @pytest.mark.asyncio
    async def test_export_session_csv_format(
        self, mock_user, mock_db_session, mock_session, mock_turn, mock_preference
    ):
        """Test session export with CSV format."""
        from app.api.v1.sessions import export_session

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = [mock_preference]

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await export_session(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
            export_format="csv",
        )

        assert isinstance(response, SessionExport)
        assert response.export_format == "csv"

    @pytest.mark.asyncio
    async def test_export_session_not_found(self, mock_user, mock_db_session):
        """Test session export when session not found."""
        from app.api.v1.sessions import export_session

        # Mock database query result - session not found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await export_session(
                session_id="nonexistent_session",
                current_user=mock_user,
                db=mock_db_session,
                export_format="json",
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    # Test router configuration
    def test_router_exists(self):
        """Test that the router is properly configured."""
        assert router is not None
        # Check that the router has the expected endpoints
        route_paths = [route.path for route in router.routes]
        assert "/sessions/" in route_paths
        assert "/sessions/{session_id}" in route_paths
        assert "/sessions/{session_id}/turns" in route_paths
        assert "/sessions/{session_id}/turns/{turn_id}" in route_paths
        assert "/sessions/{session_id}/turns/{turn_id}/preferences" in route_paths
        assert "/sessions/{session_id}/preferences" in route_paths
        assert "/sessions/{session_id}/analytics" in route_paths
        assert "/sessions/{session_id}/export" in route_paths

    # Additional edge case tests
    @pytest.mark.asyncio
    async def test_session_analytics_with_multiple_preferences(
        self, mock_user, mock_db_session, mock_session, mock_turn
    ):
        """Test session analytics with multiple preferences for the same model."""
        from app.api.v1.sessions import get_session_analytics

        # Create multiple preferences for different models
        pref1 = Mock(spec=Preference)
        pref1.preferred_model = "gpt-4"

        pref2 = Mock(spec=Preference)
        pref2.preferred_model = "claude-3-sonnet"

        pref3 = Mock(spec=Preference)
        pref3.preferred_model = "gpt-4"  # Another preference for gpt-4

        # Mock database query results
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = [mock_turn]

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = [pref1, pref2, pref3]

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await get_session_analytics(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
        )

        assert isinstance(response, SessionAnalytics)
        # gpt-4 should have 2 wins, claude-3-sonnet should have 1 win
        assert response.model_preference_stats["gpt-4"]["wins"] == 2
        assert response.model_preference_stats["claude-3-sonnet"]["wins"] == 1
        # Win rates should be calculated correctly (2/3 and 1/3)
        assert (
            abs(response.model_preference_stats["gpt-4"]["win_rate"] - (2 / 3)) < 0.01
        )
        assert (
            abs(
                response.model_preference_stats["claude-3-sonnet"]["win_rate"] - (1 / 3)
            )
            < 0.01
        )

    @pytest.mark.asyncio
    async def test_get_sessions_with_extreme_pagination(
        self, mock_user, mock_db_session
    ):
        """Test sessions retrieval with extreme pagination values."""
        from app.api.v1.sessions import get_sessions

        # Mock database query results
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1000

        mock_sessions_result = Mock()
        mock_sessions_result.scalars.return_value.all.return_value = []

        mock_db_session.execute.side_effect = [mock_count_result, mock_sessions_result]

        response = await get_sessions(
            current_user=mock_user,
            db=mock_db_session,
            skip=999,  # Large skip value
            limit=1000,  # Maximum limit
            active_only=False,
            archived_only=False,
        )

        assert isinstance(response, SessionListResponse)
        assert response.total == 1000
        assert response.limit == 1000
        assert response.offset == 999
        assert len(response.sessions) == 0

    @pytest.mark.asyncio
    async def test_session_update_partial_fields(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test session update with only some fields provided."""
        from app.api.v1.sessions import update_session

        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db_session.execute.return_value = mock_result

        # Update only the title, leave other fields unchanged
        session_update = SessionUpdate(title="Only Title Updated")

        with patch("app.api.v1.sessions.datetime") as mock_datetime:
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            response = await update_session(
                session_id="session_abc123",
                session_update=session_update,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, SessionResponse)

    @pytest.mark.asyncio
    async def test_export_session_empty_data(
        self, mock_user, mock_db_session, mock_session
    ):
        """Test session export when session has no turns or preferences."""
        from app.api.v1.sessions import export_session

        # Mock database query results with empty turns and preferences
        mock_session_result = Mock()
        mock_session_result.scalar_one_or_none.return_value = mock_session

        mock_turns_result = Mock()
        mock_turns_result.scalars.return_value.all.return_value = []  # No turns

        mock_prefs_result = Mock()
        mock_prefs_result.scalars.return_value.all.return_value = []  # No preferences

        mock_db_session.execute.side_effect = [
            mock_session_result,
            mock_turns_result,
            mock_prefs_result,
        ]

        response = await export_session(
            session_id="session_abc123",
            current_user=mock_user,
            db=mock_db_session,
            export_format="json",
        )

        assert isinstance(response, SessionExport)
        assert len(response.turns) == 0
        assert len(response.preferences) == 0
