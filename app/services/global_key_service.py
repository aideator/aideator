"""Global API key service for development mode."""

import os

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GlobalKeyService:
    """Service for managing global API keys in development mode."""

    def __init__(self):
        self.settings = get_settings()
        self._keys_cache: dict[str, str] = {}

    def get_provider_key(self, provider: str, user_id: str | None = None) -> str | None:
        """Get API key for provider, using global keys if per-user keys disabled."""

        # If per-user keys are required and we have a user, check user-specific keys first
        if self.settings.require_per_user_keys and user_id:
            # TODO: Implement user-specific key lookup
            # For now, fall back to global keys
            pass

        # Use global environment variables
        if provider == "openai":
            return self.settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if provider == "anthropic":
            return self.settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if provider == "google" or provider == "gemini":
            return self.settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if provider == "cohere":
            return os.getenv("COHERE_API_KEY")
        if provider == "together":
            return os.getenv("TOGETHER_API_KEY")
        if provider == "replicate":
            return os.getenv("REPLICATE_API_TOKEN")
        if provider == "huggingface":
            return os.getenv("HUGGINGFACE_API_KEY")
        if provider == "azure":
            return os.getenv("AZURE_API_KEY")
        if provider == "bedrock":
            return os.getenv("AWS_ACCESS_KEY_ID")  # AWS credentials
        if provider == "vertex_ai":
            return os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # Service account path

        logger.warning(f"No API key found for provider: {provider}")
        return None

    def has_provider_key(self, provider: str, user_id: str | None = None) -> bool:
        """Check if API key exists for provider."""
        return self.get_provider_key(provider, user_id) is not None

    def get_available_providers(self, user_id: str | None = None) -> dict[str, bool]:
        """Get list of providers and their availability."""
        providers = [
            "openai", "anthropic", "google", "cohere", "together",
            "replicate", "huggingface", "azure", "bedrock", "vertex_ai"
        ]

        return {
            provider: self.has_provider_key(provider, user_id)
            for provider in providers
        }

    def get_kubernetes_env_vars(self, user_id: str | None = None) -> dict[str, str]:
        """Get environment variables for Kubernetes agent containers."""
        env_vars = {}

        # Only include keys that exist
        for provider in ["openai", "anthropic", "google"]:
            key = self.get_provider_key(provider, user_id)
            if key:
                env_name = f"{provider.upper()}_API_KEY"
                if provider == "google":
                    env_name = "GEMINI_API_KEY"
                env_vars[env_name] = key

        return env_vars


# Global instance
global_key_service = GlobalKeyService()
