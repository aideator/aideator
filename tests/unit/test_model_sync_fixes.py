"""
Tests for model sync service fixes - covering the changes made to resolve model discovery issues.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.model_definition import ModelDefinitionDB, ModelSyncLog
from app.services.model_sync_service import ModelSyncService


class TestModelSyncServiceFixes:
    """Test the fixes made to model sync service."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = MagicMock()
        session.exec.return_value.first.return_value = None  # No existing models
        session.exec.return_value.all.return_value = []  # No existing models
        session.commit = MagicMock()
        session.rollback = MagicMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def sample_model_data(self):
        """Sample model data from LiteLLM proxy."""
        return {
            "model_name": "gpt-4",
            "model_info": {
                "litellm_provider": "openai",
                "max_tokens": None,  # This was causing the comparison error
                "max_input_tokens": 4096,
                "max_output_tokens": 4096,
                "input_cost_per_token": 0.00003,
                "output_cost_per_token": 0.00006,
                "supports_function_calling": True,
                "supports_vision": None,  # This was causing null constraint error
                "supports_streaming": True,
            },
        }

    @pytest.fixture
    def service(self):
        """Model sync service instance."""
        with patch("app.services.model_sync_service.get_settings") as mock_settings:
            mock_settings.return_value.LITELLM_PROXY_URL = "http://localhost:4000"
            mock_settings.return_value.LITELLM_MASTER_KEY = "sk-1234"
            return ModelSyncService()

    def test_configuration_uses_master_key(self, service):
        """Test that service now uses LITELLM_MASTER_KEY instead of LITELLM_PROXY_API_KEY."""
        assert service.proxy_api_key == "sk-1234"
        assert service.proxy_base_url == "http://localhost:4000"

    def test_generate_description_handles_none_max_tokens(self, service):
        """Test that _generate_description handles None max_tokens without error."""
        model_info = {"max_tokens": None}

        # This should not raise a TypeError anymore
        description = service._generate_description("test-model", model_info)
        assert description == "General purpose language model"

        # Test with actual value
        model_info["max_tokens"] = 150000
        description = service._generate_description("test-model", model_info)
        assert description == "Large context window model"

    def test_process_model_handles_none_values(
        self, service, mock_session, sample_model_data
    ):
        """Test that _process_model properly handles None values for boolean fields."""
        sync_log = ModelSyncLog()

        # This should not raise a null constraint violation
        import asyncio

        asyncio.run(service._process_model(mock_session, sample_model_data, sync_log))

        # Verify model was added
        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]

        # Check that None values were converted to defaults
        assert added_model.supports_vision is False  # None -> False
        assert added_model.supports_function_calling is True  # True preserved
        assert added_model.supports_streaming is True  # True preserved
        assert added_model.provider == "openai"  # Provider field is set
        assert added_model.litellm_model_name == "gpt-4"  # litellm_model_name is set

    def test_process_model_updates_existing_with_none_handling(
        self, service, mock_session, sample_model_data
    ):
        """Test that updating existing models handles None values correctly."""
        # Setup existing model
        existing_model = ModelDefinitionDB(
            model_name="gpt-4",
            provider="openai",
            litellm_provider="openai",
            litellm_model_name="gpt-4",
            display_name="GPT-4",
            supports_vision=True,  # Will be updated to False due to None
            supports_function_calling=False,  # Will be updated to True
            supports_streaming=True,
        )
        mock_session.exec.return_value.first.return_value = existing_model

        sync_log = ModelSyncLog()

        import asyncio

        asyncio.run(service._process_model(mock_session, sample_model_data, sync_log))

        # Check that boolean fields were updated correctly, handling None values
        assert existing_model.supports_vision is False  # None converted to False
        assert existing_model.supports_function_calling is True  # True preserved
        assert existing_model.supports_streaming is True  # True preserved
        assert existing_model.provider == "openai"  # Provider updated
        assert sync_log.models_updated == 1

    @patch("app.services.model_sync_service.httpx.AsyncClient")
    def test_fetch_models_uses_master_key_auth(self, mock_client, service):
        """Test that model fetching uses the master key for authentication."""
        # Mock the /v1/models response
        models_response = MagicMock()
        models_response.json.return_value = {"data": [{"id": "gpt-4"}]}
        models_response.raise_for_status = MagicMock()

        # Mock the /v1/model/info response
        info_response = MagicMock()
        info_response.json.return_value = {
            "data": [{"model_name": "gpt-4", "litellm_provider": "openai"}]
        }
        info_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        # Return different responses for different URLs
        mock_client_instance.get.side_effect = [models_response, info_response]
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        import asyncio

        result = asyncio.run(service._fetch_models_from_proxy())

        # Verify requests were made with correct authentication
        calls = mock_client_instance.get.call_args_list
        assert len(calls) == 2  # Two API calls made

        # Check that Authorization header is set correctly
        for call in calls:
            headers = call[1]["headers"]
            assert headers["Authorization"] == "Bearer sk-1234"

        # Verify the result includes merged data
        assert len(result) == 1
        assert result[0]["model_name"] == "gpt-4"

    def test_sync_models_is_idempotent(self, service, mock_session):
        """Test that sync operation handles duplicate key errors gracefully."""
        sync_log = ModelSyncLog()
        mock_session.add(sync_log)
        mock_session.commit.return_value = None

        # Mock _fetch_models_from_proxy to return sample data
        sample_models = [
            {"model_name": "gpt-4", "model_info": {"litellm_provider": "openai"}},
            {"model_name": "claude-3", "model_info": {"litellm_provider": "anthropic"}},
        ]

        with patch.object(
            service, "_fetch_models_from_proxy", return_value=sample_models
        ):
            with patch.object(service, "_process_model") as mock_process:
                with patch.object(service, "_deactivate_missing_models"):
                    # Simulate unique constraint violation on second model
                    def side_effect(session, model_data, sync_log):
                        if model_data["model_name"] == "claude-3":
                            # Simulate a database unique constraint violation
                            raise Exception(
                                "duplicate key value violates unique constraint"
                            )

                    mock_process.side_effect = side_effect

                    # This should complete successfully despite the constraint violation
                    import asyncio

                    result = asyncio.run(service.sync_models(mock_session))

                    # Operation should succeed overall
                    assert result.status == "success"
                    assert (
                        mock_session.rollback.called
                    )  # Rollback was called for the duplicate

    def test_provider_field_is_set_correctly(
        self, service, mock_session, sample_model_data
    ):
        """Test that both provider and litellm_provider fields are set correctly."""
        sync_log = ModelSyncLog()

        import asyncio

        asyncio.run(service._process_model(mock_session, sample_model_data, sync_log))

        added_model = mock_session.add.call_args[0][0]

        # Both provider fields should be set to the same value
        assert added_model.provider == "openai"
        assert added_model.litellm_provider == "openai"
        assert added_model.litellm_model_name == "gpt-4"
