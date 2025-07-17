"""
Provider mapping utilities.

All API-key validation and management has been removed.  The only remaining
responsibility of this module is to map a model name to its provider.
"""

from __future__ import annotations


class ProviderConfig:
    """
    Lightweight helper that figures out which provider a model belongs to.

    All former API-key discovery / validation logic was stripped – GitHub OAuth
    is the only auth mechanism now, so every model is treated as available.
    """

    # Always empty – kept only so callers that introspect this attribute survive
    available_keys: dict[str, bool] = {}

    # Flag kept for backward-compat; always False
    require_api_keys: bool = False

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def get_model_provider(model_name: str) -> str:
        """Return a canonical provider slug for a model string."""
        model_lower = model_name.lower()

        if model_lower.startswith(("gpt", "openai", "o1")):
            return "openai"
        if model_lower.startswith(("claude", "anthropic")):
            return "anthropic"
        if model_lower.startswith(("gemini", "google")):
            return "gemini"
        if model_lower.startswith(("mistral", "mixtral")):
            return "mistral"
        if model_lower.startswith(("cohere", "command")):
            return "cohere"
        if model_lower.startswith("groq"):
            return "groq"
        if model_lower.startswith("perplexity"):
            return "perplexity"
        if model_lower.startswith("deepseek"):
            return "deepseek"
        # Default fallback
        return "openai"

    # --------------------------------------------------------------------- #
    # Compatibility shim – always succeed
    # --------------------------------------------------------------------- #
    def validate_model_credentials(self, model_name: str) -> tuple[bool, str]:
        """
        Compatibility method that now always passes.

        Returns
        -------
        tuple[bool, str]
            (True, "")  – credentials are considered valid in OAuth-only mode.
        """
        return True, ""
