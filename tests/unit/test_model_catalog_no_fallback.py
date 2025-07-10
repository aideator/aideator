"""
Test model catalog with no fallback functionality.
This tests the changes that removed hardcoded model fallbacks.
"""

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.model_definition import ModelDefinitionDB
from app.models.provider import ModelCapability, ProviderType
from app.services.model_catalog import ModelCatalogService


class TestModelCatalogNoFallback:
    """Test cases for database-only model catalog with no fallback."""

    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        try:
            SQLModel.metadata.create_all(engine)
        except Exception:
            # If tables already exist, that's fine
            pass
        return engine

    @pytest.fixture
    def test_models(self):
        """Create test model data."""
        return [
            ModelDefinitionDB(
                model_name="gpt-4o",
                litellm_provider="openai",
                display_name="GPT-4o",
                description="OpenAI's latest model",
                max_tokens=128000,
                max_output_tokens=4096,
                input_cost_per_token=0.000005,
                output_cost_per_token=0.000015,
                supports_function_calling=True,
                supports_vision=True,
                supports_streaming=True,
                category="advanced",
                requires_api_key=True,
                api_key_env_var="OPENAI_API_KEY",
                is_active=True
            ),
            ModelDefinitionDB(
                model_name="claude-3-5-sonnet-20241022",
                litellm_provider="anthropic",
                display_name="Claude 3.5 Sonnet",
                description="Anthropic's latest model",
                max_tokens=200000,
                max_output_tokens=4096,
                input_cost_per_token=0.000003,
                output_cost_per_token=0.000015,
                supports_function_calling=True,
                supports_vision=True,
                supports_streaming=True,
                category="advanced",
                requires_api_key=True,
                api_key_env_var="ANTHROPIC_API_KEY",
                is_active=True
            )
        ]

    def test_database_only_loading(self, test_db, test_models):
        """Test that models are loaded only from database."""
        with Session(test_db) as session:
            for model in test_models:
                session.add(model)
            session.commit()

        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])

            mock_exec_result = Mock()
            mock_exec_result.all.return_value = test_models
            mock_session.exec.return_value = mock_exec_result

            catalog = ModelCatalogService()

            # Should load exactly 2 models from database
            assert len(catalog._models) == 2
            assert "gpt-4o" in catalog._models
            assert "claude-3-5-sonnet-20241022" in catalog._models

            # Should not have any hardcoded models
            hardcoded_models = [
                "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini",
                "claude-3-opus-20240229", "claude-3-sonnet-20240229",
                "gemini-pro", "gemini-1.5-pro", "gemini-2.0-flash"
            ]
            for model in hardcoded_models:
                assert model not in catalog._models, f"Found hardcoded model: {model}"

    def test_no_fallback_on_database_error(self):
        """Test that NO fallback occurs when database fails."""
        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            # Make database access fail
            mock_get_session.side_effect = Exception("Database connection failed")

            # This should fail completely, no fallback
            with pytest.raises(Exception) as exc_info:
                ModelCatalogService()

            assert "Database connection failed" in str(exc_info.value)

    def test_empty_database_returns_empty_catalog(self):
        """Test that empty database returns empty model catalog."""
        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])

            # Return empty result
            mock_exec_result = Mock()
            mock_exec_result.all.return_value = []
            mock_session.exec.return_value = mock_exec_result

            catalog = ModelCatalogService()

            # Should have no models
            assert len(catalog._models) == 0
            assert catalog.get_all_models() == []

    def test_inactive_models_excluded(self, test_db):
        """Test that inactive models are not loaded."""
        inactive_model = ModelDefinitionDB(
            model_name="deprecated-model",
            litellm_provider="openai",
            display_name="Deprecated Model",
            description="Old model",
            is_active=False  # Inactive
        )

        active_model = ModelDefinitionDB(
            model_name="current-model",
            litellm_provider="openai",
            display_name="Current Model",
            description="Active model",
            is_active=True  # Active
        )

        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])

            # Database query should only return active models
            mock_exec_result = Mock()
            mock_exec_result.all.return_value = [active_model]  # Only active
            mock_session.exec.return_value = mock_exec_result

            catalog = ModelCatalogService()

            # Should only have active model
            assert len(catalog._models) == 1
            assert "current-model" in catalog._models
            assert "deprecated-model" not in catalog._models

    def test_provider_mapping_comprehensive(self):
        """Test comprehensive provider mapping without fallback."""
        test_providers = [
            ("openai", ProviderType.OPENAI),
            ("anthropic", ProviderType.ANTHROPIC),
            ("gemini", ProviderType.GEMINI),
            ("google", ProviderType.GEMINI),
            ("vertex_ai", ProviderType.VERTEX_AI),
            ("bedrock", ProviderType.BEDROCK),
            ("azure", ProviderType.AZURE),
            ("mistral", ProviderType.MISTRAL),
            ("cohere", ProviderType.COHERE),
            ("groq", ProviderType.GROQ),
            ("deepseek", ProviderType.DEEPSEEK),
            ("perplexity", ProviderType.PERPLEXITY),
            ("ollama", ProviderType.OLLAMA),
            ("unknown_provider", ProviderType.OPENAI),  # Default fallback
        ]

        for provider_str, expected_enum in test_providers:
            model = ModelDefinitionDB(
                model_name=f"test-{provider_str}",
                litellm_provider=provider_str,
                display_name=f"Test {provider_str}",
                is_active=True
            )

            with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
                mock_session = Mock(spec=Session)
                mock_get_session.return_value = iter([mock_session])

                mock_exec_result = Mock()
                mock_exec_result.all.return_value = [model]
                mock_session.exec.return_value = mock_exec_result

                catalog = ModelCatalogService()
                model_info = catalog._models.get(f"test-{provider_str}")

                assert model_info is not None
                assert model_info.provider == expected_enum

    def test_capability_mapping(self):
        """Test capability mapping from database fields."""
        # Model with all capabilities
        full_model = ModelDefinitionDB(
            model_name="full-model",
            litellm_provider="openai",
            display_name="Full Model",
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=True,
            category="general",  # Not embedding
            is_active=True
        )

        # Embedding model
        embedding_model = ModelDefinitionDB(
            model_name="embedding-model",
            litellm_provider="openai",
            display_name="Embedding Model",
            supports_streaming=False,
            supports_function_calling=False,
            supports_vision=False,
            category="embedding",
            is_active=True
        )

        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])

            mock_exec_result = Mock()
            mock_exec_result.all.return_value = [full_model, embedding_model]
            mock_session.exec.return_value = mock_exec_result

            catalog = ModelCatalogService()

            # Check full model capabilities
            full_info = catalog._models.get("full-model")
            assert ModelCapability.STREAMING in full_info.capabilities
            assert ModelCapability.FUNCTION_CALLING in full_info.capabilities
            assert ModelCapability.VISION in full_info.capabilities
            assert ModelCapability.TEXT_COMPLETION in full_info.capabilities
            assert ModelCapability.CHAT_COMPLETION in full_info.capabilities
            assert ModelCapability.EMBEDDINGS not in full_info.capabilities

            # Check embedding model capabilities
            embedding_info = catalog._models.get("embedding-model")
            assert ModelCapability.EMBEDDINGS in embedding_info.capabilities
            assert ModelCapability.STREAMING not in embedding_info.capabilities
            assert ModelCapability.FUNCTION_CALLING not in embedding_info.capabilities
            assert ModelCapability.VISION not in embedding_info.capabilities

    def test_get_all_models_database_only(self, test_models):
        """Test get_all_models returns only database models."""
        with patch("app.services.model_catalog.get_sync_session") as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])

            mock_exec_result = Mock()
            mock_exec_result.all.return_value = test_models
            mock_session.exec.return_value = mock_exec_result

            catalog = ModelCatalogService()
            all_models = catalog.get_all_models()

            # Should only return database models
            assert len(all_models) == 2
            model_names = [m.model_name for m in all_models]
            assert "gpt-4o" in model_names
            assert "claude-3-5-sonnet-20241022" in model_names

            # Should not contain any hardcoded models
            assert all(m.model_name in ["gpt-4o", "claude-3-5-sonnet-20241022"] for m in all_models)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
