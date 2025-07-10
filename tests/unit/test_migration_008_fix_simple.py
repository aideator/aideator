"""Test migration 008 fix to verify it handles missing constraints gracefully."""
import pytest
from unittest.mock import Mock, patch
import importlib.util
import os


class TestMigration008Fix:
    """Test that migration 008 handles missing constraints gracefully."""

    def test_migration_handles_missing_model_variants_table(self):
        """Test that migration 008 works when model_variants table doesn't exist."""
        # Mock the database connection and result
        mock_connection = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = False  # Table doesn't exist
        mock_connection.execute.return_value = mock_result
        
        # Load the migration module
        migration_path = os.path.join(os.path.dirname(__file__), 
                                    "../../alembic/versions/008_update_model_definitions_schema.py")
        spec = importlib.util.spec_from_file_location("migration_008", migration_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Mock op.get_bind() to return our mock connection
        with patch('alembic.op.get_bind', return_value=mock_connection):
            with patch('alembic.op.drop_constraint') as mock_drop_constraint:
                with patch('alembic.op.create_table') as mock_create_table:
                    with patch('alembic.op.execute') as mock_execute:
                        with patch('alembic.op.drop_index') as mock_drop_index:
                            with patch('alembic.op.drop_table') as mock_drop_table:
                                with patch('alembic.op.rename_table') as mock_rename_table:
                                    with patch('alembic.op.create_index') as mock_create_index:
                                        # This should not raise an exception
                                        migration_module.upgrade()
                                        
                                        # Verify that drop_constraint was NOT called since table doesn't exist
                                        mock_drop_constraint.assert_not_called()
                                        
                                        # Verify that other operations were called
                                        mock_create_table.assert_called()

    def test_migration_handles_missing_constraint(self):
        """Test that migration 008 works when constraint doesn't exist."""
        # Mock the database connection and result
        mock_connection = Mock()
        
        # First call - table exists
        mock_result_table = Mock()
        mock_result_table.scalar.return_value = True
        
        # Second call - constraint doesn't exist
        mock_result_constraint = Mock()
        mock_result_constraint.scalar.return_value = False
        
        # Need a third call for counting existing records
        mock_result_count = Mock()
        mock_result_count.scalar.return_value = 0
        
        mock_connection.execute.side_effect = [mock_result_table, mock_result_constraint, mock_result_count]
        
        # Load the migration module
        migration_path = os.path.join(os.path.dirname(__file__), 
                                    "../../alembic/versions/008_update_model_definitions_schema.py")
        spec = importlib.util.spec_from_file_location("migration_008", migration_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Mock op.get_bind() to return our mock connection
        with patch('alembic.op.get_bind', return_value=mock_connection):
            with patch('alembic.op.drop_constraint') as mock_drop_constraint:
                with patch('alembic.op.create_table') as mock_create_table:
                    with patch('alembic.op.execute') as mock_execute:
                        with patch('alembic.op.drop_index') as mock_drop_index:
                            with patch('alembic.op.drop_table') as mock_drop_table:
                                with patch('alembic.op.rename_table') as mock_rename_table:
                                    with patch('alembic.op.create_index') as mock_create_index:
                                        # This should not raise an exception
                                        migration_module.upgrade()
                                        
                                        # Verify that drop_constraint was NOT called since constraint doesn't exist
                                        mock_drop_constraint.assert_not_called()

    def test_migration_drops_constraint_when_exists(self):
        """Test that migration 008 drops constraint when it exists."""
        # Mock the database connection and result
        mock_connection = Mock()
        
        # First call - table exists
        mock_result_table = Mock()
        mock_result_table.scalar.return_value = True
        
        # Second call - constraint exists
        mock_result_constraint = Mock()
        mock_result_constraint.scalar.return_value = True
        
        # Third call - for counting existing records
        mock_result_count = Mock()
        mock_result_count.scalar.return_value = 0
        
        mock_connection.execute.side_effect = [mock_result_table, mock_result_constraint, mock_result_count]
        
        # Load the migration module
        migration_path = os.path.join(os.path.dirname(__file__), 
                                    "../../alembic/versions/008_update_model_definitions_schema.py")
        spec = importlib.util.spec_from_file_location("migration_008", migration_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Mock op.get_bind() to return our mock connection
        with patch('alembic.op.get_bind', return_value=mock_connection):
            with patch('alembic.op.drop_constraint') as mock_drop_constraint:
                with patch('alembic.op.create_table') as mock_create_table:
                    with patch('alembic.op.execute') as mock_execute:
                        with patch('alembic.op.drop_index') as mock_drop_index:
                            with patch('alembic.op.drop_table') as mock_drop_table:
                                with patch('alembic.op.rename_table') as mock_rename_table:
                                    with patch('alembic.op.create_index') as mock_create_index:
                                        # This should not raise an exception
                                        migration_module.upgrade()
                                        
                                        # Verify that drop_constraint WAS called since constraint exists
                                        mock_drop_constraint.assert_called_once_with(
                                            "model_variants_model_definition_id_fkey", 
                                            "model_variants", 
                                            type_="foreignkey"
                                        )