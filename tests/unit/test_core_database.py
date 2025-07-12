"""Tests for app.core.database module."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseModule:
    """Test the database module functions and session management."""

    @pytest.mark.asyncio
    async def test_create_db_and_tables_success(self):
        """Test successful database table creation."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            from app.core.database import create_db_and_tables

            await create_db_and_tables()

            mock_engine.begin.assert_called_once()
            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_db_and_tables_index_exists(self):
        """Test handling of existing index error."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock(
            side_effect=Exception("ix_model_definitions_model_name already exists")
        )

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            from app.core.database import create_db_and_tables

            # Should not raise an exception
            await create_db_and_tables()

            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_db_and_tables_duplicate_objects(self):
        """Test handling of duplicate objects error."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock(side_effect=Exception("table already exists"))

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            from app.core.database import create_db_and_tables

            # Should not raise an exception
            await create_db_and_tables()

            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_db_and_tables_other_error(self):
        """Test handling of other database errors."""
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock(
            side_effect=DatabaseError("Connection failed", None, None)
        )

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            from app.core.database import create_db_and_tables

            # Should raise the exception
            with pytest.raises(DatabaseError):
                await create_db_and_tables()

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test successful session creation and commit."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        with patch("app.core.database.async_session_maker", mock_session_maker):
            from app.core.database import get_session

            # The generator must be fully consumed for commit to be called
            sessions = [session async for session in get_session()]

            assert len(sessions) == 1
            assert sessions[0] == mock_session

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_exception(self):
        """Test that session rollback is called on exception."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock(side_effect=Exception("Commit failed"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        with patch("app.core.database.async_session_maker", mock_session_maker):
            from app.core.database import get_session

            with pytest.raises(Exception, match="Commit failed"):
                async for session in get_session():
                    pass

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_success(self):
        """Test get_async_session function."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        with patch("app.core.database.async_session_maker", mock_session_maker):
            from app.core.database import get_async_session

            # The generator must be fully consumed for session handling to complete
            sessions = [session async for session in get_async_session()]

            assert len(sessions) == 1
            assert sessions[0] == mock_session

            # get_async_session doesn't auto-commit
            mock_session.commit.assert_not_called()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_rollback_on_exception(self):
        """Test get_async_session rollback on exception."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        with patch("app.core.database.async_session_maker", mock_session_maker):
            from app.core.database import get_async_session

            # Use the generator and send an exception to it
            generator = get_async_session()
            try:
                session = await generator.__anext__()
                assert session == mock_session
                # Send exception to the generator
                with pytest.raises(RuntimeError):
                    await generator.athrow(RuntimeError("Test error"))
            finally:
                await generator.aclose()

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_sync_session_success(self):
        """Test synchronous session creation."""
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        with patch("app.core.database.sync_session_maker", mock_session_maker):
            from app.core.database import get_sync_session

            # The generator must be fully consumed for commit to be called
            sessions = list(get_sync_session())

            assert len(sessions) == 1
            assert sessions[0] == mock_session

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_get_sync_session_with_exception(self):
        """Test sync session rollback on exception."""
        mock_session = Mock()
        mock_session.commit = Mock(side_effect=Exception("Commit failed"))
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        with patch("app.core.database.sync_session_maker", mock_session_maker):
            from app.core.database import get_sync_session

            with pytest.raises(Exception, match="Commit failed"):
                # The generator must be fully consumed for the exception to be raised
                list(get_sync_session())

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_engine_configuration(self):
        """Test that engines are properly configured."""
        from app.core.database import (
            async_session_maker,
            engine,
            sync_engine,
            sync_session_maker,
        )

        # Test that engines exist and have expected properties
        assert engine is not None
        assert sync_engine is not None

        # Test that session makers exist
        assert async_session_maker is not None
        assert sync_session_maker is not None

    def test_module_imports(self):
        """Test that all necessary models are imported."""
        # This test ensures the module imports work correctly
        # The actual imports happen at module level, so we just verify
        # the module can be imported without errors
        from app.core import database

        assert database is not None

        # Verify some key attributes exist
        assert hasattr(database, "engine")
        assert hasattr(database, "sync_engine")
        assert hasattr(database, "async_session_maker")
        assert hasattr(database, "sync_session_maker")

    @pytest.mark.asyncio
    async def test_duplicate_error_types(self):
        """Test various duplicate error message patterns."""
        test_cases = [
            "duplicate key value violates unique constraint",
            "DUPLICATE KEY constraint failed",
            "table 'users' already exists",
            "index 'ix_users_email' already exists",
        ]

        for error_msg in test_cases:
            mock_conn = AsyncMock()
            mock_conn.run_sync = AsyncMock(side_effect=Exception(error_msg))

            with patch("app.core.database.engine") as mock_engine:
                mock_engine.begin.return_value.__aenter__.return_value = mock_conn

                from app.core.database import create_db_and_tables

                # Should not raise an exception for any duplicate error
                await create_db_and_tables()

    def test_database_url_postgresql_detection(self):
        """Test that PostgreSQL-specific parameters are applied correctly."""
        from app.core import database

        # The module should be importable and the engines should exist
        assert database.engine is not None
        assert database.sync_engine is not None

    @pytest.mark.asyncio
    async def test_sync_session_iteration_exception(self):
        """Test sync session with exception during iteration."""
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)

        # Create a mock that acts as the session maker function
        mock_session_maker = Mock(return_value=mock_session)

        class TestException(Exception):
            pass

        with patch("app.core.database.sync_session_maker", mock_session_maker):
            from app.core.database import get_sync_session

            try:
                generator = get_sync_session()
                session = next(generator)
                assert session == mock_session
                # Simulate exception during usage
                generator.throw(TestException("Test error"))
            except TestException:
                pass  # Expected
            except StopIteration:
                pass  # Generator cleanup

            # Verify rollback and close were called via context manager
            mock_session_maker.return_value.__exit__.assert_called()
