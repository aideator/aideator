"""
Tests for database initialization fix that handles duplicate index errors.

These tests verify that the database initialization gracefully handles
existing schema conflicts, specifically the duplicate index issue.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sqlalchemy.exc

from app.core.database import create_db_and_tables


class TestDatabaseInitializationFix:
    """Test the database initialization fix for duplicate index handling."""
    
    @pytest.mark.asyncio
    async def test_create_db_and_tables_success(self):
        """Test successful database table creation."""
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            await create_db_and_tables()
            
            # Verify engine.begin was called
            mock_engine.begin.assert_called_once()
            # Verify run_sync was called with create_all
            mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_db_handles_duplicate_model_definitions_index(self):
        """Test handling of specific duplicate model_definitions index error."""
        duplicate_index_error = sqlalchemy.exc.ProgrammingError(
            "CREATE UNIQUE INDEX ix_model_definitions_model_name ON model_definitions (model_name)",
            None,
            None
        )
        duplicate_index_error.args = ('relation "ix_model_definitions_model_name" already exists',)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = duplicate_index_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should not raise an exception
            await create_db_and_tables()
            
            # Verify the error was handled gracefully
            mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_db_handles_generic_duplicate_error(self):
        """Test handling of generic duplicate table/index errors."""
        duplicate_error = sqlalchemy.exc.ProgrammingError(
            "CREATE TABLE users",
            None,
            None
        )
        duplicate_error.args = ('table "users" already exists',)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = duplicate_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should not raise an exception
            await create_db_and_tables()
            
            # Verify the error was handled gracefully
            mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_db_raises_non_duplicate_errors(self):
        """Test that non-duplicate errors are still raised."""
        connection_error = sqlalchemy.exc.OperationalError(
            "could not connect to server",
            None,
            None
        )
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = connection_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should raise the original exception
            with pytest.raises(sqlalchemy.exc.OperationalError):
                await create_db_and_tables()
    
    @pytest.mark.asyncio
    async def test_create_db_handles_case_insensitive_duplicate_errors(self):
        """Test that duplicate error detection is case-insensitive."""
        duplicate_error = sqlalchemy.exc.ProgrammingError(
            "CREATE INDEX",
            None,
            None
        )
        duplicate_error.args = ('Index "some_index" ALREADY EXISTS',)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = duplicate_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should not raise an exception (case-insensitive detection)
            await create_db_and_tables()
            
            # Verify the error was handled gracefully
            mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_db_handles_duplicate_constraint_error(self):
        """Test handling of duplicate constraint errors."""
        duplicate_error = sqlalchemy.exc.ProgrammingError(
            "ALTER TABLE",
            None,
            None
        )
        duplicate_error.args = ('constraint "some_constraint" is a duplicate',)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = duplicate_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should not raise an exception
            await create_db_and_tables()
            
            # Verify the error was handled gracefully
            mock_conn.run_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_db_logs_appropriate_messages(self, caplog):
        """Test that appropriate log messages are generated."""
        import logging
        
        # Test successful creation
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            with caplog.at_level(logging.INFO):
                await create_db_and_tables()
            
            assert "Database tables created successfully" in caplog.text
        
        caplog.clear()
        
        # Test duplicate index handling
        duplicate_index_error = sqlalchemy.exc.ProgrammingError(
            "CREATE INDEX",
            None,
            None
        )
        duplicate_index_error.args = ('relation "ix_model_definitions_model_name" already exists',)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = duplicate_index_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            with caplog.at_level(logging.INFO):
                await create_db_and_tables()
            
            assert "Database index already exists, continuing with existing schema" in caplog.text


class TestDatabaseInitializationEdgeCases:
    """Test edge cases for database initialization."""
    
    @pytest.mark.asyncio
    async def test_create_db_handles_empty_error_message(self):
        """Test handling of errors with empty messages."""
        empty_error = sqlalchemy.exc.ProgrammingError("", None, None)
        empty_error.args = ('',)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = empty_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should raise the original exception since it's not a duplicate error
            with pytest.raises(sqlalchemy.exc.ProgrammingError):
                await create_db_and_tables()
    
    @pytest.mark.asyncio
    async def test_create_db_handles_none_error_args(self):
        """Test handling of errors with weird error messages."""
        # Create a custom exception that behaves like one with None args
        class WeirdError(sqlalchemy.exc.ProgrammingError):
            def __str__(self):
                return "weird error"
        
        weird_error = WeirdError("test", None, None)
        
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.run_sync.side_effect = weird_error
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_engine.begin.return_value.__aexit__.return_value = None
            
            # Should raise the original exception 
            with pytest.raises(WeirdError):
                await create_db_and_tables()
    
    @pytest.mark.asyncio
    async def test_create_db_multiple_error_conditions(self):
        """Test that multiple duplicate-related keywords are detected."""
        test_cases = [
            'relation "ix_test" already exists',
            'table "users" ALREADY EXISTS', 
            'index "idx_test" is a duplicate',
            'constraint "fk_test" DUPLICATE found',
        ]
        
        for error_msg in test_cases:
            duplicate_error = sqlalchemy.exc.ProgrammingError("test", None, None)
            duplicate_error.args = (error_msg,)
            
            with patch('app.core.database.engine') as mock_engine:
                mock_conn = AsyncMock()
                mock_conn.run_sync.side_effect = duplicate_error
                mock_engine.begin.return_value.__aenter__.return_value = mock_conn
                mock_engine.begin.return_value.__aexit__.return_value = None
                
                # Should not raise an exception for any of these cases
                await create_db_and_tables()
                
                # Verify the error was handled gracefully
                mock_conn.run_sync.assert_called_once()
                
                # Reset for next iteration
                mock_engine.reset_mock()