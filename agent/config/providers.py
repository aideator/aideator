"""
Provider configuration and API key management.

Handles API key validation and provider detection.
"""

import os
from typing import Dict, Tuple


# Constants for validation
MIN_API_KEY_LENGTH = 10
MIN_GENERIC_KEY_LENGTH = 5


class ProviderConfig:
    """Manages API keys and provider validation."""
    
    def __init__(self):
        """Initialize with current API key state."""
        self.available_keys = self._check_available_api_keys()
    
    def _check_available_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are available for different providers."""
        available_keys = {}

        # Check OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        available_keys["openai"] = bool(
            openai_key
            and openai_key.strip()
            and openai_key != "sk-"
            and len(openai_key) > MIN_API_KEY_LENGTH
        )

        # Check Anthropic API Key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        available_keys["anthropic"] = bool(
            anthropic_key
            and anthropic_key.strip()
            and anthropic_key.startswith("sk-ant-")
        )

        # Check Gemini API Key
        gemini_key = os.getenv("GEMINI_API_KEY")
        available_keys["gemini"] = bool(
            gemini_key 
            and gemini_key.strip() 
            and gemini_key.startswith("AIza")
        )

        # Check other provider keys
        for provider, env_var in [
            ("mistral", "MISTRAL_API_KEY"),
            ("cohere", "COHERE_API_KEY"),
            ("groq", "GROQ_API_KEY"),
            ("perplexity", "PERPLEXITY_API_KEY"),
            ("deepseek", "DEEPSEEK_API_KEY"),
        ]:
            key = os.getenv(env_var)
            available_keys[provider] = bool(
                key and key.strip() and len(key) > MIN_GENERIC_KEY_LENGTH
            )

        return available_keys

    def get_model_provider(self, model_name: str) -> str:
        """Get the provider for a given model name."""
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
        # Default to openai for unknown models
        return "openai"

    def validate_model_credentials(self, model_name: str) -> Tuple[bool, str]:
        """Validate that credentials are available for the requested model.

        Returns:
            tuple: (is_valid, error_message)
        """
        provider = self.get_model_provider(model_name)

        if not self.available_keys.get(provider, False):
            provider_names = {
                "openai": "OpenAI",
                "anthropic": "Anthropic (Claude)",
                "gemini": "Google Gemini",
                "mistral": "Mistral AI",
                "cohere": "Cohere",
                "groq": "Groq",
                "perplexity": "Perplexity",
                "deepseek": "DeepSeek",
            }

            readable_provider = provider_names.get(provider, provider.title())

            error_msg = f"""
🚫 **Missing API Key for {readable_provider}**

The model '{model_name}' requires a {readable_provider} API key, but none was found.

**To fix this issue:**

1. **Get an API key** from {readable_provider}:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/
   - Google Gemini: https://ai.google.dev/
   - Mistral AI: https://console.mistral.ai/
   - Cohere: https://dashboard.cohere.ai/
   - Groq: https://console.groq.com/
   - Perplexity: https://www.perplexity.ai/settings/api
   - DeepSeek: https://platform.deepseek.com/

2. **Add the secret to Kubernetes**:
   ```bash
   kubectl create secret generic {provider}-secret \\
     --from-literal=api-key="your-api-key-here" \\
     -n aideator
   ```

3. **Try again** - The model should work once the API key is configured.

**Available models:** Try using a model from a provider that has been configured with API keys.

{self._get_available_models_suggestion()}
"""
            return False, error_msg

        return True, ""

    def _get_available_models_suggestion(self) -> str:
        """Get a helpful suggestion of available models based on configured API keys."""
        available_providers = [
            provider
            for provider, available in self.available_keys.items()
            if available
        ]

        if not available_providers:
            return "No API keys are currently configured. Please add at least one API key to use any models."

        suggestions = []
        for provider in available_providers:
            if provider == "openai":
                suggestions.append("- OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo")
            elif provider == "anthropic":
                suggestions.append("- Anthropic: claude-3-5-sonnet, claude-3-haiku")
            elif provider == "gemini":
                suggestions.append("- Google: gemini-1.5-pro, gemini-1.5-flash")
            elif provider == "mistral":
                suggestions.append(
                    "- Mistral: mistral-large-latest, mistral-small-latest"
                )
            elif provider == "cohere":
                suggestions.append("- Cohere: command-r-plus, command-r")
            elif provider == "groq":
                suggestions.append("- Groq: llama3-8b-8192")
            elif provider == "perplexity":
                suggestions.append("- Perplexity: llama-3.1-sonar-small-128k-online")
            elif provider == "deepseek":
                suggestions.append("- DeepSeek: deepseek-chat")

        return "**Available models with configured API keys:**\n" + "\n".join(
            suggestions
        )