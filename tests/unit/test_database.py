"""
Unit Tests for Database utilities

This test suite covers the database connection and session management
to increase test coverage for app/core/database.py
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    AsyncSessionFactory,
    async_session_maker,
    create_db_and_tables,
    engine,
    get_async_session,
    get_session,
)


@pytest.mark.asyncio
class TestDatabaseFunctions:
    """Test database utility functions."""

    async def test_get_session_success(self):
        """Test successful session creation and commit."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.async_session_maker") as mock_maker:
            # Setup the async context manager
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Get session
            async for session in get_session():
                assert session is mock_session

            # Verify commit was called
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()

    async def test_get_session_with_exception(self):
        """Test session rollback on exception."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.async_session_maker") as mock_maker:
            # Setup the async context manager
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Test with exception
            with pytest.raises(ValueError):
                async for session in get_session():
                    raise ValueError("Test error")

            # Verify rollback was called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()

    async def test_get_async_session_success(self):
        """Test async session creation without auto-commit."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.async_session_maker") as mock_maker:
            # Setup the async context manager
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Get session
            async for session in get_async_session():
                assert session is mock_session

            # Verify commit was NOT called (unlike get_session)
            mock_session.commit.assert_not_called()
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()

    async def test_get_async_session_with_exception(self):
        """Test async session rollback on exception."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.async_session_maker") as mock_maker:
            # Setup the async context manager
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Test with exception
            with pytest.raises(ValueError):
                async for session in get_async_session():
                    raise ValueError("Test error")

            # Verify rollback was called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @patch("app.core.database.logger")
    @patch("app.core.database.SQLModel")
    async def test_create_db_and_tables(self, mock_sqlmodel, mock_logger):
        """Test database table creation."""
        mock_conn = AsyncMock()

        with patch.object(engine, "begin") as mock_begin:
            # Setup async context manager for engine.begin()
            mock_begin.return_value.__aenter__.return_value = mock_conn
            mock_begin.return_value.__aexit__.return_value = None

            # Call the function
            await create_db_and_tables()

            # Verify run_sync was called with create_all
            mock_conn.run_sync.assert_called_once_with(mock_sqlmodel.metadata.create_all)

            # Verify logging
            mock_logger.info.assert_called_once_with("Database tables created")

    @patch("app.core.database.SQLModel")
    async def test_create_db_and_tables_error(self, mock_sqlmodel):
        """Test error handling in table creation."""
        mock_conn = AsyncMock()
        mock_conn.run_sync.side_effect = SQLAlchemyError("Database error")

        with patch.object(engine, "begin") as mock_begin:
            # Setup async context manager
            mock_begin.return_value.__aenter__.return_value = mock_conn
            mock_begin.return_value.__aexit__.return_value = None

            # Should raise the error
            with pytest.raises(SQLAlchemyError):
                await create_db_and_tables()


class TestDatabaseConfiguration:
    """Test database configuration and setup."""

    def test_engine_configuration(self):
        """Test that engine is configured correctly."""
        from app.core.database import engine, settings

        # Check engine URL matches settings
        assert str(engine.url) == settings.database_url_async

        # Check pool configuration
        assert engine.pool.size() == settings.database_pool_size
        assert engine.pool._recycle == settings.database_pool_recycle
        assert engine.pool._pre_ping is True
        assert engine.pool._timeout == 30
        assert engine.pool._max_overflow == 10

    def test_session_maker_configuration(self):
        """Test session maker configuration."""

        # Check session maker configuration
        assert async_session_maker.class_ is AsyncSession
        assert async_session_maker.expire_on_commit is False
        assert async_session_maker.autoflush is False
        assert async_session_maker.autocommit is False

    def test_async_session_factory_alias(self):
        """Test that AsyncSessionFactory is an alias for async_session_maker."""

        assert AsyncSessionFactory is async_session_maker

    def test_model_imports(self):
        """Test that all models are imported to register with SQLModel."""
        # These imports should not raise errors
        from app.models import APIKey, Preference, Run, Session, Turn, User

        assert User is not None
        assert APIKey is not None
        assert Run is not None
        assert Session is not None
        assert Turn is not None
        assert Preference is not None


class TestDatabaseSessionClosure:
    """Test proper session closure in edge cases."""

    @pytest.mark.asyncio
    async def test_get_session_ensures_closure(self):
        """Test that session is always closed even with unexpected errors."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = Exception("Commit failed")

        with patch("app.core.database.async_session_maker") as mock_maker:
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Should raise the commit error
            with pytest.raises(Exception, match="Commit failed"):
                async for session in get_session():
                    pass  # No exception in the loop itself

            # Session should still be closed
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_async_session_ensures_closure(self):
        """Test that async session is always closed."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch("app.core.database.async_session_maker") as mock_maker:
            mock_maker.return_value.__aenter__.return_value = mock_session
            mock_maker.return_value.__aexit__.return_value = None

            # Normal usage
            async for session in get_async_session():
                assert session is mock_session

            # Session should be closed
            mock_session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
