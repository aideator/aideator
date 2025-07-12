"""Tests for ModelDiscoveryService."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.model_discovery_service import ModelDiscoveryService


class TestModelDiscoveryService:
    """Test ModelDiscoveryService methods."""

    @pytest.fixture
    def service(self):
        """Create ModelDiscoveryService instance."""
        return ModelDiscoveryService()

    def test_init(self, service):
        """Test service initialization."""
        assert isinstance(service, ModelDiscoveryService)

    @patch("app.services.model_discovery_service.litellm", None)
    @patch("app.services.model_discovery_service.get_valid_models", None)
    def test_get_all_possible_models_no_litellm(self, service):
        """Test when LiteLLM is not available."""
        result = service.get_all_possible_models()
        assert result == []

    def test_get_all_possible_models_catalog_only(self, service):
        """Test model discovery from catalog only."""
        # Mock the private method that gets catalog models directly
        with patch.object(service, "_get_litellm_catalog_models") as mock_catalog:
            mock_catalog.return_value = [
                {
                    "model_name": "gpt-4",
                    "litellm_provider": "openai",
                    "source": "litellm_catalog",
                    "requires_api_key": True,
                    "api_key_env_var": "OPENAI_API_KEY",
                },
                {
                    "model_name": "gpt-3.5-turbo",
                    "litellm_provider": "openai",
                    "source": "litellm_catalog",
                    "requires_api_key": True,
                    "api_key_env_var": "OPENAI_API_KEY",
                },
                {
                    "model_name": "claude-3-opus",
                    "litellm_provider": "anthropic",
                    "source": "litellm_catalog",
                    "requires_api_key": True,
                    "api_key_env_var": "ANTHROPIC_API_KEY",
                },
            ]

            result = service.get_all_possible_models()

            assert len(result) == 3
            model_names = [model["model_name"] for model in result]
            assert "gpt-4" in model_names
            assert "gpt-3.5-turbo" in model_names
            assert "claude-3-opus" in model_names

    @patch("app.services.model_discovery_service.litellm")
    @patch("app.services.model_discovery_service.get_valid_models")
    def test_get_all_possible_models_with_provider_keys(
        self, mock_get_valid_models, mock_litellm, service
    ):
        """Test model discovery with provider API keys."""
        # Mock catalog models
        mock_litellm.open_ai_chat_completion_models = ["gpt-4"]
        mock_litellm.anthropic_models = []

        # Mock provider endpoint discovery
        mock_get_valid_models.return_value = ["gpt-4-turbo", "gpt-4"]

        provider_keys = {"openai": "sk-test123"}
        result = service.get_all_possible_models(provider_keys)

        # Should have models from both catalog and endpoint discovery
        # Note: duplicates should be removed
        model_names = [model["model_name"] for model in result]
        assert "gpt-4" in model_names
        assert "gpt-4-turbo" in model_names

    def test_get_litellm_catalog_models_success(self, service):
        """Test getting models from LiteLLM catalog."""
        with patch("app.services.model_discovery_service.litellm") as mock_litellm:
            mock_litellm.open_ai_chat_completion_models = ["gpt-4"]
            mock_litellm.open_ai_text_completion_models = ["text-davinci-003"]
            mock_litellm.anthropic_models = ["claude-3-opus"]

            result = service._get_litellm_catalog_models()

            assert len(result) == 3

            # Check OpenAI models
            openai_models = [m for m in result if m["litellm_provider"] == "openai"]
            assert len(openai_models) == 2
            assert any(m["model_name"] == "gpt-4" for m in openai_models)
            assert any(m["model_name"] == "text-davinci-003" for m in openai_models)

            # Check Anthropic models
            anthropic_models = [
                m for m in result if m["litellm_provider"] == "anthropic"
            ]
            assert len(anthropic_models) == 1
            assert anthropic_models[0]["model_name"] == "claude-3-opus"

    def test_get_litellm_catalog_models_exception(self, service):
        """Test handling exceptions in catalog model discovery."""
        with patch("app.services.model_discovery_service.litellm") as mock_litellm:
            # Mock an attribute error
            mock_litellm.open_ai_chat_completion_models = None
            del mock_litellm.anthropic_models  # Simulate missing attribute

            result = service._get_litellm_catalog_models()
            # Should handle exceptions gracefully and return what it can
            assert isinstance(result, list)

    @patch("app.services.model_discovery_service.os.environ")
    @patch("app.services.model_discovery_service.get_valid_models")
    def test_discover_models_from_providers_success(
        self, mock_get_valid_models, mock_environ, service
    ):
        """Test discovering models from provider endpoints."""
        mock_get_valid_models.return_value = ["gpt-4-turbo", "gpt-4"]
        mock_environ.copy.return_value = {}
        mock_environ.clear = MagicMock()
        mock_environ.update = MagicMock()

        provider_keys = {"openai": "sk-test123", "anthropic": "sk-ant-test"}
        result = service._discover_models_from_providers(provider_keys)

        # Should call get_valid_models for each provider
        assert mock_get_valid_models.call_count == 2

        # Should return models from both providers
        assert len(result) == 4  # 2 models * 2 providers

        # Check that all models have correct metadata
        for model in result:
            assert "model_name" in model
            assert "litellm_provider" in model
            assert model["source"] == "provider_endpoint"
            assert model["requires_api_key"] is True

    @patch("app.services.model_discovery_service.os.environ")
    @patch("app.services.model_discovery_service.get_valid_models")
    def test_discover_models_from_providers_exception(
        self, mock_get_valid_models, mock_environ, service
    ):
        """Test handling exceptions during provider discovery."""
        mock_get_valid_models.side_effect = Exception("API error")
        mock_environ.copy.return_value = {}
        mock_environ.clear = MagicMock()
        mock_environ.update = MagicMock()

        provider_keys = {"openai": "sk-test123"}
        result = service._discover_models_from_providers(provider_keys)

        # Should handle exceptions gracefully
        assert result == []
        # Should restore environment even after exception
        mock_environ.clear.assert_called()
        mock_environ.update.assert_called()

    def test_deduplicate_and_enrich_models(self, service):
        """Test model deduplication and enrichment."""
        input_models = [
            {
                "model_name": "gpt-4",
                "litellm_provider": "openai",
                "source": "litellm_catalog",
            },
            {
                "model_name": "gpt-4",  # Duplicate
                "litellm_provider": "azure",
                "source": "provider_endpoint",
            },
            {
                "model_name": "claude-3-opus",
                "litellm_provider": "anthropic",
                "source": "litellm_catalog",
            },
        ]

        result = service._deduplicate_and_enrich_models(input_models)

        # Should remove duplicates - only 2 unique models
        assert len(result) == 2

        # Should enrich all models with additional metadata
        for model in result:
            assert "display_name" in model
            assert "description" in model
            assert "category" in model
            assert "tags" in model
            assert "is_recommended" in model
            assert "is_popular" in model
            assert "supports_streaming" in model
            assert "supports_function_calling" in model
            assert "supports_vision" in model

    def test_get_api_key_env_var_known_providers(self, service):
        """Test API key environment variable mapping."""
        assert service._get_api_key_env_var("openai") == "OPENAI_API_KEY"
        assert service._get_api_key_env_var("anthropic") == "ANTHROPIC_API_KEY"
        assert service._get_api_key_env_var("cohere") == "COHERE_API_KEY"
        assert service._get_api_key_env_var("groq") == "GROQ_API_KEY"

    def test_get_api_key_env_var_unknown_provider(self, service):
        """Test API key environment variable for unknown provider."""
        assert service._get_api_key_env_var("unknown_provider") is None

    def test_generate_display_name_gpt_models(self, service):
        """Test display name generation for GPT models."""
        assert service._generate_display_name("gpt-4") == "GPT-4"
        assert service._generate_display_name("gpt-3.5-turbo") == "GPT-3.5 Turbo"

    def test_generate_display_name_special_cases(self, service):
        """Test display name generation for special cases."""
        assert service._generate_display_name("claude-3-opus") == "Claude 3 Opus"
        assert service._generate_display_name("claude-3-sonnet") == "Claude 3 Sonnet"
        assert (
            service._generate_display_name("text-embedding-ada-002")
            == "Text Embedding Ada 002"
        )

    def test_generate_display_name_with_prefixes(self, service):
        """Test display name generation removes prefixes."""
        assert service._generate_display_name("openai/gpt-4") == "GPT-4"
        assert (
            service._generate_display_name("anthropic/claude-3-opus") == "Claude 3 Opus"
        )

    def test_generate_display_name_general_formatting(self, service):
        """Test display name generation for general formatting."""
        assert service._generate_display_name("llama-2-70b-chat") == "Llama 2 70B Chat"
        assert service._generate_display_name("custom-model-v1") == "Custom Model V1"

    def test_generate_description_exact_matches(self, service):
        """Test description generation for exact matches."""
        assert "OpenAI's most advanced" in service._generate_description(
            "gpt-4o", "openai"
        )
        assert "Anthropic's most powerful" in service._generate_description(
            "claude-3-opus", "anthropic"
        )

    def test_generate_description_characteristics(self, service):
        """Test description generation based on characteristics."""
        assert "Embedding model" in service._generate_description(
            "text-embedding-ada", "openai"
        )
        assert "Multimodal model" in service._generate_description(
            "vision-model", "test"
        )
        assert "Code generation" in service._generate_description(
            "code-davinci", "openai"
        )

    def test_generate_description_provider_fallback(self, service):
        """Test description generation with provider fallback."""
        assert "Openai language model" in service._generate_description(
            "unknown-model", "openai"
        )
        assert "General purpose language model" in service._generate_description(
            "unknown-model", None
        )

    def test_determine_category_embedding(self, service):
        """Test category determination for embedding models."""
        assert service._determine_category("text-embed-ada", "openai") == "embedding"

    def test_determine_category_vision(self, service):
        """Test category determination for vision models."""
        assert service._determine_category("vision-model", "test") == "vision"
        assert service._determine_category("multimodal-model", "test") == "vision"

    def test_determine_category_code(self, service):
        """Test category determination for code models."""
        assert service._determine_category("code-davinci", "openai") == "code"
        assert service._determine_category("codex-model", "test") == "code"

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
        tags = service._generate_tags("vision-model", "test")
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

    def test_is_popular_true(self, service):
        """Test popular model detection."""
        assert service._is_popular("gpt-4-turbo") is True
        assert service._is_popular("claude-3-sonnet") is True
        assert service._is_popular("gemini-pro") is True

    def test_is_popular_false(self, service):
        """Test non-popular model detection."""
        assert service._is_popular("obscure-model") is False

    def test_supports_function_calling_true(self, service):
        """Test function calling support detection."""
        assert service._supports_function_calling("gpt-4") is True
        assert service._supports_function_calling("gpt-3.5-turbo") is True
        assert service._supports_function_calling("claude-3-opus") is True

    def test_supports_function_calling_false(self, service):
        """Test models without function calling support."""
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
        assert service._supports_vision("basic-model") is False

    def test_integration_full_discovery_process(self, service):
        """Test full integration of model discovery process."""
        # Mock catalog models
        with (
            patch.object(service, "_get_litellm_catalog_models") as mock_catalog,
            patch.object(service, "_discover_models_from_providers") as mock_providers,
        ):
            mock_catalog.return_value = [
                {
                    "model_name": "gpt-4",
                    "litellm_provider": "openai",
                    "source": "litellm_catalog",
                    "requires_api_key": True,
                    "api_key_env_var": "OPENAI_API_KEY",
                },
                {
                    "model_name": "gpt-3.5-turbo",
                    "litellm_provider": "openai",
                    "source": "litellm_catalog",
                    "requires_api_key": True,
                    "api_key_env_var": "OPENAI_API_KEY",
                },
                {
                    "model_name": "claude-3-opus",
                    "litellm_provider": "anthropic",
                    "source": "litellm_catalog",
                    "requires_api_key": True,
                    "api_key_env_var": "ANTHROPIC_API_KEY",
                },
            ]

            mock_providers.return_value = [
                {
                    "model_name": "gpt-4-turbo",
                    "litellm_provider": "openai",
                    "source": "provider_endpoint",
                    "requires_api_key": True,
                    "api_key_env_var": "OPENAI_API_KEY",
                }
            ]

            provider_keys = {"openai": "sk-test123"}
            result = service.get_all_possible_models(provider_keys)

            # Should have models from both sources, deduplicated (4 total, no duplicates)
            assert len(result) == 4

            # Check that all returned models have complete structure
            for model in result:
                assert "model_name" in model
                assert "litellm_provider" in model
                assert "source" in model
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

    def test_singleton_instance_exists(self):
        """Test that the singleton instance is available."""
        from app.services.model_discovery_service import model_discovery_service

        assert isinstance(model_discovery_service, ModelDiscoveryService)
