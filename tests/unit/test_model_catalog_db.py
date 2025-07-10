"""
Test model catalog with database backend.
"""

import pytest
from unittest.mock import Mock, patch
from sqlmodel import create_engine, Session, SQLModel

from app.services.model_catalog import ModelCatalogService
from app.models.model_definition import ModelDefinitionDB
from app.models.provider import ProviderType, ModelCapability


class TestModelCatalogDB:
    """Test cases for database-backed model catalog."""
    
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def test_models(self):
        """Create test model data."""
        return [
            ModelDefinitionDB(
                model_name="gpt-4",
                litellm_provider="openai",
                display_name="GPT-4",
                description="OpenAI's most capable model",
                max_tokens=8192,
                max_output_tokens=4096,
                input_cost_per_token=0.00003,
                output_cost_per_token=0.00006,
                supports_function_calling=True,
                supports_vision=False,
                supports_streaming=True,
                category="advanced",
                tags=["powerful", "functions", "streaming"],
                is_recommended=True,
                is_popular=True,
                requires_api_key=True,
                api_key_env_var="OPENAI_API_KEY",
                is_active=True
            ),
            ModelDefinitionDB(
                model_name="claude-3-opus-20240229",
                litellm_provider="anthropic",
                display_name="Claude 3 Opus",
                description="Anthropic's most powerful model",
                max_tokens=200000,
                max_output_tokens=4096,
                input_cost_per_token=0.000015,
                output_cost_per_token=0.000075,
                supports_function_calling=True,
                supports_vision=True,
                supports_streaming=True,
                category="advanced",
                tags=["powerful", "vision", "large-context"],
                is_recommended=True,
                is_popular=True,
                requires_api_key=True,
                api_key_env_var="ANTHROPIC_API_KEY",
                is_active=True
            ),
            ModelDefinitionDB(
                model_name="llama-2-7b",
                litellm_provider="ollama",
                display_name="Llama 2 7B",
                description="Open source model",
                max_tokens=4096,
                supports_streaming=True,
                category="general",
                tags=["open-source", "local"],
                requires_api_key=False,
                is_active=True
            ),
            ModelDefinitionDB(
                model_name="old-model",
                litellm_provider="openai",
                display_name="Old Model",
                description="Deprecated model",
                is_active=False  # Inactive
            )
        ]
    
    def test_load_models_from_db(self, test_db, test_models):
        """Test loading models from database."""
        # Add test models to database
        with Session(test_db) as session:
            for model in test_models:
                session.add(model)
            session.commit()
        
        # Mock the database session
        with patch('app.services.model_catalog.get_sync_session') as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])
            
            # Mock the query result
            mock_exec_result = Mock()
            mock_exec_result.all.return_value = [m for m in test_models if m.is_active]
            mock_session.exec.return_value = mock_exec_result
            
            # Create catalog
            catalog = ModelCatalogService()
            
            # Verify models were loaded (only active ones)
            assert len(catalog._models) == 3
            assert "gpt-4" in catalog._models
            assert "claude-3-opus-20240229" in catalog._models
            assert "llama-2-7b" in catalog._models
            assert "old-model" not in catalog._models  # Inactive
    
    def test_model_info_conversion(self, test_db, test_models):
        """Test conversion from database model to ModelInfo."""
        with Session(test_db) as session:
            session.add(test_models[0])  # GPT-4
            session.commit()
        
        with patch('app.services.model_catalog.get_sync_session') as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])
            
            mock_exec_result = Mock()
            mock_exec_result.all.return_value = [test_models[0]]
            mock_session.exec.return_value = mock_exec_result
            
            catalog = ModelCatalogService()
            
            # Get the model
            model_info = catalog._models.get("gpt-4")
            assert model_info is not None
            
            # Verify conversion
            assert model_info.provider == ProviderType.OPENAI
            assert model_info.model_name == "gpt-4"
            assert model_info.litellm_model_name == "gpt-4"
            assert model_info.display_name == "GPT-4"
            assert model_info.description == "OpenAI's most capable model"
            assert model_info.context_window == 8192
            assert model_info.max_output_tokens == 4096
            
            # Verify price conversion (per token to per 1M tokens)
            assert model_info.input_price_per_1m_tokens == 30.0
            assert model_info.output_price_per_1m_tokens == 60.0
            
            # Verify capabilities
            assert ModelCapability.STREAMING in model_info.capabilities
            assert ModelCapability.FUNCTION_CALLING in model_info.capabilities
            assert ModelCapability.TEXT_COMPLETION in model_info.capabilities
            assert ModelCapability.CHAT_COMPLETION in model_info.capabilities
            assert ModelCapability.VISION not in model_info.capabilities
    
    def test_provider_mapping(self, test_db):
        """Test provider string to enum mapping."""
        providers_to_test = [
            ("openai", ProviderType.OPENAI),
            ("anthropic", ProviderType.ANTHROPIC),
            ("gemini", ProviderType.GEMINI),
            ("google", ProviderType.GEMINI),
            ("vertex_ai", ProviderType.VERTEX_AI),
            ("mistral", ProviderType.MISTRAL),
            ("ollama", ProviderType.OLLAMA),
            ("unknown", ProviderType.OPENAI),  # Default
        ]
        
        for provider_str, expected_enum in providers_to_test:
            model = ModelDefinitionDB(
                model_name=f"test-{provider_str}",
                litellm_provider=provider_str,
                display_name=f"Test {provider_str}",
                is_active=True
            )
            
            with Session(test_db) as session:
                session.add(model)
                session.commit()
            
            with patch('app.services.model_catalog.get_sync_session') as mock_get_session:
                mock_session = Mock(spec=Session)
                mock_get_session.return_value = iter([mock_session])
                
                mock_exec_result = Mock()
                mock_exec_result.all.return_value = [model]
                mock_session.exec.return_value = mock_exec_result
                
                catalog = ModelCatalogService()
                model_info = catalog._models.get(f"test-{provider_str}")
                
                assert model_info is not None
                assert model_info.provider == expected_enum
    
    def test_fallback_to_static_on_error(self):
        """Test fallback to static initialization on database error."""
        with patch('app.services.model_catalog.get_sync_session') as mock_get_session:
            # Make database access fail
            mock_get_session.side_effect = Exception("Database error")
            
            with patch('app.services.model_catalog.logger') as mock_logger:
                catalog = ModelCatalogService()
                
                # Verify warning was logged
                mock_logger.warning.assert_called()
                assert "Failed to load models from database" in mock_logger.warning.call_args[0][0]
                
                # Verify static models were loaded
                assert len(catalog._models) > 0
                assert "gpt-4" in catalog._models  # Should have static models
    
    def test_get_available_models_for_keys(self, test_db, test_models):
        """Test getting available models based on API keys."""
        with Session(test_db) as session:
            for model in test_models[:3]:  # Active models only
                session.add(model)
            session.commit()
        
        with patch('app.services.model_catalog.get_sync_session') as mock_get_session:
            mock_session = Mock(spec=Session)
            mock_get_session.return_value = iter([mock_session])
            
            mock_exec_result = Mock()
            mock_exec_result.all.return_value = test_models[:3]
            mock_session.exec.return_value = mock_exec_result
            
            catalog = ModelCatalogService()
            
            # Test with OpenAI key only
            available_keys = {"openai": True}
            available_models = catalog.get_available_models_for_keys(available_keys)
            
            # Should get GPT-4 and Llama (no key required)
            model_names = [m.model_name for m in available_models]
            assert "gpt-4" in model_names
            assert "llama-2-7b" in model_names  # No API key required
            assert "claude-3-opus-20240229" not in model_names  # Requires Anthropic key
            
            # Test with all keys
            all_keys = {"openai": True, "anthropic": True}
            all_available = catalog.get_available_models_for_keys(all_keys)
            
            assert len(all_available) == 3  # All active models


if __name__ == "__main__":
    pytest.main([__file__, "-v"])