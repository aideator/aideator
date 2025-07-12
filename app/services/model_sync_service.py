"""
Service for synchronizing model definitions using LiteLLM's native discovery capabilities.
"""

import logging
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.model_definition import ModelDefinitionDB, ModelSyncLog

logger = logging.getLogger(__name__)


class ModelSyncService:
    """Synchronizes model definitions from LiteLLM proxy to our database."""

    def __init__(self) -> None:
        settings = get_settings()
        self.proxy_base_url = settings.LITELLM_PROXY_URL or "http://localhost:4000"
        self.proxy_api_key = settings.LITELLM_MASTER_KEY or ""

    async def sync_models(self, session: Session | AsyncSession) -> ModelSyncLog:
        """Fetch models from LiteLLM proxy and sync to database.

        Returns:
            ModelSyncLog with details of the sync operation
        """
        sync_log = ModelSyncLog(status="in_progress")
        session.add(sync_log)
        if isinstance(session, AsyncSession):
            await session.commit()
        else:
            session.commit()

        try:
            # Fetch models from LiteLLM proxy
            models_data = await self._fetch_models_from_proxy()
            sync_log.models_discovered = len(models_data)

            # Process each model
            for model_data in models_data:
                try:
                    await self._process_model(session, model_data, sync_log)
                    if isinstance(session, AsyncSession):
                        await session.commit()
                    else:
                        session.commit()  # Commit after each model to avoid conflicts
                except Exception as e:
                    if isinstance(session, AsyncSession):
                        await session.rollback()
                    else:
                        session.rollback()
                    # If it's a unique constraint violation, the model already exists - skip it
                    if "duplicate key value violates unique constraint" in str(e):
                        logger.warning(
                            f"Model {model_data.get('model_name')} already exists, skipping"
                        )
                        continue
                    # Re-raise other exceptions
                    raise

            # Deactivate models not seen in this sync
            await self._deactivate_missing_models(session, models_data, sync_log)

            sync_log.status = "success"
            sync_log.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Model sync failed: {e!s}")
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()

        if isinstance(session, AsyncSession):
            await session.commit()
        else:
            session.commit()
        return sync_log

    async def _fetch_models_from_proxy(self) -> list[dict[str, Any]]:
        """Fetch model information from LiteLLM proxy."""
        headers = {}
        if self.proxy_api_key:
            headers["Authorization"] = f"Bearer {self.proxy_api_key}"

        async with httpx.AsyncClient() as client:
            # First get basic model list
            models_response = await client.get(
                f"{self.proxy_base_url}/v1/models", headers=headers, timeout=30.0
            )
            models_response.raise_for_status()
            models_list = models_response.json().get("data", [])

            # Then get detailed model info
            model_info_response = await client.get(
                f"{self.proxy_base_url}/v1/model/info", headers=headers, timeout=30.0
            )
            model_info_response.raise_for_status()
            model_info_data = model_info_response.json().get("data", [])

            # Merge the data
            model_info_map = {info["model_name"]: info for info in model_info_data}

            merged_models = []
            for model in models_list:
                model_name = model["id"]
                if model_name in model_info_map:
                    merged_models.append(model_info_map[model_name])
                else:
                    # Basic info only
                    merged_models.append(
                        {
                            "model_name": model_name,
                            "litellm_params": {"model": model_name},
                            "model_info": {},
                        }
                    )

            return merged_models

    async def _process_model(
        self,
        session: Session | AsyncSession,
        model_data: dict[str, Any],
        sync_log: ModelSyncLog,
    ) -> None:
        """Process a single model from the proxy."""
        model_name = model_data["model_name"]
        model_info = model_data.get("model_info", {})

        # Check if model exists
        if isinstance(session, AsyncSession):
            result = await session.execute(
                select(ModelDefinitionDB).where(
                    ModelDefinitionDB.model_name == model_name
                )
            )
            existing_model = result.scalar_one_or_none()
        else:
            existing_model = session.exec(
                select(ModelDefinitionDB).where(
                    ModelDefinitionDB.model_name == model_name
                )
            ).first()

        if existing_model:
            # Update existing model
            existing_model.last_seen_at = datetime.utcnow()
            existing_model.is_active = True

            # Update fields from proxy
            provider = model_info.get("litellm_provider", "unknown")
            existing_model.provider = provider
            existing_model.litellm_provider = provider
            existing_model.max_tokens = model_info.get("max_tokens")
            existing_model.max_input_tokens = model_info.get("max_input_tokens")
            existing_model.max_output_tokens = model_info.get("max_output_tokens")
            existing_model.input_cost_per_token = model_info.get("input_cost_per_token")
            existing_model.output_cost_per_token = model_info.get(
                "output_cost_per_token"
            )
            existing_model.supports_function_calling = (
                model_info.get("supports_function_calling")
                if model_info.get("supports_function_calling") is not None
                else False
            )
            existing_model.supports_vision = (
                model_info.get("supports_vision")
                if model_info.get("supports_vision") is not None
                else False
            )
            existing_model.supports_streaming = (
                model_info.get("supports_streaming")
                if model_info.get("supports_streaming") is not None
                else True
            )

            sync_log.models_updated += 1

        else:
            # Create new model
            provider = model_info.get("litellm_provider", "unknown")
            new_model = ModelDefinitionDB(
                model_name=model_name,
                provider=provider,
                litellm_provider=provider,
                litellm_model_name=model_name,
                display_name=self._generate_display_name(model_name),
                max_tokens=model_info.get("max_tokens"),
                max_input_tokens=model_info.get("max_input_tokens"),
                max_output_tokens=model_info.get("max_output_tokens"),
                input_cost_per_token=model_info.get("input_cost_per_token"),
                output_cost_per_token=model_info.get("output_cost_per_token"),
                supports_function_calling=model_info.get("supports_function_calling")
                if model_info.get("supports_function_calling") is not None
                else False,
                supports_vision=model_info.get("supports_vision")
                if model_info.get("supports_vision") is not None
                else False,
                supports_streaming=model_info.get("supports_streaming")
                if model_info.get("supports_streaming") is not None
                else True,
                description=self._generate_description(model_name, model_info),
                category=self._determine_category(model_name, model_info),
                tags=self._generate_tags(model_name, model_info),
                is_recommended=self._is_recommended(model_name),
                is_popular=self._is_popular(model_name),
                requires_api_key=self._requires_api_key(model_info),
                api_key_env_var=self._get_api_key_env_var(model_info),
                extra_metadata=model_info,
            )
            session.add(new_model)
            sync_log.models_added += 1

    async def _deactivate_missing_models(
        self,
        session: Session | AsyncSession,
        current_models: list[dict[str, Any]],
        sync_log: ModelSyncLog,
    ) -> None:
        """Deactivate models that weren't seen in the current sync."""
        current_model_names = {m["model_name"] for m in current_models}

        # Find active models not in current sync
        if isinstance(session, AsyncSession):
            result = await session.execute(
                select(ModelDefinitionDB).where(ModelDefinitionDB.is_active)
            )
            active_models = result.scalars().all()
        else:
            active_models = session.exec(
                select(ModelDefinitionDB).where(ModelDefinitionDB.is_active)
            ).all()

        for model in active_models:
            if model.model_name not in current_model_names:
                model.is_active = False
                model.last_seen_at = datetime.utcnow()
                sync_log.models_deactivated += 1

    def _generate_display_name(self, model_name: str) -> str:
        """Generate a human-friendly display name."""
        # Remove provider prefixes
        name = model_name.replace("openai/", "").replace("anthropic/", "")
        name = name.replace("vertex_ai/", "").replace("bedrock/", "")

        # Capitalize and format
        parts = name.replace("-", " ").replace("_", " ").split()
        formatted_parts = []
        for part in parts:
            if part.lower() in ["gpt", "ai", "api"]:
                formatted_parts.append(part.upper())
            else:
                formatted_parts.append(part.capitalize())

        return " ".join(formatted_parts)

    def _generate_description(self, model_name: str, model_info: dict[str, Any]) -> str:
        """Generate a description based on model characteristics."""
        descriptions = {
            "gpt-4": "OpenAI's most capable model for complex tasks",
            "gpt-4o": "OpenAI's optimized GPT-4 with faster performance",
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
        if model_info.get("supports_vision"):
            return "Multimodal model with vision capabilities"
        if "embed" in model_name.lower():
            return "Embedding model for semantic search and similarity"
        if (model_info.get("max_tokens") or 0) > 100000:
            return "Large context window model"
        return "General purpose language model"

    def _determine_category(self, model_name: str, model_info: dict[str, Any]) -> str:
        """Determine the category of the model."""
        if "embed" in model_name.lower():
            return "embedding"
        if model_info.get("supports_vision"):
            return "vision"
        if "code" in model_name.lower() or "codex" in model_name.lower():
            return "code"
        if any(
            x in model_name.lower() for x in ["gpt-4", "claude-3-opus", "gemini-pro"]
        ):
            return "advanced"
        return "general"

    def _generate_tags(self, model_name: str, model_info: dict[str, Any]) -> list[str]:
        """Generate tags for the model."""
        tags = []

        if model_info.get("supports_function_calling"):
            tags.append("functions")
        if model_info.get("supports_vision"):
            tags.append("vision")
        if model_info.get("supports_streaming"):
            tags.append("streaming")
        if (model_info.get("max_tokens") or 0) > 100000:
            tags.append("large-context")
        if "turbo" in model_name.lower() or "flash" in model_name.lower():
            tags.append("fast")
        if any(x in model_name.lower() for x in ["gpt-4", "opus", "pro"]):
            tags.append("powerful")

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

    def _requires_api_key(self, model_info: dict[str, Any]) -> bool:
        """Determine if the model requires an API key."""
        # Most models require API keys except local ones
        provider = model_info.get("litellm_provider", "").lower()
        return provider not in ["ollama", "local"]

    def _get_api_key_env_var(self, model_info: dict[str, Any]) -> str | None:
        """Get the environment variable name for the API key."""
        provider_env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "cohere": "COHERE_API_KEY",
            "replicate": "REPLICATE_API_KEY",
            "together": "TOGETHER_API_KEY",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        provider = model_info.get("litellm_provider", "").lower()
        return provider_env_vars.get(provider)


# Singleton instance
model_sync_service = ModelSyncService()
