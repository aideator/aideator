"""
Test model sync service functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlmodel import Session

from app.models.model_definition import ModelDefinitionDB
from app.services.model_sync_service import ModelSyncService


class TestModelSyncService:
    """Test cases for model sync service."""

    @pytest.fixture
    def sync_service(self):
        """Create model sync service instance."""
        return ModelSyncService()

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.exec = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def mock_litellm_response(self):
        """Mock response from LiteLLM proxy."""
        return {
            "models": {
                "data": [
                    {"id": "gpt-4", "object": "model"},
                    {"id": "claude-3-opus-20240229", "object": "model"},
                    {"id": "gemini-pro", "object": "model"},
                ]
            },
            "model_info": {
                "data": [
                    {
                        "model_name": "gpt-4",
                        "litellm_params": {"model": "gpt-4"},
                        "model_info": {
                            "litellm_provider": "openai",
                            "max_tokens": 8192,
                            "max_input_tokens": 8192,
                            "max_output_tokens": 4096,
                            "input_cost_per_token": 0.00003,
                            "output_cost_per_token": 0.00006,
                            "supports_function_calling": True,
                            "supports_vision": False,
                            "supports_streaming": True,
                        },
                    },
                    {
                        "model_name": "claude-3-opus-20240229",
                        "litellm_params": {"model": "claude-3-opus-20240229"},
                        "model_info": {
                            "litellm_provider": "anthropic",
                            "max_tokens": 200000,
                            "max_input_tokens": 200000,
                            "max_output_tokens": 4096,
                            "input_cost_per_token": 0.000015,
                            "output_cost_per_token": 0.000075,
                            "supports_function_calling": True,
                            "supports_vision": True,
                            "supports_streaming": True,
                        },
                    },
                    {
                        "model_name": "gemini-pro",
                        "litellm_params": {"model": "gemini-pro"},
                        "model_info": {},
                    },
                ]
            },
        }

    @pytest.mark.asyncio
    async def test_fetch_models_from_proxy(self, sync_service, mock_litellm_response):
        """Test fetching models from LiteLLM proxy."""
        with patch("httpx.AsyncClient") as mock_client:
            # Setup mock responses
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock the two API calls
            mock_instance.get = AsyncMock(
                side_effect=[
                    Mock(
                        json=Mock(return_value=mock_litellm_response["models"]),
                        raise_for_status=Mock(),
                    ),
                    Mock(
                        json=Mock(return_value=mock_litellm_response["model_info"]),
                        raise_for_status=Mock(),
                    ),
                ]
            )

            # Call the method
            models = await sync_service._fetch_models_from_proxy()

            # Verify API calls were made
            assert mock_instance.get.call_count == 2

            # The method merges models from both endpoints
            # It should have the 2 from model_info plus gemini-pro from models
            assert len(models) == 3
            model_names = {m["model_name"] for m in models}
            assert model_names == {"gpt-4", "claude-3-opus-20240229", "gemini-pro"}

    @pytest.mark.asyncio
    async def test_sync_models_success(
        self, sync_service, mock_session, mock_litellm_response
    ):
        """Test successful model sync."""
        # Mock the fetch method
        sync_service._fetch_models_from_proxy = AsyncMock(
            return_value=mock_litellm_response["model_info"]["data"]
        )

        # Mock existing models query
        mock_session.exec.return_value.first.return_value = None  # No existing models
        mock_session.exec.return_value.all.return_value = []  # No active models

        # Run sync
        sync_log = await sync_service.sync_models(mock_session)

        # Verify sync log
        assert sync_log.status == "success"
        assert sync_log.models_discovered == 3
        assert sync_log.models_added == 3
        assert sync_log.completed_at is not None

    @pytest.mark.asyncio
    async def test_sync_models_update_existing(
        self, sync_service, mock_session, mock_litellm_response
    ):
        """Test updating existing models."""
        # Mock the fetch method
        sync_service._fetch_models_from_proxy = AsyncMock(
            return_value=mock_litellm_response["model_info"]["data"][:1]  # Just GPT-4
        )

        # Mock existing model
        existing_model = ModelDefinitionDB(
            model_name="gpt-4",
            litellm_provider="openai",
            display_name="GPT-4",
            is_active=True,
            last_seen_at=datetime.utcnow(),
        )
        mock_session.exec.return_value.first.return_value = existing_model
        mock_session.exec.return_value.all.return_value = [existing_model]

        # Run sync
        sync_log = await sync_service.sync_models(mock_session)

        # Verify
        assert sync_log.models_updated == 1
        assert sync_log.models_added == 0
        assert existing_model.is_active is True

    @pytest.mark.asyncio
    async def test_sync_models_deactivate_missing(self, sync_service, mock_session):
        """Test deactivating models not in current sync."""
        # Mock empty response from proxy
        sync_service._fetch_models_from_proxy = AsyncMock(return_value=[])

        # Mock existing active models
        existing_models = [
            ModelDefinitionDB(
                model_name="gpt-4",
                litellm_provider="openai",
                display_name="GPT-4",
                is_active=True,
            ),
            ModelDefinitionDB(
                model_name="claude-3",
                litellm_provider="anthropic",
                display_name="Claude 3",
                is_active=True,
            ),
        ]
        mock_session.exec.return_value.first.return_value = None
        mock_session.exec.return_value.all.return_value = existing_models

        # Run sync
        sync_log = await sync_service.sync_models(mock_session)

        # Verify models were deactivated
        assert sync_log.models_deactivated == 2
        assert all(model.is_active is False for model in existing_models)

    @pytest.mark.asyncio
    async def test_sync_models_error_handling(self, sync_service, mock_session):
        """Test error handling during sync."""
        # Mock fetch to raise error
        sync_service._fetch_models_from_proxy = AsyncMock(
            side_effect=Exception("Connection error")
        )

        # Run sync
        sync_log = await sync_service.sync_models(mock_session)

        # Verify error was handled
        assert sync_log.status == "failed"
        assert "Connection error" in sync_log.error_message
        assert sync_log.completed_at is not None

    def test_generate_display_name(self, sync_service):
        """Test display name generation."""
        test_cases = [
            ("gpt-4", "GPT 4"),
            ("claude-3-opus", "Claude 3 Opus"),
            ("gemini-pro", "Gemini Pro"),
            ("text-embedding-ada", "Text Embedding Ada"),
            ("openai/gpt-4", "GPT 4"),  # Remove prefix
        ]

        for model_name, expected in test_cases:
            assert sync_service._generate_display_name(model_name) == expected

    def test_generate_description(self, sync_service):
        """Test description generation."""
        # Test known models
        assert "most capable" in sync_service._generate_description("gpt-4", {})
        assert "Anthropic" in sync_service._generate_description("claude-3-opus", {})

        # Test vision model
        model_info = {"supports_vision": True}
        assert "vision" in sync_service._generate_description("unknown", model_info)

        # Test embedding model
        assert "Embedding" in sync_service._generate_description(
            "text-embedding-ada", {}
        )

        # Test large context model
        model_info = {"max_tokens": 150000}
        assert "Large context" in sync_service._generate_description(
            "unknown", model_info
        )

    def test_determine_category(self, sync_service):
        """Test category determination."""
        assert sync_service._determine_category("text-embedding-ada", {}) == "embedding"
        assert sync_service._determine_category("gpt-4", {}) == "advanced"
        assert sync_service._determine_category("code-llama", {}) == "code"
        assert (
            sync_service._determine_category("unknown", {"supports_vision": True})
            == "vision"
        )
        assert sync_service._determine_category("gpt-3.5-turbo", {}) == "general"

    def test_generate_tags(self, sync_service):
        """Test tag generation."""
        model_info = {
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_streaming": True,
            "max_tokens": 150000,
        }

        tags = sync_service._generate_tags("gpt-4", model_info)

        assert "functions" in tags
        assert "vision" in tags
        assert "streaming" in tags
        assert "large-context" in tags
        assert "powerful" in tags

    def test_is_recommended(self, sync_service):
        """Test recommendation logic."""
        assert sync_service._is_recommended("gpt-4") is True
        assert sync_service._is_recommended("gpt-4o") is True
        assert sync_service._is_recommended("claude-3-opus") is True
        assert sync_service._is_recommended("random-model") is False

    def test_requires_api_key(self, sync_service):
        """Test API key requirement logic."""
        assert sync_service._requires_api_key({"litellm_provider": "openai"}) is True
        assert sync_service._requires_api_key({"litellm_provider": "ollama"}) is False
        assert sync_service._requires_api_key({"litellm_provider": "local"}) is False
        assert sync_service._requires_api_key({}) is True  # Default to required

    def test_get_api_key_env_var(self, sync_service):
        """Test API key environment variable mapping."""
        assert (
            sync_service._get_api_key_env_var({"litellm_provider": "openai"})
            == "OPENAI_API_KEY"
        )
        assert (
            sync_service._get_api_key_env_var({"litellm_provider": "anthropic"})
            == "ANTHROPIC_API_KEY"
        )
        assert (
            sync_service._get_api_key_env_var({"litellm_provider": "unknown"}) is None
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
