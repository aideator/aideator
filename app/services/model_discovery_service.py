"""
Service for discovering all possible models using LiteLLM's native capabilities.
"""

import logging
import os
from typing import Any

try:
    import litellm
    from litellm import get_valid_models
except ImportError:
    litellm = None  # type: ignore[assignment]
    get_valid_models = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class ModelDiscoveryService:
    """Service for discovering all possible models without requiring proxy configuration."""

    def __init__(self):
        pass

    def get_all_possible_models(
        self, provider_keys: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Get all possible models using LiteLLM's native discovery capabilities.

        Args:
            provider_keys: Dictionary of provider -> api_key mappings

        Returns:
            List of model definitions with metadata
        """
        if litellm is None or get_valid_models is None:
            logger.error("LiteLLM not available - cannot discover models")
            return []

        all_models = []

        # 1. Get models from LiteLLM's comprehensive catalog
        all_models.extend(self._get_litellm_catalog_models())

        # 2. If we have API keys, discover models from provider endpoints
        if provider_keys:
            all_models.extend(self._discover_models_from_providers(provider_keys))

        # 3. Remove duplicates and enrich with metadata
        unique_models = self._deduplicate_and_enrich_models(all_models)

        logger.info(f"Discovered {len(unique_models)} unique models")
        return unique_models

    def _get_litellm_catalog_models(self) -> list[dict[str, Any]]:
        """Get models from LiteLLM's comprehensive model catalog."""
        models = []

        try:
            # LiteLLM maintains lists of supported models for each provider
            providers_and_models = {
                "openai": getattr(litellm, "open_ai_chat_completion_models", [])
                + getattr(litellm, "open_ai_text_completion_models", []),
                "anthropic": getattr(litellm, "anthropic_models", []),
                "cohere": getattr(litellm, "cohere_models", []),
                "replicate": getattr(litellm, "replicate_models", []),
                "palm": getattr(litellm, "palm_models", []),
                "together_ai": getattr(litellm, "together_ai_models", []),
                "ai21": getattr(litellm, "ai21_models", []),
                "baseten": getattr(litellm, "baseten_models", []),
                "aleph_alpha": getattr(litellm, "aleph_alpha_models", []),
                "nlp_cloud": getattr(litellm, "nlp_cloud_models", []),
                "vertex_ai": getattr(litellm, "vertex_ai_models", []),
                "bedrock": getattr(litellm, "bedrock_models", []),
                "azure": getattr(litellm, "azure_models", []),
                "groq": getattr(litellm, "groq_models", []),
                "perplexity": getattr(litellm, "perplexity_models", []),
                "mistral": getattr(litellm, "mistral_models", []),
                "deepseek": getattr(litellm, "deepseek_models", []),
                "xai": getattr(litellm, "xai_models", []),
                "cerebras": getattr(litellm, "cerebras_models", []),
                "fireworks_ai": getattr(litellm, "fireworks_ai_models", []),
                "ollama": getattr(litellm, "ollama_models", []),
                "huggingface": getattr(litellm, "huggingface_models", []),
            }

            for provider, model_list in providers_and_models.items():
                for model_name in model_list:
                    if model_name:  # Skip empty strings
                        models.append(
                            {
                                "model_name": model_name,
                                "litellm_provider": provider,
                                "source": "litellm_catalog",
                                "requires_api_key": provider not in ["ollama"],
                                "api_key_env_var": self._get_api_key_env_var(provider),
                            }
                        )

        except Exception as e:
            logger.warning(f"Failed to get models from LiteLLM catalog: {e}")

        return models

    def _discover_models_from_providers(
        self, provider_keys: dict[str, str]
    ) -> list[dict[str, Any]]:
        """Discover models by calling provider endpoints with API keys."""
        models = []

        for provider, api_key in provider_keys.items():
            try:
                # Temporarily set environment variable for LiteLLM
                old_env = os.environ.copy()
                env_var = self._get_api_key_env_var(provider)
                if env_var:
                    os.environ[env_var] = api_key

                # Use LiteLLM's get_valid_models to discover from this provider
                discovered = get_valid_models(
                    check_provider_endpoint=True, custom_llm_provider=provider
                )

                for model_name in discovered:
                    models.append(
                        {
                            "model_name": model_name,
                            "litellm_provider": provider,
                            "source": "provider_endpoint",
                            "requires_api_key": True,
                            "api_key_env_var": env_var,
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to discover models from {provider}: {e}")
            finally:
                # Restore original environment
                os.environ.clear()
                os.environ.update(old_env)

        return models

    def _deduplicate_and_enrich_models(
        self, models: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Remove duplicates and add enriched metadata."""
        seen_models: set[str] = set()
        unique_models = []

        for model in models:
            model_name = model["model_name"]

            # Skip duplicates (prefer provider_endpoint over catalog)
            if model_name in seen_models:
                continue
            seen_models.add(model_name)

            # Enrich with additional metadata
            enriched = {
                **model,
                "display_name": self._generate_display_name(model_name),
                "description": self._generate_description(
                    model_name, model.get("litellm_provider")
                ),
                "category": self._determine_category(
                    model_name, model.get("litellm_provider")
                ),
                "tags": self._generate_tags(model_name, model.get("litellm_provider")),
                "is_recommended": self._is_recommended(model_name),
                "is_popular": self._is_popular(model_name),
                "supports_streaming": True,  # Most models support streaming
                "supports_function_calling": self._supports_function_calling(
                    model_name
                ),
                "supports_vision": self._supports_vision(model_name),
            }

            unique_models.append(enriched)

        return unique_models

    def _get_api_key_env_var(self, provider: str) -> str | None:
        """Get the environment variable name for a provider's API key."""
        provider_env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "cohere": "COHERE_API_KEY",
            "replicate": "REPLICATE_API_KEY",
            "together_ai": "TOGETHER_API_KEY",
            "together": "TOGETHER_API_KEY",
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
            "fireworks": "FIREWORKS_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "google": "GEMINI_API_KEY",
        }
        return provider_env_vars.get(provider.lower())

    def _generate_display_name(self, model_name: str) -> str:
        """Generate a human-friendly display name."""
        # Remove provider prefixes
        name = model_name
        for prefix in [
            "openai/",
            "anthropic/",
            "vertex_ai/",
            "bedrock/",
            "azure/",
            "groq/",
            "mistral/",
            "deepseek/",
            "xai/",
        ]:
            name = name.replace(prefix, "")

        # Special handling for known patterns
        if name.startswith("gpt-"):
            # Keep GPT models hyphenated (e.g., GPT-4, GPT-3.5)
            if "turbo" in name:
                return name.upper().replace("GPT-", "GPT-").replace("-TURBO", " Turbo")
            return name.upper().replace("GPT-", "GPT-")

        # Handle other special cases
        special_cases = {
            "claude-3-opus-20240229": "Claude 3 Opus",
            "claude-3-opus": "Claude 3 Opus",
            "claude-3-sonnet": "Claude 3 Sonnet",
            "claude-3-haiku": "Claude 3 Haiku",
            "llama-2-70b-chat": "Llama 2 70B Chat",
            "text-embedding-ada-002": "Text Embedding Ada 002",
        }

        if name in special_cases:
            return special_cases[name]

        # Capitalize and format
        parts = name.replace("-", " ").replace("_", " ").split()
        formatted_parts = []
        for part in parts:
            if part.lower() in ["gpt", "ai", "api", "llm"]:
                formatted_parts.append(part.upper())
            elif part.lower() in ["ada", "turbo", "opus", "sonnet", "haiku"]:
                formatted_parts.append(part.capitalize())
            elif part.endswith("b") and part[:-1].isdigit():  # e.g., "70b"
                formatted_parts.append(part.upper())
            else:
                formatted_parts.append(part.capitalize())

        return " ".join(formatted_parts)

    def _generate_description(self, model_name: str, provider: str | None) -> str:
        """Generate a description based on model characteristics."""
        descriptions = {
            "gpt-4o": "OpenAI's most advanced multimodal model",
            "gpt-4": "OpenAI's most capable model for complex tasks",
            "gpt-3.5-turbo": "Fast and efficient for most tasks",
            "claude-3-opus": "Anthropic's most powerful model",
            "claude-3-sonnet": "Balanced performance and cost from Anthropic",
            "claude-3-haiku": "Fast and lightweight Anthropic model",
            "gemini-pro": "Google's advanced reasoning model",
            "gemini-1.5-pro": "Google's multimodal model with large context",
            "gemini-1.5-flash": "Google's fastest model for high-volume tasks",
        }

        # Check for exact match
        for key, desc in descriptions.items():
            if key in model_name.lower():
                return desc

        # Generate based on characteristics
        if "embed" in model_name.lower():
            return "Embedding model for semantic search and similarity"
        if "vision" in model_name.lower() or "multimodal" in model_name.lower():
            return "Multimodal model with vision capabilities"
        if "code" in model_name.lower():
            return "Code generation and analysis model"
        if provider:
            return f"{provider.title()} language model"

        return "General purpose language model"

    def _determine_category(self, model_name: str, provider: str | None) -> str:
        """Determine the category of the model."""
        if "embed" in model_name.lower():
            return "embedding"
        if "vision" in model_name.lower() or "multimodal" in model_name.lower():
            return "vision"
        if "code" in model_name.lower() or "codex" in model_name.lower():
            return "code"
        if any(
            x in model_name.lower() for x in ["gpt-4", "claude-3-opus", "gemini-pro"]
        ):
            return "advanced"
        return "general"

    def _generate_tags(self, model_name: str, provider: str | None) -> list[str]:
        """Generate tags for the model."""
        tags = []

        if "turbo" in model_name.lower() or "flash" in model_name.lower():
            tags.append("fast")
        if any(x in model_name.lower() for x in ["gpt-4", "opus", "pro"]):
            tags.append("powerful")
        if "vision" in model_name.lower() or "multimodal" in model_name.lower():
            tags.append("vision")
        if "embed" in model_name.lower():
            tags.append("embedding")
        if "code" in model_name.lower():
            tags.append("code")
        if provider:
            tags.append(provider.lower())

        return tags

    def _is_recommended(self, model_name: str) -> bool:
        """Determine if this is a recommended model."""
        recommended = [
            "gpt-4o",
            "gpt-4",
            "claude-3-opus",
            "claude-3-sonnet",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        return any(r in model_name.lower() for r in recommended)

    def _is_popular(self, model_name: str) -> bool:
        """Determine if this is a popular model."""
        popular = ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini"]
        return any(p in model_name.lower() for p in popular)

    def _supports_function_calling(self, model_name: str) -> bool:
        """Determine if the model supports function calling."""
        function_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini"]
        return any(f in model_name.lower() for f in function_models)

    def _supports_vision(self, model_name: str) -> bool:
        """Determine if the model supports vision."""
        vision_models = [
            "gpt-4o",
            "gpt-4-vision",
            "claude-3-opus",
            "claude-3-sonnet",
            "gemini-pro-vision",
            "gemini-1.5",
        ]
        return any(v in model_name.lower() for v in vision_models)


# Singleton instance
model_discovery_service = ModelDiscoveryService()
