"""
Model catalog service for managing LiteLLM supported models.

This service dynamically discovers models from the LiteLLM proxy rather than
maintaining a hardcoded list. This ensures we always have the latest models
available without manual updates.
"""

import logging
from dataclasses import dataclass

from sqlmodel import select

from app.core.database import get_sync_session
from app.models.model_definition import ModelDefinitionDB
from app.models.provider import (
    ModelCapability,
    ModelDefinition,
    ProviderType,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a specific model."""

    provider: ProviderType
    model_name: str
    litellm_model_name: str
    display_name: str
    description: str | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_price_per_1m_tokens: float | None = None
    output_price_per_1m_tokens: float | None = None
    capabilities: list[ModelCapability] | None = None
    requires_api_key: bool = True
    requires_region: bool = False
    requires_project_id: bool = False

    def __post_init__(self) -> None:
        if self.capabilities is None:
            self.capabilities = []


class ModelCatalogService:
    """Service for managing the model catalog.

    Dynamically discovers models from the LiteLLM proxy rather than maintaining
    a static list. Includes caching to reduce API calls.
    """

    def __init__(self) -> None:
        self._models: dict[str, ModelInfo] = {}
        self._models_loaded = False

    def _ensure_models_loaded(self) -> None:
        """Ensure models are loaded from database (lazy loading)."""
        if not self._models_loaded:
            self._load_models_from_db()
            self._models_loaded = True

    def _load_models_from_db(self) -> None:
        """Load models from database."""
        try:
            for session in get_sync_session():
                # Query active models from database
                db_models = session.exec(
                    select(ModelDefinitionDB).where(ModelDefinitionDB.is_active)
                ).all()

                # Convert to ModelInfo objects
                for db_model in db_models:
                    # Map capabilities from tags
                    capabilities = []
                    if db_model.supports_streaming:
                        capabilities.append(ModelCapability.STREAMING)
                    if db_model.supports_function_calling:
                        capabilities.append(ModelCapability.FUNCTION_CALLING)
                    if db_model.supports_vision:
                        capabilities.append(ModelCapability.VISION)
                    if db_model.category and "embedding" in db_model.category:
                        capabilities.append(ModelCapability.EMBEDDINGS)
                    else:
                        capabilities.extend(
                            [
                                ModelCapability.TEXT_COMPLETION,
                                ModelCapability.CHAT_COMPLETION,
                            ]
                        )

                    # Map provider string to enum
                    provider_map = {
                        "openai": ProviderType.OPENAI,
                        "anthropic": ProviderType.ANTHROPIC,
                        "gemini": ProviderType.GEMINI,
                        "google": ProviderType.GEMINI,
                        "vertex_ai": ProviderType.VERTEX_AI,
                        "bedrock": ProviderType.BEDROCK,
                        "azure": ProviderType.AZURE,
                        "mistral": ProviderType.MISTRAL,
                        "cohere": ProviderType.COHERE,
                        "huggingface": ProviderType.HUGGINGFACE,
                        "together": ProviderType.TOGETHER,
                        "groq": ProviderType.GROQ,
                        "deepseek": ProviderType.DEEPSEEK,
                        "perplexity": ProviderType.PERPLEXITY,
                        "ollama": ProviderType.OLLAMA,
                    }

                    provider = provider_map.get(
                        (db_model.litellm_provider or "openai").lower(),
                        ProviderType.OPENAI,
                    )

                    model_info = ModelInfo(
                        provider=provider,
                        model_name=db_model.model_name,
                        litellm_model_name=db_model.model_name,  # Use same name
                        display_name=db_model.display_name,
                        description=db_model.description,
                        context_window=db_model.max_tokens,
                        max_output_tokens=db_model.max_output_tokens,
                        input_price_per_1m_tokens=db_model.input_cost_per_token
                        * 1_000_000
                        if db_model.input_cost_per_token
                        else None,
                        output_price_per_1m_tokens=db_model.output_cost_per_token
                        * 1_000_000
                        if db_model.output_cost_per_token
                        else None,
                        capabilities=capabilities,
                        requires_api_key=db_model.requires_api_key,
                    )

                    self._models[model_info.litellm_model_name] = model_info

                self._models_loaded = True
                logger.info(f"Loaded {len(self._models)} models from database")
        except Exception as e:
            logger.error(f"Failed to load models from database: {e!s}")
            # Database is not available or no models found - continue with empty model set
            self._models = {}
            self._models_loaded = True

    def get_all_models(self) -> list[ModelInfo]:
        """Get all available models."""
        self._ensure_models_loaded()
        return list(self._models.values())

    def get_models_by_provider(self, provider: ProviderType) -> list[ModelInfo]:
        """Get models from a specific provider."""
        self._ensure_models_loaded()
        return [model for model in self._models.values() if model.provider == provider]

    def get_models_by_capability(self, capability: ModelCapability) -> list[ModelInfo]:
        """Get models that support a specific capability."""
        self._ensure_models_loaded()
        return [
            model
            for model in self._models.values()
            if model.capabilities and capability in model.capabilities
        ]

    def get_models_without_api_key(self) -> list[ModelInfo]:
        """Get models that don't require API keys."""
        self._ensure_models_loaded()
        return [model for model in self._models.values() if not model.requires_api_key]

    def get_model_by_litellm_name(self, litellm_model_name: str) -> ModelInfo | None:
        """Get a model by its LiteLLM name."""
        self._ensure_models_loaded()
        return self._models.get(litellm_model_name)

    def validate_model_access(
        self, model_name: str, available_keys: dict[str, bool]
    ) -> tuple[bool, str]:
        """Validate that a model can be accessed with available API keys.

        Args:
            model_name: The model name to validate (can be model_name, litellm_model_name, display_name, or model_definition_id)
            available_keys: Dict of provider -> bool indicating available API keys

        Returns:
            tuple: (is_valid, error_message)
        """
        # Find the model
        model_info = None

        # First try direct lookup by litellm_model_name (most common case)
        self._ensure_models_loaded()
        model_info = self._models.get(model_name)

        if not model_info:
            # Try other lookups
            for model in self._models.values():
                # Generate the model definition ID for comparison
                model_definition_id = f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}"

                if model_name in (
                    model.model_name,
                    model.display_name,
                    model_definition_id,
                ):
                    model_info = model
                    break

        if not model_info:
            available_models = self._get_available_models_list(available_keys)
            return (
                False,
                f"Model '{model_name}' not found. Available models: {', '.join(available_models[:5])}...",
            )

        # Check if API key is required and available
        if model_info.requires_api_key:
            provider_key = model_info.provider.value
            if not available_keys.get(provider_key, False):
                return (
                    False,
                    f"Model '{model_name}' requires {model_info.provider.value.title()} API key, but none is configured.",
                )

        return True, ""

    def _get_available_models_list(self, available_keys: dict[str, bool]) -> list[str]:
        """Get list of available model names based on configured API keys."""
        self._ensure_models_loaded()
        available_models = []
        for model in self._models.values():
            if not model.requires_api_key or available_keys.get(
                model.provider.value, False
            ):
                available_models.append(model.litellm_model_name)
        return sorted(available_models)

    def get_available_models_for_keys(
        self, available_keys: dict[str, bool]
    ) -> list[ModelInfo]:
        """Get models that can be used with the available API keys."""
        self._ensure_models_loaded()
        available_models = []
        for model in self._models.values():
            if not model.requires_api_key or available_keys.get(
                model.provider.value, False
            ):
                available_models.append(model)
        return available_models

    def get_providers(self) -> list[ProviderType]:
        """Get all providers that have models."""
        self._ensure_models_loaded()
        return list({model.provider for model in self._models.values()})

    def get_capabilities(self) -> list[ModelCapability]:
        """Get all capabilities supported by any model."""
        self._ensure_models_loaded()
        capabilities: set[ModelCapability] = set()
        for model in self._models.values():
            if model.capabilities:
                capabilities.update(model.capabilities)
        return list(capabilities)

    def to_model_definitions(self) -> list[ModelDefinition]:
        """Convert model info to database model definitions."""
        self._ensure_models_loaded()
        definitions = []

        for model in self._models.values():
            definition = ModelDefinition(
                id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                provider=model.provider,
                model_name=model.model_name,
                litellm_model_name=model.litellm_model_name,
                display_name=model.display_name,
                description=model.description,
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                input_price_per_1m_tokens=model.input_price_per_1m_tokens,
                output_price_per_1m_tokens=model.output_price_per_1m_tokens,
                capabilities=model.capabilities,
                requires_api_key=model.requires_api_key,
                requires_region=model.requires_region,
                requires_project_id=model.requires_project_id,
            )
            definitions.append(definition)

        return definitions


# Global model catalog instance
model_catalog = ModelCatalogService()
