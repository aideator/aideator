"""
Integration tests for database initialization.

Tests that the database initialization fix properly handles the model_definitions table
and other database models.
"""

import pytest
from sqlmodel import SQLModel

from app.core.database import create_db_and_tables
from app.models.model_definition import ModelDefinitionDB, ModelSyncLog
from app.models.provider_key import ProviderAPIKeyDB, ProviderAPIKeyAuditLog
from app.services.model_catalog import ModelCatalogService


class TestDatabaseInitialization:
    """Test database initialization functionality."""

    def test_model_tables_registered_with_sqlmodel(self):
        """Test that all model tables are registered with SQLModel metadata."""
        # Check that critical tables are in the metadata
        table_names = [table.name for table in SQLModel.metadata.tables.values()]
        
        # Database tables from model_definition.py
        assert "model_definitions" in table_names
        assert "model_sync_logs" in table_names
        
        # Database tables from provider_key.py
        assert "provider_api_keys" in table_names
        assert "provider_api_key_audit_logs" in table_names
        
        # Core application tables
        assert "users" in table_names
        assert "runs" in table_names
        assert "sessions" in table_names
        assert "api_keys" in table_names

    def test_model_catalog_service_lazy_loading(self):
        """Test that ModelCatalogService handles missing database gracefully."""
        # This should not fail even if the database doesn't exist
        catalog = ModelCatalogService()
        
        # This should trigger lazy loading and handle the missing table gracefully
        models = catalog.get_all_models()
        
        # Should return empty list instead of crashing
        assert isinstance(models, list)
        assert len(models) == 0

    def test_model_catalog_service_error_handling(self):
        """Test that ModelCatalogService handles database errors properly."""
        catalog = ModelCatalogService()
        
        # These should all handle missing database gracefully
        assert catalog.get_providers() == []
        assert catalog.get_capabilities() == []
        assert catalog.get_models_without_api_key() == []
        assert catalog.get_model_by_litellm_name("gpt-4") is None

    @pytest.mark.parametrize("method_name,args", [
        ("get_all_models", []),
        ("get_providers", []),
        ("get_capabilities", []),
        ("get_models_without_api_key", []),
        ("get_available_models_for_keys", [{}]),
        ("to_model_definitions", []),
    ])
    def test_model_catalog_methods_with_missing_db(self, method_name, args):
        """Test all model catalog methods handle missing database gracefully."""
        catalog = ModelCatalogService()
        method = getattr(catalog, method_name)
        
        # Should not raise an exception
        result = method(*args)
        
        # Should return appropriate empty result
        assert result is not None
        if isinstance(result, list):
            assert len(result) == 0

    def test_database_models_have_correct_table_names(self):
        """Test that database models have the expected table names."""
        assert ModelDefinitionDB.__tablename__ == "model_definitions"
        assert ModelSyncLog.__tablename__ == "model_sync_logs"
        assert ProviderAPIKeyDB.__tablename__ == "provider_api_keys"
        assert ProviderAPIKeyAuditLog.__tablename__ == "provider_api_key_audit_logs"

    def test_model_definition_db_fields(self):
        """Test that ModelDefinitionDB has required fields."""
        # Test that we can create an instance with minimal required fields
        model = ModelDefinitionDB(
            model_name="test-model",
            provider="openai",
            litellm_model_name="openai/test-model",
            litellm_provider="openai",
            display_name="Test Model"
        )
        
        assert model.model_name == "test-model"
        assert model.provider == "openai"
        assert model.display_name == "Test Model"
        assert model.is_active is True  # Default value
        assert model.requires_api_key is True  # Default value