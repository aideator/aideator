"""Tests for the model catalog service."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlmodel import select

from app.models.model_definition import ModelDefinitionDB
from app.models.provider import ModelCapability, ModelDefinition, ProviderType
from app.services.model_catalog import ModelCatalogService, ModelInfo


class TestModelInfo:
    """Test the ModelInfo dataclass."""

    def test_model_info_init_with_capabilities(self):
        """Test ModelInfo initialization with capabilities."""
        capabilities = [ModelCapability.CHAT_COMPLETION, ModelCapability.STREAMING]
        model = ModelInfo(
            provider=ProviderType.OPENAI,
            model_name="gpt-4",
            litellm_model_name="gpt-4",
            display_name="GPT-4",
            capabilities=capabilities,
        )
        assert model.capabilities == capabilities

    def test_model_info_init_without_capabilities(self):
        """Test ModelInfo initialization without capabilities."""
        model = ModelInfo(
            provider=ProviderType.OPENAI,
            model_name="gpt-4",
            litellm_model_name="gpt-4",
            display_name="GPT-4",
        )
        assert model.capabilities == []


class TestModelCatalogService:
    """Test the model catalog service."""

    @pytest.fixture
    def service(self):
        """Create a model catalog service instance."""
        return ModelCatalogService()

    @pytest.fixture
    def mock_db_models(self):
        """Create mock database models."""
        models = []

        # OpenAI model
        model1 = Mock(spec=ModelDefinitionDB)
        model1.model_name = "gpt-4"
        model1.display_name = "GPT-4"
        model1.description = "Advanced language model"
        model1.litellm_provider = "openai"
        model1.max_tokens = 8192
        model1.max_output_tokens = 4096
        model1.input_cost_per_token = 0.00003
        model1.output_cost_per_token = 0.00006
        model1.supports_streaming = True
        model1.supports_function_calling = True
        model1.supports_vision = False
        model1.category = "chat"
        model1.requires_api_key = True
        model1.is_active = True
        models.append(model1)

        # Anthropic model
        model2 = Mock(spec=ModelDefinitionDB)
        model2.model_name = "claude-3-opus"
        model2.display_name = "Claude 3 Opus"
        model2.description = "Most capable Claude model"
        model2.litellm_provider = "anthropic"
        model2.max_tokens = 200000
        model2.max_output_tokens = 4096
        model2.input_cost_per_token = 0.000015
        model2.output_cost_per_token = 0.000075
        model2.supports_streaming = True
        model2.supports_function_calling = True
        model2.supports_vision = True
        model2.category = "chat"
        model2.requires_api_key = True
        model2.is_active = True
        models.append(model2)

        # Embedding model
        model3 = Mock(spec=ModelDefinitionDB)
        model3.model_name = "text-embedding-ada-002"
        model3.display_name = "Ada Embeddings v2"
        model3.description = "Text embedding model"
        model3.litellm_provider = "openai"
        model3.max_tokens = 8191
        model3.max_output_tokens = None
        model3.input_cost_per_token = 0.0000001
        model3.output_cost_per_token = None
        model3.supports_streaming = False
        model3.supports_function_calling = False
        model3.supports_vision = False
        model3.category = "embedding"
        model3.requires_api_key = True
        model3.is_active = True
        models.append(model3)

        # Free model
        model4 = Mock(spec=ModelDefinitionDB)
        model4.model_name = "llama-2-7b"
        model4.display_name = "Llama 2 7B"
        model4.description = "Open source model"
        model4.litellm_provider = "ollama"
        model4.max_tokens = 4096
        model4.max_output_tokens = 2048
        model4.input_cost_per_token = None
        model4.output_cost_per_token = None
        model4.supports_streaming = True
        model4.supports_function_calling = False
        model4.supports_vision = False
        model4.category = "chat"
        model4.requires_api_key = False
        model4.is_active = True
        models.append(model4)

        return models

    def test_init(self, service):
        """Test service initialization."""
        assert service._models == {}
        assert service._models_loaded is False

    @patch("app.services.model_catalog.get_sync_session")
    def test_load_models_from_db_success(
        self, mock_get_session, service, mock_db_models
    ):
        """Test loading models from database successfully."""
        # Mock session
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Trigger loading
        service._ensure_models_loaded()

        # Verify models were loaded
        assert len(service._models) == 4
        assert service._models_loaded is True

        # Check GPT-4
        gpt4 = service._models.get("gpt-4")
        assert gpt4 is not None
        assert gpt4.provider == ProviderType.OPENAI
        assert gpt4.display_name == "GPT-4"
        assert gpt4.context_window == 8192
        assert gpt4.input_price_per_1m_tokens == 30.0
        assert ModelCapability.STREAMING in gpt4.capabilities
        assert ModelCapability.FUNCTION_CALLING in gpt4.capabilities
        assert ModelCapability.VISION not in gpt4.capabilities

        # Check Claude
        claude = service._models.get("claude-3-opus")
        assert claude is not None
        assert claude.provider == ProviderType.ANTHROPIC
        assert ModelCapability.VISION in claude.capabilities

        # Check embedding model
        embedding = service._models.get("text-embedding-ada-002")
        assert embedding is not None
        assert ModelCapability.EMBEDDINGS in embedding.capabilities
        assert ModelCapability.CHAT_COMPLETION not in embedding.capabilities

        # Check free model
        llama = service._models.get("llama-2-7b")
        assert llama is not None
        assert llama.provider == ProviderType.OLLAMA
        assert llama.requires_api_key is False

    @patch("app.services.model_catalog.get_sync_session")
    def test_load_models_from_db_error(self, mock_get_session, service):
        """Test handling database error when loading models."""
        # Mock session to raise exception
        mock_get_session.side_effect = Exception("Database connection failed")

        # Trigger loading - should not raise
        service._ensure_models_loaded()

        # Verify empty models and marked as loaded
        assert service._models == {}
        assert service._models_loaded is True

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_all_models(self, mock_get_session, service, mock_db_models):
        """Test getting all models."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get models
        models = service.get_all_models()

        assert len(models) == 4
        assert all(isinstance(m, ModelInfo) for m in models)

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_models_by_provider(self, mock_get_session, service, mock_db_models):
        """Test getting models by provider."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get OpenAI models
        openai_models = service.get_models_by_provider(ProviderType.OPENAI)
        assert len(openai_models) == 2
        assert all(m.provider == ProviderType.OPENAI for m in openai_models)

        # Get Anthropic models
        anthropic_models = service.get_models_by_provider(ProviderType.ANTHROPIC)
        assert len(anthropic_models) == 1
        assert anthropic_models[0].model_name == "claude-3-opus"

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_models_by_capability(self, mock_get_session, service, mock_db_models):
        """Test getting models by capability."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get vision models
        vision_models = service.get_models_by_capability(ModelCapability.VISION)
        assert len(vision_models) == 1
        assert vision_models[0].model_name == "claude-3-opus"

        # Get embedding models
        embedding_models = service.get_models_by_capability(ModelCapability.EMBEDDINGS)
        assert len(embedding_models) == 1
        assert embedding_models[0].model_name == "text-embedding-ada-002"

        # Get streaming models
        streaming_models = service.get_models_by_capability(ModelCapability.STREAMING)
        assert len(streaming_models) == 3  # GPT-4, Claude, Llama

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_models_without_api_key(
        self, mock_get_session, service, mock_db_models
    ):
        """Test getting models that don't require API keys."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get free models
        free_models = service.get_models_without_api_key()
        assert len(free_models) == 1
        assert free_models[0].model_name == "llama-2-7b"
        assert free_models[0].requires_api_key is False

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_model_by_litellm_name(self, mock_get_session, service, mock_db_models):
        """Test getting model by LiteLLM name."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get existing model
        model = service.get_model_by_litellm_name("gpt-4")
        assert model is not None
        assert model.model_name == "gpt-4"

        # Get non-existent model
        model = service.get_model_by_litellm_name("non-existent")
        assert model is None

    @patch("app.services.model_catalog.get_sync_session")
    def test_validate_model_access_success(
        self, mock_get_session, service, mock_db_models
    ):
        """Test validating model access with required keys."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Validate with required key
        available_keys = {"openai": True}
        is_valid, error = service.validate_model_access("gpt-4", available_keys)
        assert is_valid is True
        assert error == ""

    @patch("app.services.model_catalog.get_sync_session")
    def test_validate_model_access_missing_key(
        self, mock_get_session, service, mock_db_models
    ):
        """Test validating model access without required key."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Validate without required key
        available_keys = {"anthropic": True}  # Has Anthropic but not OpenAI
        is_valid, error = service.validate_model_access("gpt-4", available_keys)
        assert is_valid is False
        assert "requires Openai API key" in error

    @patch("app.services.model_catalog.get_sync_session")
    def test_validate_model_access_free_model(
        self, mock_get_session, service, mock_db_models
    ):
        """Test validating access to free model."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Validate free model (no key required)
        available_keys = {}
        is_valid, error = service.validate_model_access("llama-2-7b", available_keys)
        assert is_valid is True
        assert error == ""

    @patch("app.services.model_catalog.get_sync_session")
    def test_validate_model_access_by_display_name(
        self, mock_get_session, service, mock_db_models
    ):
        """Test validating model access by display name."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Validate by display name
        available_keys = {"openai": True}
        is_valid, error = service.validate_model_access("GPT-4", available_keys)
        assert is_valid is True

    @patch("app.services.model_catalog.get_sync_session")
    def test_validate_model_access_by_definition_id(
        self, mock_get_session, service, mock_db_models
    ):
        """Test validating model access by model definition ID."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Validate by definition ID
        available_keys = {"openai": True}
        is_valid, error = service.validate_model_access(
            "model_gpt_4_openai", available_keys
        )
        assert is_valid is True

    @patch("app.services.model_catalog.get_sync_session")
    def test_validate_model_access_unknown_model(
        self, mock_get_session, service, mock_db_models
    ):
        """Test validating access to unknown model."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Validate unknown model
        available_keys = {"openai": True}
        is_valid, error = service.validate_model_access("unknown-model", available_keys)
        assert is_valid is False
        assert "not found" in error
        assert "Available models:" in error

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_available_models_for_keys(
        self, mock_get_session, service, mock_db_models
    ):
        """Test getting models available for given API keys."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get models for OpenAI key
        available_keys = {"openai": True}
        models = service.get_available_models_for_keys(available_keys)
        assert len(models) == 3  # 2 OpenAI + 1 free model

        # Get models with no keys
        available_keys = {}
        models = service.get_available_models_for_keys(available_keys)
        assert len(models) == 1  # Only free model

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_providers(self, mock_get_session, service, mock_db_models):
        """Test getting all providers."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get providers
        providers = service.get_providers()
        assert len(providers) == 3
        assert ProviderType.OPENAI in providers
        assert ProviderType.ANTHROPIC in providers
        assert ProviderType.OLLAMA in providers

    @patch("app.services.model_catalog.get_sync_session")
    def test_get_capabilities(self, mock_get_session, service, mock_db_models):
        """Test getting all capabilities."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Get capabilities
        capabilities = service.get_capabilities()
        assert ModelCapability.STREAMING in capabilities
        assert ModelCapability.FUNCTION_CALLING in capabilities
        assert ModelCapability.VISION in capabilities
        assert ModelCapability.EMBEDDINGS in capabilities
        assert ModelCapability.CHAT_COMPLETION in capabilities

    @patch("app.services.model_catalog.get_sync_session")
    def test_to_model_definitions(self, mock_get_session, service, mock_db_models):
        """Test converting to model definitions."""
        # Setup
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = mock_db_models
        mock_get_session.return_value = [mock_session]

        # Convert to definitions
        definitions = service.to_model_definitions()
        assert len(definitions) == 4
        assert all(isinstance(d, ModelDefinition) for d in definitions)

        # Check a specific definition
        gpt4_def = next(d for d in definitions if d.model_name == "gpt-4")
        assert gpt4_def.id == "model_gpt_4_openai"
        assert gpt4_def.provider == ProviderType.OPENAI
        assert gpt4_def.display_name == "GPT-4"

    @patch("app.services.model_catalog.get_sync_session")
    def test_provider_mapping(self, mock_get_session, service):
        """Test provider string to enum mapping."""
        # Create models with various provider strings
        models = []

        provider_tests = [
            ("gemini", ProviderType.GEMINI),
            ("google", ProviderType.GEMINI),
            ("vertex_ai", ProviderType.VERTEX_AI),
            ("bedrock", ProviderType.BEDROCK),
            ("azure", ProviderType.AZURE),
            ("mistral", ProviderType.MISTRAL),
            ("cohere", ProviderType.COHERE),
            ("huggingface", ProviderType.HUGGINGFACE),
            ("together", ProviderType.TOGETHER),
            ("groq", ProviderType.GROQ),
            ("deepseek", ProviderType.DEEPSEEK),
            ("perplexity", ProviderType.PERPLEXITY),
            ("unknown", ProviderType.OPENAI),  # Default
            (None, ProviderType.OPENAI),  # Default when None
        ]

        for provider_str, expected_enum in provider_tests:
            model = Mock(spec=ModelDefinitionDB)
            model.model_name = f"test-{provider_str}"
            model.display_name = f"Test {provider_str}"
            model.litellm_provider = provider_str
            model.max_tokens = 1000
            model.max_output_tokens = None
            model.input_cost_per_token = None
            model.output_cost_per_token = None
            model.supports_streaming = False
            model.supports_function_calling = False
            model.supports_vision = False
            model.category = "chat"
            model.requires_api_key = True
            model.is_active = True
            model.description = None
            models.append(model)

        # Mock session
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = models
        mock_get_session.return_value = [mock_session]

        # Trigger loading
        service._ensure_models_loaded()

        # Verify provider mapping
        for provider_str, expected_enum in provider_tests:
            model_name = f"test-{provider_str}"
            model = service.get_model_by_litellm_name(model_name)
            assert model is not None
            assert model.provider == expected_enum

    def test_lazy_loading(self, service):
        """Test that models are loaded lazily."""
        # Initially not loaded
        assert service._models_loaded is False

        # Mock the loading method
        with patch.object(service, "_load_models_from_db") as mock_load:
            # First access triggers loading
            service._ensure_models_loaded()
            mock_load.assert_called_once()

            # Mark as loaded
            service._models_loaded = True

            # Second access doesn't trigger loading
            service._ensure_models_loaded()
            mock_load.assert_called_once()  # Still only called once

    @patch("app.services.model_catalog.get_sync_session")
    def test_empty_database(self, mock_get_session, service):
        """Test handling empty database."""
        # Mock session with no models
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []
        mock_get_session.return_value = [mock_session]

        # Get models
        models = service.get_all_models()
        assert len(models) == 0

        # Other methods should return empty results
        assert service.get_models_by_provider(ProviderType.OPENAI) == []
        assert service.get_models_by_capability(ModelCapability.VISION) == []
        assert service.get_models_without_api_key() == []
        assert service.get_providers() == []
        assert service.get_capabilities() == []
