"""Tests for models API endpoints."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.models import router
from app.models.provider import (
    ModelCapability,
    ProviderCredential,
    ProviderType,
)
from app.models.user import User
from app.schemas.models import (
    ModelRecommendationRequest,
)
from app.services.model_catalog import ModelInfo


class TestModelsEndpoints:
    """Test models API endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=User)
        user.id = "test-user-123"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_model_catalog(self):
        """Create a mock model catalog with sample models."""
        models = [
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="gpt-4",
                litellm_model_name="gpt-4",
                display_name="GPT-4",
                description="OpenAI's most capable model",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=30.0,
                output_price_per_1m_tokens=60.0,
                capabilities=[
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ],
                requires_api_key=True,
                requires_region=False,
                requires_project_id=False,
            ),
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-opus",
                litellm_model_name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                description="Anthropic's most capable model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=15.0,
                output_price_per_1m_tokens=75.0,
                capabilities=[
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.VISION,
                    ModelCapability.STREAMING,
                ],
                requires_api_key=True,
                requires_region=False,
                requires_project_id=False,
            ),
            ModelInfo(
                provider=ProviderType.OLLAMA,
                model_name="llama-2-7b",
                litellm_model_name="ollama/llama2",
                display_name="Llama 2 7B",
                description="Open source model",
                context_window=4096,
                max_output_tokens=2048,
                input_price_per_1m_tokens=0.0,
                output_price_per_1m_tokens=0.0,
                capabilities=[ModelCapability.CHAT_COMPLETION],
                requires_api_key=False,
                requires_region=False,
                requires_project_id=False,
            ),
        ]

        mock_catalog = Mock()
        mock_catalog.get_all_models.return_value = models
        mock_catalog.get_models_by_provider.side_effect = lambda p: [
            m for m in models if m.provider == p
        ]
        mock_catalog.get_capabilities.return_value = [
            ModelCapability.CHAT_COMPLETION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.STREAMING,
            ModelCapability.VISION,
        ]
        mock_catalog.get_providers.return_value = [
            ProviderType.OPENAI,
            ProviderType.ANTHROPIC,
            ProviderType.OLLAMA,
        ]

        return mock_catalog

    @pytest.fixture
    def mock_user_credentials(self):
        """Create mock user credentials."""
        cred1 = Mock(spec=ProviderCredential)
        cred1.provider = ProviderType.OPENAI
        cred1.user_id = "test-user-123"
        cred1.is_active = True

        return [cred1]

    @pytest.mark.asyncio
    async def test_get_model_catalog(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test getting the full model catalog."""
        # Mock database query for user credentials
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model_catalog

            result = await get_model_catalog(
                provider=None,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db,
            )

            # Verify structure
            assert len(result.providers) == 3
            assert len(result.models) == 3
            assert len(result.capabilities) == 4

            # Check provider summaries
            openai_provider = next(
                p for p in result.providers if p.provider == ProviderType.OPENAI
            )
            assert openai_provider.display_name == "OpenAI"
            assert openai_provider.model_count == 1
            assert openai_provider.user_has_credentials is True

            anthropic_provider = next(
                p for p in result.providers if p.provider == ProviderType.ANTHROPIC
            )
            assert anthropic_provider.user_has_credentials is False

            # Check models
            gpt4 = next(m for m in result.models if m.model_name == "gpt-4")
            assert gpt4.id == "model_gpt_4_openai"
            assert gpt4.provider == ProviderType.OPENAI
            assert gpt4.input_price_per_1m_tokens == 30.0

    @pytest.mark.asyncio
    async def test_get_model_catalog_with_filters(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test getting model catalog with filters."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model_catalog

            # Filter by provider
            result = await get_model_catalog(
                provider=ProviderType.OPENAI,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db,
            )

            assert len(result.models) == 1
            assert result.models[0].provider == ProviderType.OPENAI

            # Filter by capability
            result = await get_model_catalog(
                provider=None,
                capability=ModelCapability.VISION,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db,
            )

            assert len(result.models) == 1
            assert result.models[0].model_name == "claude-3-opus"

            # Filter by API key requirement
            result = await get_model_catalog(
                provider=None,
                capability=None,
                requires_api_key=False,
                current_user=mock_user,
                db=mock_db,
            )

            assert len(result.models) == 1
            assert result.models[0].model_name == "llama-2-7b"

    @pytest.mark.asyncio
    async def test_get_model_catalog_error(self, mock_db, mock_user):
        """Test error handling in get_model_catalog."""
        mock_db.execute.side_effect = Exception("Database error")

        from app.api.v1.models import get_model_catalog

        with pytest.raises(HTTPException) as exc_info:
            await get_model_catalog(
                provider=None,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
                db=mock_db,
            )

        assert exc_info.value.status_code == 500
        assert "Failed to get model catalog" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_models(self, mock_user, mock_model_catalog):
        """Test getting models list."""
        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_models

            result = await get_models(
                provider=None,
                capability=None,
                requires_api_key=None,
                current_user=mock_user,
            )

            assert len(result) == 3
            assert any(m.model_name == "gpt-4" for m in result)
            assert any(m.model_name == "claude-3-opus" for m in result)
            assert any(m.model_name == "llama-2-7b" for m in result)

    @pytest.mark.asyncio
    async def test_get_model_by_id(self, mock_user, mock_model_catalog):
        """Test getting a specific model by ID."""
        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model

            result = await get_model(
                model_id="model_gpt_4_openai", current_user=mock_user
            )

            assert result.model_name == "gpt-4"
            assert result.provider == ProviderType.OPENAI
            assert result.display_name == "GPT-4"

    @pytest.mark.asyncio
    async def test_get_model_invalid_id(self, mock_user, mock_model_catalog):
        """Test getting model with invalid ID format."""
        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model

            with pytest.raises(HTTPException) as exc_info:
                await get_model(model_id="invalid_id", current_user=mock_user)

            assert exc_info.value.status_code == 400
            assert "Invalid model ID format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_not_found(self, mock_user, mock_model_catalog):
        """Test getting non-existent model."""
        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model

            with pytest.raises(HTTPException) as exc_info:
                await get_model(
                    model_id="model_nonexistent_openai", current_user=mock_user
                )

            assert exc_info.value.status_code == 404
            assert "Model not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_model_recommendations_code_task(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test getting model recommendations for code tasks."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model_recommendations

            request = ModelRecommendationRequest(
                prompt="Write a function to calculate fibonacci numbers",
                task_type="code_generation",
                variations=3,
                performance_preference="quality",
                budget_preference="medium",
            )

            result = await get_model_recommendations(
                request=request, current_user=mock_user, db=mock_db
            )

            assert len(result.recommendations) > 0
            assert (
                "code" in result.explanation.lower()
                or "function" in result.explanation.lower()
            )

            # Should recommend GPT-4 for quality code tasks
            top_rec = result.recommendations[0]
            assert "gpt_4" in top_rec.model_definition_id
            assert top_rec.confidence_score >= 0.8
            assert "code" in top_rec.reasoning.lower()

    @pytest.mark.asyncio
    async def test_get_model_recommendations_analysis_task(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test getting model recommendations for analysis tasks."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model_recommendations

            request = ModelRecommendationRequest(
                prompt="Analyze the performance of this codebase",
                task_type="analysis",
                variations=3,
                performance_preference="balanced",
                budget_preference="low",
            )

            result = await get_model_recommendations(
                request=request, current_user=mock_user, db=mock_db
            )

            assert len(result.recommendations) > 0
            assert (
                "analyze" in result.explanation.lower()
                or "analysis" in result.explanation.lower()
            )

    @pytest.mark.asyncio
    async def test_get_model_recommendations_speed_preference(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test recommendations with speed preference."""
        # Add a turbo model to the catalog
        models = mock_model_catalog.get_all_models()
        turbo_model = ModelInfo(
            provider=ProviderType.OPENAI,
            model_name="gpt-3.5-turbo",
            litellm_model_name="gpt-3.5-turbo",
            display_name="GPT-3.5 Turbo",
            description="Fast model",
            context_window=4096,
            max_output_tokens=4096,
            input_price_per_1m_tokens=1.0,
            output_price_per_1m_tokens=2.0,
            capabilities=[
                ModelCapability.CHAT_COMPLETION,
                ModelCapability.FUNCTION_CALLING,
            ],
            requires_api_key=True,
        )
        models.append(turbo_model)
        mock_model_catalog.get_all_models.return_value = models

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model_recommendations

            request = ModelRecommendationRequest(
                prompt="Write some code quickly",
                performance_preference="speed",
                budget_preference="low",
            )

            result = await get_model_recommendations(
                request=request, current_user=mock_user, db=mock_db
            )

            # Should prefer turbo model for speed
            assert any(
                "turbo" in rec.model_definition_id for rec in result.recommendations
            )

    @pytest.mark.asyncio
    async def test_get_model_recommendations_no_credentials(
        self, mock_db, mock_user, mock_model_catalog
    ):
        """Test recommendations when user has no credentials."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []  # No credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_model_recommendations

            request = ModelRecommendationRequest(prompt="Generate some text")

            result = await get_model_recommendations(
                request=request, current_user=mock_user, db=mock_db
            )

            # Should only recommend models that don't require API keys
            assert len(result.recommendations) > 0
            # Should recommend Ollama model
            assert any(
                "llama" in rec.model_definition_id for rec in result.recommendations
            )

    @pytest.mark.asyncio
    async def test_get_providers(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test getting providers list."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_providers

            result = await get_providers(current_user=mock_user, db=mock_db)

            assert len(result) == 3

            # Check OpenAI provider
            openai = next(p for p in result if p.provider == ProviderType.OPENAI)
            assert openai.display_name == "OpenAI"
            assert openai.user_has_credentials is True
            assert openai.model_count == 1

            # Check Anthropic provider
            anthropic = next(p for p in result if p.provider == ProviderType.ANTHROPIC)
            assert anthropic.user_has_credentials is False

    @pytest.mark.asyncio
    async def test_get_capabilities(self, mock_user, mock_model_catalog):
        """Test getting capabilities list."""
        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_capabilities

            result = await get_capabilities(current_user=mock_user)

            assert len(result) == 4
            assert ModelCapability.CHAT_COMPLETION in result
            assert ModelCapability.FUNCTION_CALLING in result
            assert ModelCapability.STREAMING in result
            assert ModelCapability.VISION in result

    @pytest.mark.asyncio
    async def test_get_available_models(
        self, mock_db, mock_user, mock_model_catalog, mock_user_credentials
    ):
        """Test getting models available to the user."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_user_credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_available_models

            result = await get_available_models(current_user=mock_user, db=mock_db)

            # Should have models from OpenAI (user has creds) and Ollama (no key required)
            assert len(result.models) == 2
            model_names = [m.model_name for m in result.models]
            assert "gpt-4" in model_names
            assert "llama-2-7b" in model_names
            assert "claude-3-opus" not in model_names  # No Anthropic credentials

            # Should have 2 providers
            assert len(result.providers) == 2
            provider_types = [p.provider for p in result.providers]
            assert ProviderType.OPENAI in provider_types
            assert ProviderType.OLLAMA in provider_types

    @pytest.mark.asyncio
    async def test_get_available_models_no_credentials(
        self, mock_db, mock_user, mock_model_catalog
    ):
        """Test available models when user has no credentials."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []  # No credentials
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.models.model_catalog", mock_model_catalog):
            from app.api.v1.models import get_available_models

            result = await get_available_models(current_user=mock_user, db=mock_db)

            # Should only have Ollama model (no API key required)
            assert len(result.models) == 1
            assert result.models[0].model_name == "llama-2-7b"
            assert result.models[0].provider == ProviderType.OLLAMA

    def test_router_exists(self):
        """Test that router is properly configured."""
        assert router is not None
        routes = [route.path for route in router.routes]
        assert "/catalog" in routes
        assert "/models" in routes
        assert "/models/{model_id}" in routes
        assert "/recommendations" in routes
        assert "/providers" in routes
        assert "/capabilities" in routes
        assert "/available" in routes
