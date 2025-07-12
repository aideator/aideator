"""Tests for LiteLLMModelDiscovery service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.litellm_model_discovery import LiteLLMModelDiscovery


class TestLiteLLMModelDiscovery:
    """Test LiteLLMModelDiscovery methods."""

    @pytest.fixture
    def service(self):
        """Create LiteLLMModelDiscovery instance."""
        return LiteLLMModelDiscovery()

    def test_init(self, service):
        """Test service initialization."""
        assert isinstance(service, LiteLLMModelDiscovery)

    @patch("app.services.litellm_model_discovery.LITELLM_AVAILABLE", False)
    def test_get_all_supported_models_no_litellm(self, service):
        """Test model discovery when LiteLLM is not available."""
        result = service.get_all_supported_models()
        assert result == []

    @patch("app.services.litellm_model_discovery.LITELLM_AVAILABLE", True)
    @patch("app.services.litellm_model_discovery.litellm")
    def test_get_all_supported_models_success(self, mock_litellm, service):
        """Test successful model discovery."""
        # Mock the models_by_provider data
        mock_litellm.models_by_provider = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet"],
        }

        result = service.get_all_supported_models()

        assert len(result) == 4
        model_names = [model["model_name"] for model in result]
        assert "gpt-4" in model_names
        assert "gpt-3.5-turbo" in model_names
        assert "claude-3-opus" in model_names
        assert "claude-3-sonnet" in model_names

    @patch("app.services.litellm_model_discovery.LITELLM_AVAILABLE", True)
    @patch("app.services.litellm_model_discovery.litellm")
    def test_get_all_supported_models_no_models_attr(self, mock_litellm, service):
        """Test when litellm doesn't have models_by_provider attribute."""
        # Remove the models_by_provider attribute
        if hasattr(mock_litellm, "models_by_provider"):
            delattr(mock_litellm, "models_by_provider")

        result = service.get_all_supported_models()
        assert result == []

    def test_create_model_info(self, service):
        """Test creating model info dictionary."""
        result = service._create_model_info("gpt-4", "openai")

        assert result["model_name"] == "gpt-4"
        assert result["litellm_provider"] == "openai"
        assert "display_name" in result
        assert "description" in result
        assert "category" in result
        assert "tags" in result
        assert "source" in result
        assert result["source"] == "litellm_catalog"

    def test_deduplicate_models(self, service):
        """Test model deduplication with provider priority."""
        models = [
            {"model_name": "gpt-4", "litellm_provider": "azure"},
            {"model_name": "gpt-4", "litellm_provider": "openai"},
            {"model_name": "claude-3-opus", "litellm_provider": "anthropic"},
        ]

        result = service._deduplicate_models(models)

        assert len(result) == 2
        # Should prefer openai over azure for gpt-4
        gpt4_model = next(m for m in result if m["model_name"] == "gpt-4")
        assert gpt4_model["litellm_provider"] == "openai"

    def test_generate_display_name_basic(self, service):
        """Test display name generation for basic model names."""
        assert service._generate_display_name("gpt-4") == "GPT 4"
        assert service._generate_display_name("claude-3-opus") == "Claude 3 Opus"

    def test_generate_display_name_with_prefixes(self, service):
        """Test display name generation with provider prefixes."""
        assert service._generate_display_name("openai/gpt-4") == "GPT 4"
        assert (
            service._generate_display_name("anthropic/claude-3-opus") == "Claude 3 Opus"
        )

    def test_generate_display_name_with_special_terms(self, service):
        """Test display name generation with special terms."""
        assert service._generate_display_name("gpt-4-api") == "GPT 4 API"
        assert service._generate_display_name("claude-ai-v1") == "Claude AI V1"

    def test_generate_description_exact_matches(self, service):
        """Test description generation for exact model matches."""
        assert "OpenAI's most advanced" in service._generate_description(
            "gpt-4o", "openai"
        )
        assert "Anthropic's most powerful" in service._generate_description(
            "claude-3-opus", "anthropic"
        )

    def test_generate_description_characteristics(self, service):
        """Test description generation based on model characteristics."""
        assert "Embedding model" in service._generate_description(
            "text-embedding-ada", "openai"
        )
        assert (
            "Multimodal model with vision capabilities"
            in service._generate_description("vision-model", "test")
        )
        assert "Code generation" in service._generate_description(
            "code-davinci", "openai"
        )
        assert "Speech-to-text" in service._generate_description("whisper-1", "openai")
        assert "Text-to-speech" in service._generate_description("tts-1", "openai")

    def test_generate_description_fallback(self, service):
        """Test description generation fallback."""
        result = service._generate_description("unknown-model", "custom_provider")
        assert "Custom Provider language model" in result

    def test_determine_category_embedding(self, service):
        """Test category determination for embedding models."""
        assert service._determine_category("text-embed-ada", "openai") == "embedding"

    def test_determine_category_vision(self, service):
        """Test category determination for vision models."""
        assert service._determine_category("gpt-4-vision", "openai") == "vision"
        assert service._determine_category("multimodal-model", "test") == "vision"

    def test_determine_category_code(self, service):
        """Test category determination for code models."""
        assert service._determine_category("code-davinci", "openai") == "code"
        assert service._determine_category("coder-model", "test") == "code"

    def test_determine_category_audio(self, service):
        """Test category determination for audio models."""
        assert service._determine_category("whisper-1", "openai") == "speech-to-text"
        assert service._determine_category("tts-1", "openai") == "text-to-speech"

    def test_determine_category_advanced(self, service):
        """Test category determination for advanced models."""
        assert service._determine_category("gpt-4-turbo", "openai") == "advanced"
        assert service._determine_category("claude-3-opus", "anthropic") == "advanced"
        assert service._determine_category("gemini-pro", "google") == "advanced"

    def test_determine_category_general(self, service):
        """Test category determination for general models."""
        assert service._determine_category("basic-model", "test") == "general"

    def test_generate_tags_speed_indicators(self, service):
        """Test tag generation for speed indicators."""
        tags = service._generate_tags("gpt-3.5-turbo", "openai")
        assert "fast" in tags

        tags = service._generate_tags("gemini-flash", "google")
        assert "fast" in tags

    def test_generate_tags_capability_indicators(self, service):
        """Test tag generation for capability indicators."""
        tags = service._generate_tags("gpt-4", "openai")
        assert "powerful" in tags

        tags = service._generate_tags("claude-3-opus", "anthropic")
        assert "powerful" in tags

    def test_generate_tags_features(self, service):
        """Test tag generation for feature indicators."""
        tags = service._generate_tags("gpt-4-vision", "openai")
        assert "vision" in tags

        tags = service._generate_tags("text-embedding-ada", "openai")
        assert "embedding" in tags

        tags = service._generate_tags("code-davinci", "openai")
        assert "code" in tags

    def test_generate_tags_provider(self, service):
        """Test tag generation includes provider."""
        tags = service._generate_tags("gpt-4", "openai")
        assert "openai" in tags

        tags = service._generate_tags("claude-3", "anthropic")
        assert "anthropic" in tags

    def test_is_recommended_true(self, service):
        """Test recommended model detection."""
        assert service._is_recommended("gpt-4o") is True
        assert service._is_recommended("claude-3-opus") is True
        assert service._is_recommended("gemini-1.5-pro") is True

    def test_is_recommended_false(self, service):
        """Test non-recommended model detection."""
        assert service._is_recommended("basic-model") is False
        assert service._is_recommended("old-model") is False

    def test_is_popular_true(self, service):
        """Test popular model detection."""
        assert service._is_popular("gpt-4-turbo") is True
        assert service._is_popular("claude-3-sonnet") is True
        assert service._is_popular("gemini-pro") is True

    def test_is_popular_false(self, service):
        """Test non-popular model detection."""
        assert service._is_popular("obscure-model") is False

    def test_requires_api_key_true(self, service):
        """Test API key requirement for most providers."""
        assert service._requires_api_key("openai") is True
        assert service._requires_api_key("anthropic") is True
        assert service._requires_api_key("cohere") is True

    def test_requires_api_key_false(self, service):
        """Test no API key requirement for local providers."""
        assert service._requires_api_key("ollama") is False
        assert service._requires_api_key("local") is False
        assert service._requires_api_key("huggingface_local") is False

    def test_get_api_key_env_var_known_providers(self, service):
        """Test API key environment variable mapping for known providers."""
        assert service._get_api_key_env_var("openai") == "OPENAI_API_KEY"
        assert service._get_api_key_env_var("anthropic") == "ANTHROPIC_API_KEY"
        assert service._get_api_key_env_var("cohere") == "COHERE_API_KEY"
        assert service._get_api_key_env_var("groq") == "GROQ_API_KEY"

    def test_get_api_key_env_var_unknown_provider(self, service):
        """Test API key environment variable for unknown providers."""
        assert service._get_api_key_env_var("unknown_provider") is None

    def test_supports_function_calling_true(self, service):
        """Test function calling support detection."""
        assert service._supports_function_calling("gpt-4") is True
        assert service._supports_function_calling("gpt-3.5-turbo") is True
        assert service._supports_function_calling("claude-3-opus") is True

    def test_supports_function_calling_false(self, service):
        """Test models without function calling support."""
        assert service._supports_function_calling("whisper-1") is False
        assert service._supports_function_calling("basic-model") is False

    def test_supports_vision_true(self, service):
        """Test vision support detection."""
        assert service._supports_vision("gpt-4o") is True
        assert service._supports_vision("gpt-4-vision") is True
        assert service._supports_vision("claude-3-opus") is True
        assert service._supports_vision("gemini-1.5-pro") is True

    def test_supports_vision_false(self, service):
        """Test models without vision support."""
        assert service._supports_vision("gpt-3.5-turbo") is False
        assert service._supports_vision("text-embedding-ada") is False

    @patch("app.services.litellm_model_discovery.LITELLM_AVAILABLE", True)
    @patch("app.services.litellm_model_discovery.litellm")
    def test_integration_full_model_creation(self, mock_litellm, service):
        """Test full integration of model creation process."""
        mock_litellm.models_by_provider = {
            "openai": ["gpt-4", "gpt-4", "gpt-3.5-turbo"],  # Duplicate gpt-4
            "anthropic": ["claude-3-opus"],
        }

        result = service.get_all_supported_models()

        # Should have deduplicated models
        assert len(result) == 3

        # Check structure of returned models
        for model in result:
            assert "model_name" in model
            assert "litellm_provider" in model
            assert "display_name" in model
            assert "description" in model
            assert "category" in model
            assert "tags" in model
            assert "is_recommended" in model
            assert "is_popular" in model
            assert "requires_api_key" in model
            assert "supports_streaming" in model
            assert "supports_function_calling" in model
            assert "supports_vision" in model
            assert "source" in model
            assert model["source"] == "litellm_catalog"

    def test_singleton_instance_exists(self):
        """Test that the singleton instance is available."""
        from app.services.litellm_model_discovery import litellm_model_discovery

        assert isinstance(litellm_model_discovery, LiteLLMModelDiscovery)
