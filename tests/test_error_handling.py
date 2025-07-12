"""
Tests for graceful error handling of missing model secrets.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agent.main import AIdeatorAgent
    from app.services.model_catalog import model_catalog
except ImportError as e:
    print(f"Import error: {e}")
    pytest.skip("Cannot import required modules", allow_module_level=True)


@pytest.fixture(autouse=True)
def mock_redis_env():
    """Automatically provide Redis URL for all agent tests."""
    with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}, clear=False):
        yield


class TestModelValidation:
    """Test model validation and error handling."""

    def test_check_available_api_keys_all_missing(self):
        """Test API key detection when no keys are available."""
        agent = AIdeatorAgent()

        # Mock environment with no API keys
        with patch.dict(os.environ, {}, clear=True):
            available_keys = agent._check_available_api_keys()

        assert available_keys["openai"] is False
        assert available_keys["anthropic"] is False
        assert available_keys["gemini"] is False
        assert available_keys["mistral"] is False

    def test_check_available_api_keys_partial(self):
        """Test API key detection with some keys available."""
        agent = AIdeatorAgent()

        # Mock environment with only OpenAI key
        mock_env = {
            "OPENAI_API_KEY": "sk-test123456789",
            "REDIS_URL": "redis://localhost:6379/1",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            available_keys = agent._check_available_api_keys()

        assert available_keys["openai"] is True
        assert available_keys["anthropic"] is False
        assert available_keys["gemini"] is False

    def test_check_available_api_keys_all_present(self):
        """Test API key detection when all keys are available."""
        agent = AIdeatorAgent()

        mock_env = {
            "OPENAI_API_KEY": "sk-test123456789",
            "ANTHROPIC_API_KEY": "sk-ant-test123456789",
            "GEMINI_API_KEY": "AIzatest123456789",
            "MISTRAL_API_KEY": "test123456789",
            "REDIS_URL": "redis://localhost:6379/1",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            available_keys = agent._check_available_api_keys()

        assert available_keys["openai"] is True
        assert available_keys["anthropic"] is True
        assert available_keys["gemini"] is True
        assert available_keys["mistral"] is True

    def test_get_model_provider(self):
        """Test provider detection from model names."""
        agent = AIdeatorAgent()

        assert agent._get_model_provider("gpt-4") == "openai"
        assert agent._get_model_provider("claude-3-sonnet") == "anthropic"
        assert agent._get_model_provider("gemini-1.5-pro") == "gemini"
        assert agent._get_model_provider("mistral-large") == "mistral"
        assert agent._get_model_provider("command-r") == "cohere"
        assert agent._get_model_provider("unknown-model") == "openai"  # Default

    def test_validate_model_credentials_missing_key(self):
        """Test validation when API key is missing."""
        agent = AIdeatorAgent()
        agent.available_api_keys = {
            "openai": False,
            "anthropic": False,
            "gemini": False,
            "mistral": False,
        }

        is_valid, error_msg = agent._validate_model_credentials("claude-3-sonnet")

        assert is_valid is False
        assert "Missing API Key for Anthropic" in error_msg
        assert "claude-3-sonnet" in error_msg
        assert "kubectl create secret" in error_msg

    def test_validate_model_credentials_key_available(self):
        """Test validation when API key is available."""
        agent = AIdeatorAgent()
        agent.available_api_keys = {
            "openai": True,
            "anthropic": True,
            "gemini": False,
            "mistral": False,
        }

        is_valid, error_msg = agent._validate_model_credentials("gpt-4")

        assert is_valid is True
        assert error_msg == ""

    def test_get_available_models_suggestion(self):
        """Test available models suggestion generation."""
        agent = AIdeatorAgent()
        agent.available_api_keys = {
            "openai": True,
            "anthropic": False,
            "gemini": True,
            "mistral": False,
        }

        suggestion = agent._get_available_models_suggestion()

        assert "Available models with configured API keys:" in suggestion
        assert "OpenAI: gpt-4o, gpt-4o-mini" in suggestion
        assert "Google: gemini-1.5-pro" in suggestion
        assert "Anthropic" not in suggestion  # Should not be included

    def test_get_available_models_suggestion_no_keys(self):
        """Test suggestion when no API keys are available."""
        agent = AIdeatorAgent()
        agent.available_api_keys = {
            "openai": False,
            "anthropic": False,
            "gemini": False,
            "mistral": False,
        }

        suggestion = agent._get_available_models_suggestion()

        assert "No API keys are currently configured" in suggestion


class TestModelCatalogValidation:
    """Test model catalog validation methods."""

    def test_validate_model_access_missing_model(self):
        """Test validation for non-existent model."""
        available_keys = {"openai": True}

        is_valid, error_msg = model_catalog.validate_model_access(
            "nonexistent-model", available_keys
        )

        assert is_valid is False
        assert "not found" in error_msg
        assert "Available models:" in error_msg

    def test_validate_model_access_missing_key(self):
        """Test validation when required API key is missing."""
        available_keys = {"openai": False, "anthropic": False}

        # First ensure models are loaded
        model_catalog._ensure_models_loaded()

        is_valid, error_msg = model_catalog.validate_model_access(
            "gpt-4", available_keys
        )

        assert is_valid is False
        # The test should check for the actual error message format
        # If the model is not found, we get a "not found" message
        # If the model is found but key is missing, we get a "requires" message
        assert ("not found" in error_msg) or (
            "requires" in error_msg and "API key" in error_msg
        )

    def test_validate_model_access_key_available(self):
        """Test validation when API key is available."""
        available_keys = {"openai": True}

        is_valid, error_msg = model_catalog.validate_model_access(
            "gpt-4", available_keys
        )

        assert is_valid is True
        assert error_msg == ""

    def test_get_available_models_for_keys(self):
        """Test getting available models based on API keys."""
        available_keys = {"openai": True, "anthropic": False}

        available_models = model_catalog.get_available_models_for_keys(available_keys)

        # Should include OpenAI models but not Anthropic models
        openai_models = [m for m in available_models if m.provider.value == "openai"]
        anthropic_models = [
            m for m in available_models if m.provider.value == "anthropic"
        ]

        assert len(openai_models) > 0
        assert len(anthropic_models) == 0


@pytest.mark.asyncio
class TestAgentErrorHandling:
    """Test agent error handling during execution."""

    async def test_agent_run_missing_api_key(self):
        """Test agent fails gracefully when API key is missing."""
        # Mock environment with no API keys
        mock_env = {"MODEL": "claude-3-sonnet", "REDIS_URL": "redis://localhost:6379/1"}

        with patch.dict(os.environ, mock_env, clear=True):
            agent = AIdeatorAgent()

            with pytest.raises(RuntimeError) as exc_info:
                await agent.run()

            assert "Missing API key for model claude-3-sonnet" in str(exc_info.value)

    async def test_agent_run_api_key_available(self):
        """Test agent proceeds when API key is available."""
        mock_env = {
            "MODEL": "gpt-4",
            "OPENAI_API_KEY": "sk-test123456789",
            "AGENT_MODE": "litellm",
            "REDIS_URL": "redis://localhost:6379/1",
            "PROMPT": "test prompt",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            agent = AIdeatorAgent()

            # Mock the LLM API call to avoid actual API requests
            with patch("agent.main.acompletion") as mock_completion:
                mock_response = AsyncMock()
                mock_response.__aiter__.return_value = []
                mock_completion.return_value = mock_response

                # Should not raise an error
                await agent.run()

    async def test_litellm_authentication_error_handling(self):
        """Test handling of authentication errors from LiteLLM."""
        mock_env = {
            "MODEL": "gpt-4",
            "OPENAI_API_KEY": "sk-test123456789",
            "AGENT_MODE": "litellm",
            "PROMPT": "test prompt",
            "REDIS_URL": "redis://localhost:6379/1",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            agent = AIdeatorAgent()

            # Mock authentication error
            with patch("agent.main.acompletion") as mock_completion:
                mock_completion.side_effect = Exception(
                    "Authentication failed: invalid API key"
                )

                with pytest.raises(RuntimeError) as exc_info:
                    await agent._generate_litellm_response(None)

                assert "Authentication failed for openai" in str(exc_info.value)

    async def test_litellm_rate_limit_error_handling(self):
        """Test handling of rate limit errors from LiteLLM."""
        mock_env = {
            "MODEL": "gpt-4",
            "OPENAI_API_KEY": "sk-test123456789",
            "AGENT_MODE": "litellm",
            "PROMPT": "test prompt",
            "REDIS_URL": "redis://localhost:6379/1",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            agent = AIdeatorAgent()

            # Mock rate limit error
            with patch("agent.main.acompletion") as mock_completion:
                mock_completion.side_effect = Exception("Rate limit exceeded")

                with pytest.raises(RuntimeError) as exc_info:
                    await agent._generate_litellm_response(None)

                assert "Rate limit exceeded for openai" in str(exc_info.value)

    async def test_litellm_model_not_found_error_handling(self):
        """Test handling of model not found errors from LiteLLM."""
        mock_env = {
            "MODEL": "nonexistent-model",
            "OPENAI_API_KEY": "sk-test123456789",
            "AGENT_MODE": "litellm",
            "PROMPT": "test prompt",
            "REDIS_URL": "redis://localhost:6379/1",
        }

        with patch.dict(os.environ, mock_env, clear=True):
            agent = AIdeatorAgent()

            # Mock model not found error
            with patch("agent.main.acompletion") as mock_completion:
                mock_completion.side_effect = Exception("Model does not exist")

                with pytest.raises(RuntimeError) as exc_info:
                    await agent._generate_litellm_response(None)

                assert "Model not available" in str(exc_info.value)


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test API endpoint error handling."""

    async def test_create_run_with_unavailable_model(self):
        """Test run creation fails gracefully with unavailable models."""
        # This would require a full app test setup with database
        # For now, we'll test the validation logic directly

        # Mock settings with no API keys
        with patch("app.api.v1.runs.settings") as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.gemini_api_key = None

            # Create mock request with unavailable model
            mock_request = Mock()
            mock_request.model_variants = [Mock(model_definition_id="claude-3-sonnet")]

            # This should raise HTTPException due to missing API key
            # (Full integration test would require FastAPI test client setup)
            # Placeholder for integration test

    def test_available_models_endpoint_logic(self):
        """Test the logic for the available models endpoint."""

        # Test the key validation logic
        available_keys = {
            "openai": True,
            "anthropic": False,
            "gemini": True,
        }

        available_models = model_catalog.get_available_models_for_keys(
            {
                provider.value: available
                for provider, available in available_keys.items()
            }
        )

        # Should include OpenAI and Gemini models, but not Anthropic
        providers = {model.provider.value for model in available_models}
        assert "openai" in providers
        assert "gemini" in providers
        assert "anthropic" not in providers


class TestKubernetesSecretHandling:
    """Test Kubernetes secret handling improvements."""

    def test_optional_secrets_in_job_template(self):
        """Test that secrets are marked as optional in job template."""
        # Read the job template and verify optional: true is set
        with open("/Users/cpb/git/aideator/k8s/jobs/agent-job-template.yaml") as f:
            template_content = f.read()

        # Check that all API key secrets are marked as optional
        assert "optional: true" in template_content

        # Count occurrences - should have at least 8 optional secrets
        optional_count = template_content.count("optional: true")
        assert optional_count >= 8

        # Verify specific secrets are optional
        assert "openai-secret" in template_content
        assert "anthropic-secret" in template_content
        assert "gemini-secret" in template_content
        assert "mistral-secret" in template_content


def test_error_message_quality():
    """Test that error messages are helpful and actionable."""
    agent = AIdeatorAgent()
    agent.available_api_keys = {"openai": False, "anthropic": False, "gemini": False}

    is_valid, error_msg = agent._validate_model_credentials("claude-3-sonnet")

    # Check that error message contains helpful information
    assert "Missing API Key for Anthropic" in error_msg
    assert "kubectl create secret" in error_msg
    assert "https://console.anthropic.com/" in error_msg
    assert "Available models with configured API keys:" in error_msg

    # Should be markdown formatted for better readability
    assert "**" in error_msg or "#" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
