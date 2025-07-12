"""
Service for discovering all models that LiteLLM supports using its built-in model catalogs.
"""

import logging
from typing import Any

try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None  # type: ignore[assignment]
    LITELLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class LiteLLMModelDiscovery:
    """Service for discovering all models using LiteLLM's built-in knowledge."""

    def __init__(self):
        pass

    def get_all_supported_models(self) -> list[dict[str, Any]]:
        """
        Get all models that LiteLLM supports using its built-in model catalogs.

        Returns:
            List of model definitions with metadata
        """
        if not LITELLM_AVAILABLE:
            logger.error("LiteLLM not available - cannot discover models")
            return []

        logger.info("Discovering models from LiteLLM's built-in catalogs...")

        # Get all models from models_by_provider
        all_models = []
        if hasattr(litellm, "models_by_provider"):
            providers_data = litellm.models_by_provider

            for provider, models in providers_data.items():
                for model_name in models:
                    model_info = self._create_model_info(model_name, provider)
                    all_models.append(model_info)

        # Remove duplicates based on model_name
        unique_models = self._deduplicate_models(all_models)

        logger.info(f"Discovered {len(unique_models)} unique models")
        return unique_models

    def _create_model_info(self, model_name: str, provider: str) -> dict[str, Any]:
        """Create model info dictionary from model name and provider."""
        return {
            "model_name": model_name,
            "litellm_provider": provider,
            "display_name": self._generate_display_name(model_name),
            "description": self._generate_description(model_name, provider),
            "category": self._determine_category(model_name, provider),
            "tags": self._generate_tags(model_name, provider),
            "is_recommended": self._is_recommended(model_name),
            "is_popular": self._is_popular(model_name),
            "requires_api_key": self._requires_api_key(provider),
            "api_key_env_var": self._get_api_key_env_var(provider),
            "supports_streaming": True,  # Most models support streaming
            "supports_function_calling": self._supports_function_calling(model_name),
            "supports_vision": self._supports_vision(model_name),
            "source": "litellm_catalog",
        }

    def _deduplicate_models(self, models: list[dict]) -> list[dict]:
        """Remove duplicate models, preferring certain providers."""
        seen: set[str] = set()
        unique_models = []

        # Sort models to prefer certain providers
        provider_priority = {
            "openai": 1,
            "anthropic": 2,
            "cohere": 3,
            "groq": 4,
            "gemini": 5,
            "xai": 6,
            "deepseek": 7,
            "mistral": 8,
            "perplexity": 9,
        }

        models_sorted = sorted(
            models, key=lambda m: provider_priority.get(m["litellm_provider"], 100)
        )

        for model in models_sorted:
            model_name = model["model_name"]
            if model_name not in seen:
                seen.add(model_name)
                unique_models.append(model)

        return unique_models

    def _generate_display_name(self, model_name: str) -> str:
        """Generate a human-friendly display name."""
        # Remove provider prefixes
        name = model_name
        prefixes = [
            "openai/",
            "anthropic/",
            "vertex_ai/",
            "bedrock/",
            "azure/",
            "groq/",
            "mistral/",
            "deepseek/",
            "xai/",
            "gemini/",
            "cohere/",
            "perplexity/",
            "fireworks_ai/",
        ]
        for prefix in prefixes:
            name = name.replace(prefix, "")

        # Clean up account paths for fireworks
        if "accounts/fireworks/models/" in name:
            name = name.split("accounts/fireworks/models/")[-1]

        # Capitalize and format
        parts = name.replace("-", " ").replace("_", " ").split()
        formatted_parts = []
        for part in parts:
            if part.lower() in [
                "gpt",
                "ai",
                "api",
                "llm",
                "tts",
                "stt",
            ] or part.lower() in ["v1", "v2", "v3", "v4", "v5"]:
                formatted_parts.append(part.upper())
            else:
                formatted_parts.append(part.capitalize())

        return " ".join(formatted_parts)

    def _generate_description(self, model_name: str, provider: str) -> str:
        """Generate a description based on model characteristics."""
        descriptions = {
            "gpt-4o": "OpenAI's most advanced multimodal model",
            "gpt-4": "OpenAI's most capable model for complex tasks",
            "gpt-3.5-turbo": "Fast and efficient for most tasks",
            "claude-3-opus": "Anthropic's most powerful model",
            "claude-3-sonnet": "Balanced performance and cost from Anthropic",
            "claude-3-haiku": "Fast and lightweight Anthropic model",
            "claude-3-5-sonnet": "Anthropic's most advanced model",
            "gemini-pro": "Google's advanced reasoning model",
            "gemini-1.5-pro": "Google's multimodal model with large context",
            "gemini-1.5-flash": "Google's fastest model for high-volume tasks",
            "grok-beta": "xAI's conversational AI model",
            "deepseek-chat": "DeepSeek's general purpose model",
            "deepseek-reasoner": "DeepSeek's reasoning-focused model",
        }

        # Check for exact matches
        for key, desc in descriptions.items():
            if key in model_name.lower():
                return desc

        # Generate based on characteristics
        if "embed" in model_name.lower():
            return "Embedding model for semantic search and similarity"
        if "vision" in model_name.lower() or "multimodal" in model_name.lower():
            return "Multimodal model with vision capabilities"
        if "code" in model_name.lower() or "coder" in model_name.lower():
            return "Code generation and analysis model"
        if "whisper" in model_name.lower():
            return "Speech-to-text transcription model"
        if "tts" in model_name.lower():
            return "Text-to-speech synthesis model"
        if "rerank" in model_name.lower():
            return "Document reranking model"
        if "moderation" in model_name.lower():
            return "Content moderation model"
        return f"{provider.replace('_', ' ').title()} language model"

    def _determine_category(self, model_name: str, provider: str) -> str:
        """Determine the category of the model."""
        if "embed" in model_name.lower():
            return "embedding"
        if "vision" in model_name.lower() or "multimodal" in model_name.lower():
            return "vision"
        if "code" in model_name.lower() or "coder" in model_name.lower():
            return "code"
        if "whisper" in model_name.lower():
            return "speech-to-text"
        if "tts" in model_name.lower():
            return "text-to-speech"
        if "rerank" in model_name.lower():
            return "rerank"
        if "moderation" in model_name.lower():
            return "moderation"
        if any(
            x in model_name.lower()
            for x in ["gpt-4", "claude-3-opus", "claude-3-5", "gemini-pro", "grok"]
        ):
            return "advanced"
        return "general"

    def _generate_tags(self, model_name: str, provider: str) -> list[str]:
        """Generate tags for the model."""
        tags = []

        # Speed indicators
        if any(x in model_name.lower() for x in ["turbo", "flash", "fast", "instant"]):
            tags.append("fast")

        # Capability indicators
        if any(
            x in model_name.lower()
            for x in ["gpt-4", "opus", "pro", "grok", "reasoner"]
        ):
            tags.append("powerful")

        # Feature tags
        if "vision" in model_name.lower() or "multimodal" in model_name.lower():
            tags.append("vision")
        if "embed" in model_name.lower():
            tags.append("embedding")
        if "code" in model_name.lower():
            tags.append("code")
        if "whisper" in model_name.lower():
            tags.append("speech")
        if "tts" in model_name.lower():
            tags.append("audio")

        # Provider tag
        if provider:
            clean_provider = provider.replace("_", "-").replace("text-completion-", "")
            tags.append(clean_provider)

        return tags

    def _is_recommended(self, model_name: str) -> bool:
        """Determine if this is a recommended model."""
        recommended = [
            "gpt-4o",
            "gpt-4",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-5-sonnet",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "grok-beta",
            "deepseek-reasoner",
        ]
        return any(r in model_name.lower() for r in recommended)

    def _is_popular(self, model_name: str) -> bool:
        """Determine if this is a popular model."""
        popular = ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini", "grok", "deepseek"]
        return any(p in model_name.lower() for p in popular)

    def _requires_api_key(self, provider: str) -> bool:
        """Determine if the provider requires an API key."""
        # Most providers require API keys except local ones
        no_key_providers = ["ollama", "local", "huggingface_local"]
        return provider.lower() not in no_key_providers

    def _get_api_key_env_var(self, provider: str) -> str | None:
        """Get the environment variable name for a provider's API key."""
        provider_env_vars = {
            "openai": "OPENAI_API_KEY",
            "text-completion-openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "cohere": "COHERE_API_KEY",
            "cohere_chat": "COHERE_API_KEY",
            "replicate": "REPLICATE_API_KEY",
            "together_ai": "TOGETHER_API_KEY",
            "ai21": "AI21_API_KEY",
            "palm": "PALM_API_KEY",
            "vertex_ai": "GOOGLE_APPLICATION_CREDENTIALS",
            "bedrock": "AWS_ACCESS_KEY_ID",
            "azure": "AZURE_API_KEY",
            "groq": "GROQ_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "xai": "XAI_API_KEY",
            "cerebras": "CEREBRAS_API_KEY",
            "fireworks_ai": "FIREWORKS_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "google": "GEMINI_API_KEY",
        }
        return provider_env_vars.get(provider.lower())

    def _supports_function_calling(self, model_name: str) -> bool:
        """Determine if the model supports function calling."""
        function_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini", "grok"]
        return any(f in model_name.lower() for f in function_models)

    def _supports_vision(self, model_name: str) -> bool:
        """Determine if the model supports vision."""
        return "vision" in model_name.lower() or any(
            v in model_name.lower()
            for v in [
                "gpt-4o",
                "gpt-4-vision",
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-5-sonnet",
                "gemini-pro-vision",
                "gemini-1.5",
                "gemini-2.0",
                "grok-vision",
            ]
        )


# Singleton instance
litellm_model_discovery = LiteLLMModelDiscovery()
