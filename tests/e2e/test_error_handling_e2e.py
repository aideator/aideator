"""
End-to-end tests for error handling user journeys.
Tests the complete flow from frontend request to backend error response.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from httpx import AsyncClient
except ImportError:
    AsyncClient = None

try:
    from playwright.async_api import Browser, Page, async_playwright
except ImportError:
    # Playwright not available - skip these tests
    Page = None
    Browser = None


@pytest.mark.asyncio
class TestErrorHandlingE2E:
    """End-to-end tests for error handling scenarios."""

    @pytest.fixture(scope="class")
    async def browser(self):
        """Setup browser for E2E tests."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        yield browser
        await browser.close()
        await playwright.stop()

    @pytest.fixture
    async def page(self, browser: Browser):
        """Create a new page for each test."""
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    async def test_missing_api_key_error_flow(self):
        """Test complete flow when API key is missing."""

        # Test via API directly (simulating frontend call)
        async with AsyncClient(base_url="http://localhost:8000") as client:
            # Create run request with model requiring missing API key
            run_request = {
                "github_url": "https://github.com/octocat/Hello-World",
                "prompt": "Analyze this repository",
                "model_variants": [
                    {"model_definition_id": "claude-3-sonnet"}
                ],
                "agent_mode": "litellm"
            }

            response = await client.post(
                "/api/v1/runs",
                json=run_request,
                headers={"X-API-Key": "test-api-key"}
            )

            # Should get 400 with helpful error
            assert response.status_code == 400
            error_data = response.json()["detail"]

            # Verify error structure
            assert "message" in error_data
            assert "unavailable_models" in error_data
            assert "available_models" in error_data
            assert "suggestion" in error_data

            # Verify helpful content
            assert "claude-3-sonnet" in str(error_data["unavailable_models"])
            assert "missing API keys" in error_data["message"].lower()
            assert len(error_data["suggestion"]) > 0

    async def test_available_models_api_flow(self):
        """Test the available models endpoint flow."""

        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(
                "/api/v1/models/available",
                headers={"Authorization": "Bearer test-token"}
            )

            # Should succeed even with no API keys
            assert response.status_code == 200
            data = response.json()

            # Should have expected structure
            assert "models" in data
            assert "providers" in data
            assert "total_models" in data
            assert "available_providers" in data

            # Models should only include those with available API keys
            models = data["models"]
            for model in models:
                if model["requires_api_key"]:
                    # This model should have corresponding provider with credentials
                    provider = model["provider"]
                    provider_data = next(
                        (p for p in data["providers"] if p["provider"] == provider),
                        None
                    )
                    assert provider_data is not None

    async def test_agent_error_handling_simulation(self):
        """Test agent-level error handling by simulating container environment."""

        # Simulate agent container environment with missing API key
        test_env = {
            "MODEL": "claude-3-sonnet",
            "PROMPT": "Test prompt",
            "RUN_ID": "test-run",
            "VARIATION_ID": "0",
            "AGENT_MODE": "litellm",
            # Missing ANTHROPIC_API_KEY
        }

        # Import and run agent logic
        from agent.main import AIdeatorAgent

        with pytest.raises(RuntimeError) as exc_info:
            # Simulate environment
            with patch.dict(os.environ, test_env, clear=True):
                agent = AIdeatorAgent()
                await agent.run()

        # Should get helpful error message
        error_msg = str(exc_info.value)
        assert "Missing API key" in error_msg

    async def test_model_validation_flow(self):
        """Test model validation across the entire stack."""

        from app.services.model_catalog import model_catalog

        # Test with no API keys
        available_keys = {
            "openai": False,
            "anthropic": False,
            "gemini": False,
            "mistral": False,
        }

        # Should reject models requiring API keys
        is_valid, error = model_catalog.validate_model_access("gpt-4", available_keys)
        assert not is_valid
        assert "API key" in error

        # Should accept models that don't require API keys
        no_key_models = model_catalog.get_models_without_api_key()
        if no_key_models:
            model = no_key_models[0]
            is_valid, error = model_catalog.validate_model_access(
                model.model_name, available_keys
            )
            assert is_valid

    async def test_error_message_quality_e2e(self):
        """Test that error messages meet quality standards."""

        async with AsyncClient(base_url="http://localhost:8000") as client:
            # Test with completely unavailable model
            run_request = {
                "github_url": "https://github.com/octocat/Hello-World",
                "prompt": "Test prompt",
                "model_variants": [
                    {"model_definition_id": "claude-3-sonnet"},
                    {"model_definition_id": "gpt-4"},
                    {"model_definition_id": "gemini-1.5-pro"}
                ],
                "agent_mode": "litellm"
            }

            response = await client.post(
                "/api/v1/runs",
                json=run_request,
                headers={"X-API-Key": "test-key"}
            )

            if response.status_code == 400:
                error_detail = response.json()["detail"]

                # Error message quality checks
                assert len(error_detail["message"]) > 10  # Substantial message
                assert "suggestion" in error_detail
                assert len(error_detail["suggestion"]) > 20  # Helpful suggestion

                # Should provide actionable guidance
                suggestion = error_detail["suggestion"].lower()
                assert any(word in suggestion for word in [
                    "try", "use", "available", "configure", "add"
                ])


class TestErrorRecoveryE2E:
    """Test error recovery scenarios."""

    async def test_partial_model_availability_recovery(self):
        """Test system behavior when some models work and others don't."""

        # Simulate scenario where OpenAI works but Anthropic doesn't
        async with AsyncClient(base_url="http://localhost:8000") as client:
            # First, try mixed request (should fail)
            mixed_request = {
                "github_url": "https://github.com/octocat/Hello-World",
                "prompt": "Test prompt",
                "model_variants": [
                    {"model_definition_id": "gpt-4"},  # Might work
                    {"model_definition_id": "claude-3-sonnet"}  # Likely doesn't work
                ],
                "agent_mode": "litellm"
            }

            response = await client.post(
                "/api/v1/runs",
                json=mixed_request,
                headers={"X-API-Key": "test-key"}
            )

            if response.status_code == 400:
                error_detail = response.json()["detail"]
                available_models = error_detail.get("available_models", [])

                # If there are available models, try using one
                if available_models:
                    recovery_request = {
                        "github_url": "https://github.com/octocat/Hello-World",
                        "prompt": "Test prompt",
                        "model_variants": [
                            {"model_definition_id": available_models[0]}
                        ],
                        "agent_mode": "litellm"
                    }

                    recovery_response = await client.post(
                        "/api/v1/runs",
                        json=recovery_request,
                        headers={"X-API-Key": "test-key"}
                    )

                    # This should succeed (or fail for different reason)
                    # Note: May still fail due to other issues, but not model availability
                    assert recovery_response.status_code != 400 or \
                           "missing API keys" not in recovery_response.json().get("detail", {}).get("message", "").lower()


class TestUserJourneyE2E:
    """Test complete user journeys with error handling."""

    async def test_new_user_no_api_keys_journey(self):
        """Test journey for new user with no API keys configured."""

        async with AsyncClient(base_url="http://localhost:8000") as client:
            # 1. User tries to see available models
            models_response = await client.get(
                "/api/v1/models/available",
                headers={"Authorization": "Bearer test-token"}
            )

            assert models_response.status_code == 200
            models_data = models_response.json()

            # Should get minimal model list (only no-key-required models)
            available_models = models_data["models"]

            # 2. User tries to create run (should fail gracefully)
            if available_models:
                # Try with available model
                run_request = {
                    "github_url": "https://github.com/octocat/Hello-World",
                    "prompt": "Analyze this code",
                    "model_variants": [
                        {"model_definition_id": available_models[0]["model_name"]}
                    ],
                    "agent_mode": "litellm"
                }
            else:
                # Try with common model (should fail)
                run_request = {
                    "github_url": "https://github.com/octocat/Hello-World",
                    "prompt": "Analyze this code",
                    "model_variants": [
                        {"model_definition_id": "gpt-4"}
                    ],
                    "agent_mode": "litellm"
                }

            run_response = await client.post(
                "/api/v1/runs",
                json=run_request,
                headers={"X-API-Key": "test-key"}
            )

            # Should either succeed (if no-key model available) or fail gracefully
            if run_response.status_code == 400:
                error_detail = run_response.json()["detail"]
                assert "suggestion" in error_detail
                assert len(error_detail["suggestion"]) > 0
            else:
                # If it succeeded, should have created a valid run
                assert run_response.status_code == 202
                run_data = run_response.json()
                assert "run_id" in run_data
                assert "stream_url" in run_data


if __name__ == "__main__":
    # Run E2E tests
    import sys
    sys.path.append("/Users/cpb/git/aideator")

    pytest.main([__file__, "-v", "--tb=short"])
