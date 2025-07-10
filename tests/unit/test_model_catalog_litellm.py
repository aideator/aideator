"""
Test model catalog with LiteLLM canonical names.
"""

import pytest

from app.models.provider import ModelCapability, ProviderType
from app.services.model_catalog import model_catalog


class TestLiteLLMModelCatalog:
    """Test cases for LiteLLM model catalog."""

    def test_openai_models_use_canonical_names(self):
        """Test that OpenAI models use canonical LiteLLM names."""
        # Get OpenAI models
        openai_models = model_catalog.get_models_by_provider(ProviderType.OPENAI)

        # Check canonical names
        model_names = {m.litellm_model_name for m in openai_models}

        # These should be the canonical names (no openai/ prefix)
        assert "gpt-4" in model_names
        assert "gpt-4-turbo" in model_names
        assert "gpt-4o" in model_names
        assert "gpt-3.5-turbo" in model_names
        assert "o1-preview" in model_names

        # Should NOT have prefixes
        assert not any(name.startswith("openai/") for name in model_names)

    def test_anthropic_models_use_canonical_names(self):
        """Test that Anthropic models use canonical LiteLLM names."""
        anthropic_models = model_catalog.get_models_by_provider(ProviderType.ANTHROPIC)

        model_names = {m.litellm_model_name for m in anthropic_models}

        # Check for version-specific names
        assert "claude-3-opus-20240229" in model_names
        assert "claude-3-sonnet-20240229" in model_names
        assert "claude-3-haiku-20240307" in model_names
        assert "claude-3-5-sonnet-20241022" in model_names

        # Should NOT have anthropic/ prefix
        assert not any(name.startswith("anthropic/") for name in model_names)

    def test_google_models_use_canonical_names(self):
        """Test that Google/Gemini models use canonical LiteLLM names."""
        gemini_models = model_catalog.get_models_by_provider(ProviderType.GEMINI)

        model_names = {m.litellm_model_name for m in gemini_models}

        # These should be without gemini/ prefix
        assert "gemini-pro" in model_names
        assert "gemini-1.5-pro" in model_names
        assert "gemini-1.5-flash" in model_names

        # Should NOT have gemini/ prefix
        assert not any(name.startswith("gemini/") for name in model_names)

    def test_prefixed_models_keep_prefix(self):
        """Test that models requiring prefixes keep them."""
        # Vertex AI models should keep their prefix
        vertex_models = model_catalog.get_models_by_provider(ProviderType.VERTEX_AI)
        for model in vertex_models:
            assert model.litellm_model_name.startswith("vertex_ai/")

        # Bedrock models should keep their prefix
        bedrock_models = model_catalog.get_models_by_provider(ProviderType.BEDROCK)
        for model in bedrock_models:
            assert model.litellm_model_name.startswith("bedrock/")

        # Together AI models should keep their prefix
        together_models = model_catalog.get_models_by_provider(ProviderType.TOGETHER)
        for model in together_models:
            assert model.litellm_model_name.startswith("together_ai/")

    def test_model_validation_with_canonical_names(self):
        """Test model validation works with canonical names."""
        available_keys = {
            "openai": True,
            "anthropic": True,
            "gemini": True,
        }

        # Test validation with canonical names
        is_valid, error = model_catalog.validate_model_access("gpt-4", available_keys)
        assert is_valid
        assert error == ""

        is_valid, error = model_catalog.validate_model_access("claude-3-opus-20240229", available_keys)
        assert is_valid
        assert error == ""

        is_valid, error = model_catalog.validate_model_access("gemini-pro", available_keys)
        assert is_valid
        assert error == ""

    def test_model_validation_with_definition_ids(self):
        """Test model validation still works with old definition IDs for backward compatibility."""
        available_keys = {
            "openai": True,
        }

        # Test with old format model definition ID
        is_valid, error = model_catalog.validate_model_access("model_gpt_4_openai", available_keys)
        assert is_valid
        assert error == ""

    def test_model_validation_without_api_key(self):
        """Test model validation fails when API key is missing."""
        available_keys = {}  # No API keys

        is_valid, error = model_catalog.validate_model_access("gpt-4", available_keys)
        assert not is_valid
        assert "API key" in error
        assert "Openai" in error  # Should show proper provider name

    def test_models_without_api_key(self):
        """Test that some models don't require API keys."""
        no_key_models = model_catalog.get_models_without_api_key()

        # Ollama models should not require API key
        ollama_models = [m for m in no_key_models if m.provider == ProviderType.OLLAMA]
        assert len(ollama_models) > 0

        # Check that they're marked correctly
        for model in ollama_models:
            assert not model.requires_api_key

    def test_available_models_list_returns_canonical_names(self):
        """Test that available models list returns canonical LiteLLM names."""
        available_keys = {
            "openai": True,
        }

        # This is a private method but we need to test it
        available_models = model_catalog._get_available_models_list(available_keys)

        # Should include OpenAI models
        assert "gpt-4" in available_models
        assert "gpt-3.5-turbo" in available_models

        # Should also include models that don't require API keys
        assert any("ollama/" in model for model in available_models)

    def test_get_model_by_litellm_name(self):
        """Test getting model by its LiteLLM name."""
        model = model_catalog.get_model_by_litellm_name("gpt-4")
        assert model is not None
        assert model.model_name == "gpt-4"
        assert model.provider == ProviderType.OPENAI

        model = model_catalog.get_model_by_litellm_name("claude-3-opus-20240229")
        assert model is not None
        assert model.provider == ProviderType.ANTHROPIC

    def test_model_capabilities(self):
        """Test that models have appropriate capabilities."""
        # GPT-4 should have multiple capabilities
        model = model_catalog.get_model_by_litellm_name("gpt-4")
        assert ModelCapability.CHAT_COMPLETION in model.capabilities
        assert ModelCapability.FUNCTION_CALLING in model.capabilities
        assert ModelCapability.STREAMING in model.capabilities

        # Embedding models should have embedding capability
        voyage_models = model_catalog.get_models_by_provider(ProviderType.VOYAGE)
        for model in voyage_models:
            assert ModelCapability.EMBEDDINGS in model.capabilities

    def test_provider_coverage(self):
        """Test that we have good provider coverage."""
        all_providers = model_catalog.get_providers()

        # Check major providers are included
        major_providers = [
            ProviderType.OPENAI,
            ProviderType.ANTHROPIC,
            ProviderType.GEMINI,
            ProviderType.BEDROCK,
            ProviderType.VERTEX_AI,
            ProviderType.MISTRAL,
            ProviderType.COHERE,
            ProviderType.TOGETHER,
            ProviderType.GROQ,
            ProviderType.DEEPSEEK,
            ProviderType.PERPLEXITY,
            ProviderType.OLLAMA,
        ]

        for provider in major_providers:
            assert provider in all_providers

            # Each provider should have at least one model
            models = model_catalog.get_models_by_provider(provider)
            assert len(models) > 0, f"No models found for {provider.value}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
