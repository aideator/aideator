"""
Test for the NoneType handling fix in model catalog.
"""

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from app.models.model_definition import ModelDefinitionDB
from app.models.provider import ModelCapability, ProviderType
from app.services.model_catalog import ModelCatalogService


class TestModelCatalogNoneTypeFix:
    """Test cases for NoneType handling fixes in model catalog."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def catalog_service(self, mock_session):
        """Create ModelCatalogService with mocked session."""
        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            service = ModelCatalogService()
            service._models_loaded = False
            return service

    def test_load_models_handles_none_category(self, catalog_service, mock_session):
        """Test that _load_models_from_db handles None category gracefully."""
        # Create a mock model with None category
        mock_model = Mock(spec=ModelDefinitionDB)
        mock_model.model_name = "test-model"
        mock_model.provider = "openai"
        mock_model.litellm_model_name = "test-model"
        mock_model.litellm_provider = "openai"
        mock_model.display_name = "Test Model"
        mock_model.description = "Test description"
        mock_model.max_tokens = 4096
        mock_model.max_output_tokens = 2048
        mock_model.input_cost_per_token = 0.000001
        mock_model.output_cost_per_token = 0.000002
        mock_model.supports_streaming = True
        mock_model.supports_function_calling = False
        mock_model.supports_vision = False
        mock_model.category = None  # This is the fix we're testing
        mock_model.requires_api_key = True

        # Mock the database query
        mock_result = Mock()
        mock_result.all.return_value = [mock_model]
        mock_session.exec.return_value = mock_result

        # This should not raise an exception
        catalog_service._load_models_from_db()

        # Verify that the model was processed without error
        assert len(catalog_service._models) == 1
        assert "test-model" in catalog_service._models

        # Verify the model has the expected capabilities (should NOT include embeddings)
        model_info = catalog_service._models["test-model"]
        assert ModelCapability.STREAMING in model_info.capabilities
        assert ModelCapability.TEXT_COMPLETION in model_info.capabilities
        assert ModelCapability.CHAT_COMPLETION in model_info.capabilities
        assert ModelCapability.EMBEDDINGS not in model_info.capabilities

    def test_load_models_handles_none_litellm_provider(self, catalog_service, mock_session):
        """Test that _load_models_from_db handles None litellm_provider gracefully."""
        # Create a mock model with None litellm_provider
        mock_model = Mock(spec=ModelDefinitionDB)
        mock_model.model_name = "test-model"
        mock_model.provider = "openai"
        mock_model.litellm_model_name = "test-model"
        mock_model.litellm_provider = None  # This is the fix we're testing
        mock_model.display_name = "Test Model"
        mock_model.description = "Test description"
        mock_model.max_tokens = 4096
        mock_model.max_output_tokens = 2048
        mock_model.input_cost_per_token = 0.000001
        mock_model.output_cost_per_token = 0.000002
        mock_model.supports_streaming = True
        mock_model.supports_function_calling = False
        mock_model.supports_vision = False
        mock_model.category = "general"
        mock_model.requires_api_key = True

        # Mock the database query
        mock_result = Mock()
        mock_result.all.return_value = [mock_model]
        mock_session.exec.return_value = mock_result

        # This should not raise an exception
        catalog_service._load_models_from_db()

        # Verify that the model was processed without error
        assert len(catalog_service._models) == 1
        assert "test-model" in catalog_service._models

        # Verify the model defaulted to OpenAI provider
        model_info = catalog_service._models["test-model"]
        assert model_info.provider == ProviderType.OPENAI

    def test_load_models_handles_embedding_category(self, catalog_service, mock_session):
        """Test that models with 'embedding' in category get EMBEDDINGS capability."""
        # Create a mock model with embedding category
        mock_model = Mock(spec=ModelDefinitionDB)
        mock_model.model_name = "text-embedding-ada-002"
        mock_model.provider = "openai"
        mock_model.litellm_model_name = "text-embedding-ada-002"
        mock_model.litellm_provider = "openai"
        mock_model.display_name = "Text Embedding Ada 002"
        mock_model.description = "OpenAI embedding model"
        mock_model.max_tokens = 8192
        mock_model.max_output_tokens = None
        mock_model.input_cost_per_token = 0.0000001
        mock_model.output_cost_per_token = None
        mock_model.supports_streaming = False
        mock_model.supports_function_calling = False
        mock_model.supports_vision = False
        mock_model.category = "embedding"  # Should trigger embeddings capability
        mock_model.requires_api_key = True

        # Mock the database query
        mock_result = Mock()
        mock_result.all.return_value = [mock_model]
        mock_session.exec.return_value = mock_result

        # Process the model
        catalog_service._load_models_from_db()

        # Verify that the model has embeddings capability
        model_info = catalog_service._models["text-embedding-ada-002"]
        assert ModelCapability.EMBEDDINGS in model_info.capabilities
        # Should NOT have text completion capabilities for embedding models
        assert ModelCapability.TEXT_COMPLETION not in model_info.capabilities
        assert ModelCapability.CHAT_COMPLETION not in model_info.capabilities

    def test_load_models_handles_database_exception(self, catalog_service, mock_session):
        """Test that database exceptions are handled gracefully."""
        # Mock a database exception
        mock_session.exec.side_effect = Exception("Database connection failed")

        # This should not raise an exception, but should log the error
        with patch("app.services.model_catalog.logger") as mock_logger:
            catalog_service._load_models_from_db()

            # Verify that the error was logged
            mock_logger.warning.assert_called_once()
            assert "Failed to load models from database" in mock_logger.warning.call_args[0][0]

            # Verify that fallback initialization was triggered
            mock_logger.info.assert_called_with("Falling back to static model initialization")

    @patch("app.services.model_catalog.get_sync_session")
    def test_provider_type_mapping(self, mock_get_session):
        """Test that all provider types in the mapping exist in ProviderType enum."""
        mock_session = Mock(spec=Session)
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock empty result to avoid actual model processing
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        # Create service and try to load models
        service = ModelCatalogService()

        # This should not raise an AttributeError for missing provider types
        try:
            service._load_models_from_db()
        except AttributeError as e:
            pytest.fail(f"Provider type missing from enum: {e}")
