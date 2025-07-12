"""Tests for the models API endpoints."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.models import router
from app.models.provider import ModelCapability, ProviderCredential, ProviderType
from app.models.user import User
from app.schemas.models import (
    ModelCatalogResponse,
    ModelDefinitionResponse,
    ModelRecommendation,
    ModelRecommendationRequest,
    ModelRecommendationResponse,
    ProviderSummary,
)


class TestModelsAPI:
    """Test the models API endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = "user_123"
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_model_catalog(self):
        """Create a mock model catalog."""
        mock_catalog = Mock()

        # Create mock model definitions
        mock_model_1 = Mock()
        mock_model_1.provider = ProviderType.OPENAI
        mock_model_1.model_name = "gpt-4"
        mock_model_1.litellm_model_name = "openai/gpt-4"
        mock_model_1.display_name = "GPT-4"
        mock_model_1.description = "Most capable GPT-4 model"
        mock_model_1.context_window = 8000
        mock_model_1.max_output_tokens = 4000
        mock_model_1.input_price_per_1m_tokens = 30.0
        mock_model_1.output_price_per_1m_tokens = 60.0
        mock_model_1.capabilities = [
            ModelCapability.CHAT_COMPLETION,
            ModelCapability.FUNCTION_CALLING,
        ]
        mock_model_1.requires_api_key = True
        mock_model_1.requires_region = False
        mock_model_1.requires_project_id = False

        mock_model_2 = Mock()
        mock_model_2.provider = ProviderType.ANTHROPIC
        mock_model_2.model_name = "claude-3-opus"
        mock_model_2.litellm_model_name = "anthropic/claude-3-opus"
        mock_model_2.display_name = "Claude 3 Opus"
        mock_model_2.description = "Most capable Claude model"
        mock_model_2.context_window = 200000
        mock_model_2.max_output_tokens = 4000
        mock_model_2.input_price_per_1m_tokens = 15.0
        mock_model_2.output_price_per_1m_tokens = 75.0
        mock_model_2.capabilities = [ModelCapability.CHAT_COMPLETION]
        mock_model_2.requires_api_key = True
        mock_model_2.requires_region = False
        mock_model_2.requires_project_id = False

        mock_model_3 = Mock()
        mock_model_3.provider = ProviderType.OLLAMA
        mock_model_3.model_name = "llama2"
        mock_model_3.litellm_model_name = "ollama/llama2"
        mock_model_3.display_name = "Llama 2"
        mock_model_3.description = "Open source model"
        mock_model_3.context_window = 4000
        mock_model_3.max_output_tokens = 2000
        mock_model_3.input_price_per_1m_tokens = 0.0
        mock_model_3.output_price_per_1m_tokens = 0.0
        mock_model_3.capabilities = [ModelCapability.CHAT_COMPLETION]
        mock_model_3.requires_api_key = False
        mock_model_3.requires_region = False
        mock_model_3.requires_project_id = False

        mock_catalog.get_all_models.return_value = [
            mock_model_1,
            mock_model_2,
            mock_model_3,
        ]
        mock_catalog.get_models_by_provider.return_value = [mock_model_1]
        mock_catalog.get_providers.return_value = [
            ProviderType.OPENAI,
            ProviderType.ANTHROPIC,
            ProviderType.OLLAMA,
        ]
        mock_catalog.get_capabilities.return_value = [
            ModelCapability.CHAT_COMPLETION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.TEXT_COMPLETION,
        ]

        return mock_catalog

    @pytest.fixture
    def mock_provider_credentials(self):
        """Create mock provider credentials."""
        cred1 = Mock(spec=ProviderCredential)
        cred1.provider = ProviderType.OPENAI
        cred1.is_active = True

        cred2 = Mock(spec=ProviderCredential)
        cred2.provider = ProviderType.ANTHROPIC
        cred2.is_active = True

        return [cred1, cred2]

    @pytest.mark.asyncio
    async def test_get_model_catalog_success(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test successful model catalog retrieval."""
        from app.api.v1.models import get_model_catalog

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_catalog(
                provider=None,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelCatalogResponse)
        assert len(response.models) == 3
        assert len(response.providers) == 3
        assert response.capabilities == [
            ModelCapability.CHAT_COMPLETION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.TEXT_COMPLETION,
        ]

        # Check that providers include user credential status
        openai_provider = next(
            p for p in response.providers if p.provider == ProviderType.OPENAI
        )
        assert openai_provider.user_has_credentials is True

        ollama_provider = next(
            p for p in response.providers if p.provider == ProviderType.OLLAMA
        )
        assert ollama_provider.user_has_credentials is False

    @pytest.mark.asyncio
    async def test_get_model_catalog_with_provider_filter(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test model catalog retrieval with provider filter."""
        from app.api.v1.models import get_model_catalog

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_catalog(
                provider=ProviderType.OPENAI,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelCatalogResponse)
        # Should only return OpenAI models
        assert all(model.provider == ProviderType.OPENAI for model in response.models)

    @pytest.mark.asyncio
    async def test_get_model_catalog_with_capability_filter(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test model catalog retrieval with capability filter."""
        from app.api.v1.models import get_model_catalog

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_catalog(
                provider=None,
                capability=ModelCapability.FUNCTION_CALLING,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelCatalogResponse)
        # Should only return models with function calling capability
        for model in response.models:
            assert ModelCapability.FUNCTION_CALLING in model.capabilities

    @pytest.mark.asyncio
    async def test_get_model_catalog_with_api_key_filter(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test model catalog retrieval with API key requirement filter."""
        from app.api.v1.models import get_model_catalog

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_catalog(
                provider=None,
                capability=None,
                requires_api_key=False,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelCatalogResponse)
        # Should only return models that don't require API keys
        assert all(not model.requires_api_key for model in response.models)

    @pytest.mark.asyncio
    async def test_get_model_catalog_exception_handling(
        self, mock_user, mock_db_session, mock_model_catalog
    ):
        """Test model catalog exception handling."""
        from app.api.v1.models import get_model_catalog

        # Mock database to raise an exception
        mock_db_session.execute.side_effect = Exception("Database error")

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_model_catalog(
                    provider=None,
                    capability=None,
                    requires_api_key=None,
                    current_user=mock_user,
                    db=mock_db_session,
                )

        assert exc_info.value.status_code == 500
        assert "Failed to get model catalog" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_models_success(self, mock_user, mock_model_catalog):
        """Test successful models retrieval."""
        from app.api.v1.models import get_models

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_models(
                provider=None,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
            )

        assert isinstance(response, list)
        assert len(response) == 3
        assert all(isinstance(model, ModelDefinitionResponse) for model in response)

    @pytest.mark.asyncio
    async def test_get_models_with_filters(self, mock_user, mock_model_catalog):
        """Test models retrieval with filters."""
        from app.api.v1.models import get_models

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_models(
                provider=ProviderType.OPENAI,
                capability=ModelCapability.FUNCTION_CALLING,
                requires_api_key=True,
                current_user=mock_user,
            )

        assert isinstance(response, list)
        # Should filter down to only OpenAI models with function calling that require API keys
        for model in response:
            assert model.provider == ProviderType.OPENAI
            assert ModelCapability.FUNCTION_CALLING in model.capabilities
            assert model.requires_api_key is True

    @pytest.mark.asyncio
    async def test_get_models_exception_handling(self, mock_user, mock_model_catalog):
        """Test models endpoint exception handling."""
        from app.api.v1.models import get_models

        mock_model_catalog.get_all_models.side_effect = Exception("Catalog error")

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_models(
                    provider=None,
                    capability=None,
                    requires_api_key=None,
                    current_user=mock_user,
                )

        assert exc_info.value.status_code == 500
        assert "Failed to get models" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_success(self, mock_user, mock_model_catalog):
        """Test successful individual model retrieval."""
        from app.api.v1.models import get_model

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model(
                model_id="model_gpt_4_openai",
                current_user=mock_user,
            )

        assert isinstance(response, ModelDefinitionResponse)
        assert response.model_name == "gpt-4"
        assert response.provider == ProviderType.OPENAI

    @pytest.mark.asyncio
    async def test_get_model_invalid_id_format(self, mock_user, mock_model_catalog):
        """Test model retrieval with invalid ID format."""
        from app.api.v1.models import get_model

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_model(
                    model_id="invalid_id",
                    current_user=mock_user,
                )

        assert exc_info.value.status_code == 400
        assert "Invalid model ID format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_invalid_provider(self, mock_user, mock_model_catalog):
        """Test model retrieval with invalid provider."""
        from app.api.v1.models import get_model

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_model(
                    model_id="model_gpt_4_invalid_provider",
                    current_user=mock_user,
                )

        assert exc_info.value.status_code == 400
        assert "Invalid provider in model ID" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_not_found(self, mock_user, mock_model_catalog):
        """Test model retrieval when model not found."""
        from app.api.v1.models import get_model

        # Return empty list for get_models_by_provider
        mock_model_catalog.get_models_by_provider.return_value = []

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_model(
                    model_id="model_nonexistent_openai",
                    current_user=mock_user,
                )

        assert exc_info.value.status_code == 404
        assert "Model not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_exception_handling(self, mock_user, mock_model_catalog):
        """Test model endpoint exception handling."""
        from app.api.v1.models import get_model

        mock_model_catalog.get_models_by_provider.side_effect = Exception(
            "Catalog error"
        )

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_model(
                    model_id="model_gpt_4_openai",
                    current_user=mock_user,
                )

        assert exc_info.value.status_code == 500
        assert "Failed to get model" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_recommendations_coding_task(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test model recommendations for coding tasks."""
        from app.api.v1.models import get_model_recommendations

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        request = ModelRecommendationRequest(
            prompt="Write a function to implement a binary search algorithm",
            task_type="coding",
            performance_preference="quality",
            budget_preference="medium",
        )

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_recommendations(
                request=request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelRecommendationResponse)
        assert len(response.recommendations) > 0
        assert isinstance(response.recommendations[0], ModelRecommendation)
        assert (
            "code" in response.explanation.lower()
            or "coding" in response.explanation.lower()
        )

    @pytest.mark.asyncio
    async def test_get_model_recommendations_analysis_task(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test model recommendations for analysis tasks."""
        from app.api.v1.models import get_model_recommendations

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        request = ModelRecommendationRequest(
            prompt="Analyze this large dataset and provide insights",
            performance_preference="quality",
            budget_preference="high",
        )

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_recommendations(
                request=request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelRecommendationResponse)
        assert len(response.recommendations) > 0
        # Should prefer high-context models for analysis
        for rec in response.recommendations:
            assert rec.confidence_score > 0.0

    @pytest.mark.asyncio
    async def test_get_model_recommendations_speed_preference(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test model recommendations with speed preference."""
        from app.api.v1.models import get_model_recommendations

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        request = ModelRecommendationRequest(
            prompt="Write a quick code snippet for string manipulation",
            performance_preference="speed",
            budget_preference="low",
        )

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_recommendations(
                request=request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelRecommendationResponse)
        assert len(response.recommendations) > 0
        assert (
            "speed" in response.explanation.lower()
            or "fast" in response.explanation.lower()
        )

    @pytest.mark.asyncio
    async def test_get_model_recommendations_no_credentials(
        self, mock_user, mock_db_session, mock_model_catalog
    ):
        """Test model recommendations when user has no credentials."""
        from app.api.v1.models import get_model_recommendations

        # Set up database mock to return no credentials
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        request = ModelRecommendationRequest(
            prompt="General question about AI",
            performance_preference="quality",
            budget_preference="low",
        )

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_model_recommendations(
                request=request,
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelRecommendationResponse)
        # Should still get recommendations for models that don't require API keys
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_get_model_recommendations_exception_handling(
        self, mock_user, mock_db_session, mock_model_catalog
    ):
        """Test model recommendations exception handling."""
        from app.api.v1.models import get_model_recommendations

        # Mock database to raise an exception
        mock_db_session.execute.side_effect = Exception("Database error")

        request = ModelRecommendationRequest(
            prompt="Test prompt",
            performance_preference="quality",
            budget_preference="medium",
        )

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_model_recommendations(
                    request=request,
                    current_user=mock_user,
                    db=mock_db_session,
                )

        assert exc_info.value.status_code == 500
        assert "Failed to get recommendations" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_providers_success(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test successful providers retrieval."""
        from app.api.v1.models import get_providers

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_providers(
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, list)
        assert len(response) == 3
        assert all(isinstance(provider, ProviderSummary) for provider in response)

        # Check credential status
        openai_provider = next(p for p in response if p.provider == ProviderType.OPENAI)
        assert openai_provider.user_has_credentials is True

        ollama_provider = next(p for p in response if p.provider == ProviderType.OLLAMA)
        assert ollama_provider.user_has_credentials is False

    @pytest.mark.asyncio
    async def test_get_providers_exception_handling(
        self, mock_user, mock_db_session, mock_model_catalog
    ):
        """Test providers endpoint exception handling."""
        from app.api.v1.models import get_providers

        # Mock database to raise an exception
        mock_db_session.execute.side_effect = Exception("Database error")

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_providers(
                    current_user=mock_user,
                    db=mock_db_session,
                )

        assert exc_info.value.status_code == 500
        assert "Failed to get providers" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_capabilities_success(self, mock_user, mock_model_catalog):
        """Test successful capabilities retrieval."""
        from app.api.v1.models import get_capabilities

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_capabilities(current_user=mock_user)

        assert isinstance(response, list)
        assert len(response) == 3
        assert ModelCapability.CHAT_COMPLETION in response
        assert ModelCapability.FUNCTION_CALLING in response
        assert ModelCapability.TEXT_COMPLETION in response

    @pytest.mark.asyncio
    async def test_get_capabilities_exception_handling(
        self, mock_user, mock_model_catalog
    ):
        """Test capabilities endpoint exception handling."""
        from app.api.v1.models import get_capabilities

        mock_model_catalog.get_capabilities.side_effect = Exception("Catalog error")

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_capabilities(current_user=mock_user)

        assert exc_info.value.status_code == 500
        assert "Failed to get capabilities" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_available_models_success(
        self, mock_user, mock_db_session, mock_model_catalog, mock_provider_credentials
    ):
        """Test successful available models retrieval."""
        from app.api.v1.models import get_available_models

        # Set up database mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_provider_credentials
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_available_models(
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelCatalogResponse)
        # Should include models that user has credentials for plus free models
        assert len(response.models) >= 1  # At least the Ollama model
        assert len(response.providers) >= 1

    @pytest.mark.asyncio
    async def test_get_available_models_no_credentials(
        self, mock_user, mock_db_session, mock_model_catalog
    ):
        """Test available models when user has no credentials."""
        from app.api.v1.models import get_available_models

        # Set up database mock to return no credentials
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            response = await get_available_models(
                current_user=mock_user,
                db=mock_db_session,
            )

        assert isinstance(response, ModelCatalogResponse)
        # Should still get models that don't require API keys
        free_models = [m for m in response.models if not m.requires_api_key]
        assert len(free_models) >= 1

    @pytest.mark.asyncio
    async def test_get_available_models_exception_handling(
        self, mock_user, mock_db_session, mock_model_catalog
    ):
        """Test available models exception handling."""
        from app.api.v1.models import get_available_models

        # Mock database to raise an exception
        mock_db_session.execute.side_effect = Exception("Database error")

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            with pytest.raises(HTTPException) as exc_info:
                await get_available_models(
                    current_user=mock_user,
                    db=mock_db_session,
                )

        assert exc_info.value.status_code == 500
        assert "Failed to get available models" in str(exc_info.value.detail)

    def test_router_exists(self):
        """Test that the router is properly configured."""
        assert router is not None
        # Check that the router has the expected endpoints
        route_paths = [route.path for route in router.routes]
        assert "/catalog" in route_paths
        assert "/models" in route_paths
        assert "/models/{model_id}" in route_paths
        assert "/recommendations" in route_paths
        assert "/providers" in route_paths
        assert "/capabilities" in route_paths
        assert "/available" in route_paths
