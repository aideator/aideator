"""
Integration tests for error handling in API endpoints.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
class TestRunCreationErrorHandling:
    """Test run creation with missing API keys."""

    async def test_create_run_missing_api_keys(self):
        """Test that run creation fails gracefully when API keys are missing."""

        # Mock settings with no API keys
        with patch("app.api.v1.runs.settings") as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.gemini_api_key = None

            async with AsyncClient(app=app, base_url="http://test") as client:
                # Create a run request with models that require API keys
                run_request = {
                    "github_url": "https://github.com/test/repo",
                    "prompt": "Test prompt",
                    "model_variants": [
                        {"model_definition_id": "claude-3-sonnet"},
                        {"model_definition_id": "gpt-4"}
                    ],
                    "agent_mode": "litellm"
                }

                # This should fail with helpful error message
                response = await client.post(
                    "/api/v1/runs",
                    json=run_request,
                    headers={"X-API-Key": "test-key"}
                )

                assert response.status_code == 400
                error_detail = response.json()["detail"]

                assert "missing API keys" in error_detail["message"].lower()
                assert "unavailable_models" in error_detail
                assert "available_models" in error_detail
                assert "suggestion" in error_detail

    async def test_create_run_partial_api_keys(self):
        """Test run creation when some but not all API keys are available."""

        # Mock settings with only OpenAI key
        with patch("app.api.v1.runs.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test123456789"
            mock_settings.anthropic_api_key = None
            mock_settings.gemini_api_key = None

            async with AsyncClient(app=app, base_url="http://test") as client:
                # Request both available and unavailable models
                run_request = {
                    "github_url": "https://github.com/test/repo",
                    "prompt": "Test prompt",
                    "model_variants": [
                        {"model_definition_id": "gpt-4"},  # Available
                        {"model_definition_id": "claude-3-sonnet"}  # Not available
                    ],
                    "agent_mode": "litellm"
                }

                response = await client.post(
                    "/api/v1/runs",
                    json=run_request,
                    headers={"X-API-Key": "test-key"}
                )

                assert response.status_code == 400
                error_detail = response.json()["detail"]

                # Should mention only claude-3-sonnet as unavailable
                unavailable_models = error_detail["unavailable_models"]
                assert len(unavailable_models) == 1
                assert unavailable_models[0]["model"] == "claude-3-sonnet"

                # Should suggest gpt-4 and other OpenAI models as available
                available_models = error_detail["available_models"]
                assert "gpt-4" in available_models or "gpt-4o" in available_models


@pytest.mark.asyncio
class TestModelsEndpointErrorHandling:
    """Test models endpoint error handling."""

    async def test_available_models_endpoint(self):
        """Test the /api/v1/models/available endpoint."""

        # Mock settings with specific API keys
        with patch("app.api.v1.models.settings") as mock_settings:
            mock_settings.openai_api_key = "sk-test123456789"
            mock_settings.anthropic_api_key = None
            mock_settings.gemini_api_key = "AIzatest123456789"

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/models/available",
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()

                # Should only include models from providers with API keys
                models = data["models"]
                providers = data["providers"]

                # Check that only OpenAI and Gemini providers are included
                provider_names = [p["provider"] for p in providers]
                assert "openai" in provider_names
                assert "gemini" in provider_names
                assert "anthropic" not in provider_names

                # Check that models match available providers
                model_providers = set(m["provider"] for m in models)
                assert "openai" in model_providers
                assert "gemini" in model_providers
                assert "anthropic" not in model_providers

    async def test_model_catalog_with_no_keys(self):
        """Test model catalog when no API keys are configured."""

        with patch("app.api.v1.models.settings") as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.gemini_api_key = None

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/models/available",
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()

                # Should return empty or only no-key-required models
                models = data["models"]
                providers = data["providers"]

                # All returned models should not require API keys
                for model in models:
                    assert model["requires_api_key"] is False


@pytest.mark.asyncio
class TestStreamingErrorHandling:
    """Test streaming endpoint error handling."""

    async def test_stream_with_missing_run(self):
        """Test streaming for non-existent run."""

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/runs/nonexistent-run/stream",
                headers={"X-API-Key": "test-key"}
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


def test_kubernetes_template_has_optional_secrets():
    """Test that Kubernetes job template has optional secrets."""

    template_path = "/Users/cpb/git/aideator/k8s/jobs/agent-job-template.yaml"

    with open(template_path) as f:
        template_content = f.read()

    # Verify that secrets are marked as optional
    lines = template_content.split("\n")
    secret_ref_lines = [i for i, line in enumerate(lines) if "secretKeyRef:" in line]

    for secret_line_idx in secret_ref_lines:
        # Look for "optional: true" within the next few lines
        found_optional = False
        for j in range(secret_line_idx + 1, min(secret_line_idx + 5, len(lines))):
            if "optional: true" in lines[j]:
                found_optional = True
                break

        # Get the secret name for better error message
        secret_name = "unknown"
        for k in range(max(0, secret_line_idx - 3), secret_line_idx):
            if "name:" in lines[k] and "API_KEY" in lines[k]:
                secret_name = lines[k].strip()
                break

        assert found_optional, f"Secret {secret_name} should be marked as optional"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
