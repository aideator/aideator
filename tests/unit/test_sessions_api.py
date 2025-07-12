"""Tests for sessions API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.sessions import router
from app.models.session import Preference, Session, Turn
from app.models.user import User
from app.schemas.session import (
    PreferenceCreate,
    SessionCreate,
    SessionUpdate,
    TurnCreate,
)


class TestSessionsEndpoints:
    """Test sessions API endpoints."""

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
    def mock_session(self):
        """Create a mock session."""
        session = Mock(spec=Session)
        session.id = "test-session-123"
        session.user_id = "test-user-123"
        session.title = "Test Session"
        session.description = "Test Description"
        session.models_used = ["gpt-4", "claude-3"]
        session.is_active = True
        session.is_archived = False
        session.created_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.last_activity_at = datetime.utcnow()
        session.total_turns = 5
        session.total_cost = 0.25
        return session

    @pytest.fixture
    def mock_turn(self):
        """Create a mock turn."""
        turn = Mock(spec=Turn)
        turn.id = str(uuid4())
        turn.session_id = "test-session-123"
        turn.turn_number = 1
        turn.prompt = "Test prompt"
        turn.context = "Test context"
        turn.models_requested = ["gpt-4", "claude-3"]
        turn.responses = {
            "gpt-4": {"content": "GPT-4 response", "tokens": 100},
            "claude-3": {"content": "Claude response", "tokens": 120},
        }
        turn.started_at = datetime.utcnow()
        turn.completed_at = datetime.utcnow()
        turn.duration_seconds = 1.5
        turn.total_cost = 0.05
        turn.status = "completed"
        return turn

    @pytest.fixture
    def mock_preference(self):
        """Create a mock preference."""
        pref = Mock(spec=Preference)
        pref.id = str(uuid4())
        pref.user_id = "test-user-123"
        pref.session_id = "test-session-123"
        pref.turn_id = "test-turn-123"
        pref.preferred_model = "gpt-4"
        pref.preferred_response_id = "response-123"
        pref.compared_models = ["gpt-4", "claude-3"]
        pref.response_quality_scores = {"gpt-4": 5, "claude-3": 4}
        pref.feedback_text = "GPT-4 provided better code"
        pref.confidence_score = 4
        pref.preference_type = "response"
        pref.created_at = datetime.utcnow()
        return pref

    @pytest.mark.asyncio
    async def test_get_sessions(self, mock_db, mock_user, mock_session):
        """Test getting user sessions with pagination."""
        # Mock database queries
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=1)),  # total count
            Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_session])))
            ),  # sessions
        ]

        from app.api.v1.sessions import get_sessions

        result = await get_sessions(
            current_user=mock_user,
            db=mock_db,
            skip=0,
            limit=100,
            active_only=False,
            archived_only=False,
        )

        assert result.total == 1
        assert len(result.sessions) == 1
        assert result.sessions[0].id == "test-session-123"
        assert result.limit == 100
        assert result.offset == 0

    @pytest.mark.asyncio
    async def test_get_sessions_active_only(self, mock_db, mock_user, mock_session):
        """Test getting only active sessions."""
        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=1)),
            Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_session])))
            ),
        ]

        from app.api.v1.sessions import get_sessions

        result = await get_sessions(
            current_user=mock_user,
            db=mock_db,
            skip=0,
            limit=10,
            active_only=True,
            archived_only=False,
        )

        assert result.total == 1
        assert result.sessions[0].is_active is True

    @pytest.mark.asyncio
    async def test_get_sessions_archived_only(self, mock_db, mock_user):
        """Test getting only archived sessions."""
        archived_session = Mock(spec=Session)
        archived_session.id = "archived-123"
        archived_session.is_archived = True
        archived_session.is_active = False
        archived_session.user_id = "test-user-123"
        archived_session.title = "Archived Session"
        archived_session.description = "Archived Description"
        archived_session.models_used = []
        archived_session.created_at = datetime.utcnow()
        archived_session.updated_at = datetime.utcnow()
        archived_session.last_activity_at = datetime.utcnow()
        archived_session.total_turns = 0
        archived_session.total_cost = 0

        mock_db.execute.side_effect = [
            Mock(scalar=Mock(return_value=1)),
            Mock(
                scalars=Mock(
                    return_value=Mock(all=Mock(return_value=[archived_session]))
                )
            ),
        ]

        from app.api.v1.sessions import get_sessions

        result = await get_sessions(
            current_user=mock_user,
            db=mock_db,
            skip=0,
            limit=100,
            active_only=False,
            archived_only=True,
        )

        assert result.sessions[0].is_archived is True

    @pytest.mark.asyncio
    async def test_create_session(self, mock_db, mock_user):
        """Test creating a new session."""
        session_data = SessionCreate(
            title="New Session",
            description="Test Description",
            models_used=["gpt-4", "claude-3"],
        )

        # Mock the created session
        created_session = Mock(spec=Session)
        created_session.id = "new-session-123"
        created_session.user_id = mock_user.id
        created_session.title = session_data.title
        created_session.description = session_data.description
        created_session.models_used = session_data.models_used
        created_session.is_active = True
        created_session.is_archived = False
        created_session.created_at = datetime.utcnow()
        created_session.updated_at = datetime.utcnow()
        created_session.last_activity_at = datetime.utcnow()
        created_session.total_turns = 0
        created_session.total_cost = 0

        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Patch uuid4 to return predictable ID
        with patch("app.api.v1.sessions.uuid4", return_value="new-session-123"):
            # Mock the session creation
            def add_side_effect(session):
                session.id = "new-session-123"
                session.created_at = created_session.created_at
                session.updated_at = created_session.updated_at
                session.last_activity_at = created_session.last_activity_at
                session.total_turns = 0
                session.total_cost = 0
                session.is_active = True
                session.is_archived = False

            mock_db.add.side_effect = add_side_effect

            from app.api.v1.sessions import create_session

            result = await create_session(
                session_data=session_data, current_user=mock_user, db=mock_db
            )

            assert result.id == "new-session-123"
            assert result.title == "New Session"
            assert result.models_used == ["gpt-4", "claude-3"]
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_by_id(self, mock_db, mock_user, mock_session):
        """Test getting a specific session."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

        from app.api.v1.sessions import get_session

        result = await get_session(
            session_id="test-session-123", current_user=mock_user, db=mock_db
        )

        assert result.id == "test-session-123"
        assert result.title == "Test Session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_db, mock_user):
        """Test getting non-existent session."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.api.v1.sessions import get_session

        with pytest.raises(HTTPException) as exc_info:
            await get_session(
                session_id="non-existent", current_user=mock_user, db=mock_db
            )

        assert exc_info.value.status_code == 404
        assert "Session not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_session(self, mock_db, mock_user, mock_session):
        """Test updating a session."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        update_data = SessionUpdate(
            title="Updated Title", description="Updated Description"
        )

        from app.api.v1.sessions import update_session

        await update_session(
            session_id="test-session-123",
            session_update=update_data,
            current_user=mock_user,
            db=mock_db,
        )

        assert mock_session.title == "Updated Title"
        assert mock_session.description == "Updated Description"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session(self, mock_db, mock_user, mock_session):
        """Test deleting a session."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        from app.api.v1.sessions import delete_session

        result = await delete_session(
            session_id="test-session-123", current_user=mock_user, db=mock_db
        )

        assert result["message"] == "Session deleted successfully"
        mock_db.delete.assert_called_once_with(mock_session)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_turn(self, mock_db, mock_user, mock_session):
        """Test adding a turn to a session."""
        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_session)),  # get session
            Mock(scalar=Mock(return_value=2)),  # get turn count
        ]
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        turn_data = TurnCreate(
            prompt="Test prompt",
            context="Test context",
            models_requested=["gpt-4", "claude-3"],
        )

        # Mock turn creation
        created_turn = Mock()
        created_turn.id = "new-turn-123"
        created_turn.turn_number = 3
        created_turn.session_id = "test-session-123"
        created_turn.prompt = turn_data.prompt
        created_turn.context = turn_data.context
        created_turn.models_requested = turn_data.models_requested
        created_turn.started_at = datetime.utcnow()
        created_turn.responses = {}
        created_turn.completed_at = None
        created_turn.duration_seconds = None
        created_turn.total_cost = 0.0
        created_turn.status = "pending"

        def add_side_effect(turn):
            turn.id = created_turn.id
            turn.turn_number = created_turn.turn_number
            turn.started_at = created_turn.started_at

        mock_db.add.side_effect = add_side_effect

        from app.api.v1.sessions import create_turn

        result = await create_turn(
            session_id="test-session-123",
            turn_data=turn_data,
            current_user=mock_user,
            db=mock_db,
        )

        assert result.turn_number == 3
        assert result.prompt == "Test prompt"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_turns(self, mock_db, mock_user, mock_session, mock_turn):
        """Test getting turns for a session."""
        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_session)),  # get session
            Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_turn])))
            ),  # get turns
        ]

        from app.api.v1.sessions import get_session_turns

        result = await get_session_turns(
            session_id="test-session-123",
            current_user=mock_user,
            db=mock_db,
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_add_preference(self, mock_db, mock_user, mock_session):
        """Test adding a preference."""
        mock_turn = Mock()
        mock_turn.id = "test-turn-123"

        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_session)),  # get session
            Mock(scalar_one_or_none=Mock(return_value=mock_turn)),  # get turn
        ]
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        pref_data = PreferenceCreate(
            preferred_model="gpt-4",
            preferred_response_id="response-123",
            compared_models=["gpt-4", "claude-3"],
            response_quality_scores={"gpt-4": 5, "claude-3": 4},
            feedback_text="Better response",
            confidence_score=4,
        )

        created_pref = Mock()
        created_pref.id = "new-pref-123"
        created_pref.session_id = "test-session-123"
        created_pref.turn_id = "test-turn-123"
        created_pref.preferred_model = pref_data.preferred_model
        created_pref.preferred_response_id = pref_data.preferred_response_id
        created_pref.compared_models = pref_data.compared_models
        created_pref.response_quality_scores = pref_data.response_quality_scores
        created_pref.feedback_text = pref_data.feedback_text
        created_pref.confidence_score = pref_data.confidence_score
        created_pref.created_at = datetime.utcnow()

        def add_side_effect(pref):
            pref.id = created_pref.id
            pref.created_at = created_pref.created_at

        mock_db.add.side_effect = add_side_effect

        from app.api.v1.sessions import create_preference

        result = await create_preference(
            session_id="test-session-123",
            turn_id="test-turn-123",
            preference_data=pref_data,
            current_user=mock_user,
            db=mock_db,
        )

        assert result.preferred_model == "gpt-4"
        assert result.confidence_score == 4
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_analytics(self, mock_db, mock_user, mock_session):
        """Test getting session analytics."""
        # Mock turns and preferences
        mock_turn1 = Mock()
        mock_turn1.total_cost = 0.15
        mock_turn2 = Mock()
        mock_turn2.total_cost = 0.10

        mock_pref1 = Mock()
        mock_pref1.preferred_model = "gpt-4"
        mock_pref2 = Mock()
        mock_pref2.preferred_model = "claude-3"

        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_session)),  # get session
            Mock(
                scalars=Mock(
                    return_value=Mock(all=Mock(return_value=[mock_turn1, mock_turn2]))
                )
            ),  # get turns
            Mock(
                scalars=Mock(
                    return_value=Mock(all=Mock(return_value=[mock_pref1, mock_pref2]))
                )
            ),  # get preferences
        ]

        from app.api.v1.sessions import get_session_analytics

        result = await get_session_analytics(
            session_id="test-session-123", current_user=mock_user, db=mock_db
        )

        assert result.total_turns == 2
        assert result.total_cost == 0.25

    @pytest.mark.asyncio
    async def test_export_session(
        self, mock_db, mock_user, mock_session, mock_turn, mock_preference
    ):
        """Test exporting a session."""
        mock_db.execute.side_effect = [
            Mock(scalar_one_or_none=Mock(return_value=mock_session)),  # get session
            Mock(
                scalars=Mock(return_value=Mock(all=Mock(return_value=[mock_turn])))
            ),  # get turns
            Mock(
                scalars=Mock(
                    return_value=Mock(all=Mock(return_value=[mock_preference]))
                )
            ),  # get preferences
        ]

        from app.api.v1.sessions import export_session

        result = await export_session(
            session_id="test-session-123",
            current_user=mock_user,
            db=mock_db,
            export_format="json",
        )

        assert result.session.id == "test-session-123"
        assert len(result.turns) == 1
        assert len(result.preferences) == 1
        assert result.export_format == "json"

    def test_router_exists(self):
        """Test that router is properly configured."""
        assert router is not None
        routes = [route.path for route in router.routes]
        assert "/sessions/" in routes
        assert "/sessions/{session_id}" in routes
        assert "/sessions/{session_id}/turns" in routes
        assert "/sessions/{session_id}/preferences" in routes
        assert "/sessions/{session_id}/analytics" in routes
        assert "/sessions/{session_id}/export" in routes
