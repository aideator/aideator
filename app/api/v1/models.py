"""
API endpoints for model management and selection.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.provider import (
    ModelCapability,
    ProviderCredential,
    ProviderType,
)
from app.models.user import User
from app.schemas.models import (
    ModelCatalogResponse,
    ModelDefinitionResponse,
    ModelRecommendation,
    ModelRecommendationRequest,
    ModelRecommendationResponse,
    ProviderSummary,
)
from app.services.model_catalog import model_catalog

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/catalog", response_model=ModelCatalogResponse)
async def get_model_catalog(
    provider: ProviderType | None = Query(None, description="Filter by provider"),
    capability: ModelCapability | None = Query(None, description="Filter by capability"),
    requires_api_key: bool | None = Query(None, description="Filter by API key requirement"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get the full model catalog with provider information and user credentials status.
    """
    try:
        # Get user's existing credentials
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == current_user.id,
                ProviderCredential.is_active == True
            )
        )
        user_credentials = result.all()

        user_provider_map = {cred.provider: True for cred in user_credentials}

        # Get all models from catalog
        all_models = model_catalog.get_all_models()

        # Apply filters
        if provider:
            all_models = [m for m in all_models if m.provider == provider]

        if capability:
            all_models = [m for m in all_models if capability in m.capabilities]

        if requires_api_key is not None:
            all_models = [m for m in all_models if m.requires_api_key == requires_api_key]

        # Convert to response format
        model_responses = []
        for model in all_models:
            model_response = ModelDefinitionResponse(
                id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                provider=model.provider,
                model_name=model.model_name,
                litellm_model_name=model.litellm_model_name,
                display_name=model.display_name,
                description=model.description,
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                input_price_per_1m_tokens=model.input_price_per_1m_tokens,
                output_price_per_1m_tokens=model.output_price_per_1m_tokens,
                capabilities=model.capabilities,
                requires_api_key=model.requires_api_key,
                requires_region=model.requires_region,
                requires_project_id=model.requires_project_id,
                is_active=True,
            )
            model_responses.append(model_response)

        # Create provider summaries
        provider_summaries = []
        provider_names = {
            ProviderType.OPENAI: "OpenAI",
            ProviderType.ANTHROPIC: "Anthropic",
            ProviderType.GEMINI: "Google Gemini",
            ProviderType.VERTEX_AI: "Google Vertex AI",
            ProviderType.MISTRAL: "Mistral AI",
            ProviderType.COHERE: "Cohere",
            ProviderType.BEDROCK: "AWS Bedrock",
            ProviderType.AZURE: "Azure OpenAI",
            ProviderType.HUGGINGFACE: "Hugging Face",
            ProviderType.GROQ: "Groq",
            ProviderType.PERPLEXITY: "Perplexity",
            ProviderType.DEEPSEEK: "DeepSeek",
            ProviderType.TOGETHER: "Together AI",
            ProviderType.OLLAMA: "Ollama",
        }

        provider_descriptions = {
            ProviderType.OPENAI: "Leading AI research company, creators of GPT models",
            ProviderType.ANTHROPIC: "AI safety company, creators of Claude models",
            ProviderType.GEMINI: "Google's latest multimodal AI models",
            ProviderType.VERTEX_AI: "Google Cloud's AI platform with multiple model providers",
            ProviderType.MISTRAL: "European AI company with open and commercial models",
            ProviderType.COHERE: "Enterprise-focused NLP models",
            ProviderType.BEDROCK: "Amazon's managed AI service with multiple providers",
            ProviderType.AZURE: "Microsoft's OpenAI partnership offerings",
            ProviderType.HUGGINGFACE: "Open source AI model hub",
            ProviderType.GROQ: "Ultra-fast AI inference platform",
            ProviderType.PERPLEXITY: "AI models with web search capabilities",
            ProviderType.DEEPSEEK: "Chinese AI company with competitive models",
            ProviderType.TOGETHER: "AI inference platform with open models",
            ProviderType.OLLAMA: "Run AI models locally",
        }

        # Group models by provider
        provider_model_count = {}
        for model in model_responses:
            provider_model_count[model.provider] = provider_model_count.get(model.provider, 0) + 1

        for provider_type, count in provider_model_count.items():
            provider_summary = ProviderSummary(
                provider=provider_type,
                display_name=provider_names.get(provider_type, provider_type.value.title()),
                description=provider_descriptions.get(provider_type, f"{provider_type.value.title()} AI models"),
                requires_api_key=any(m.requires_api_key for m in model_responses if m.provider == provider_type),
                model_count=count,
                user_has_credentials=user_provider_map.get(provider_type, False),
            )
            provider_summaries.append(provider_summary)

        # Sort providers by name
        provider_summaries.sort(key=lambda x: x.display_name)

        return ModelCatalogResponse(
            providers=provider_summaries,
            models=model_responses,
            capabilities=model_catalog.get_capabilities(),
        )

    except Exception as e:
        logger.error(f"Error getting model catalog: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model catalog")


@router.get("/models", response_model=list[ModelDefinitionResponse])
async def get_models(
    provider: ProviderType | None = Query(None, description="Filter by provider"),
    capability: ModelCapability | None = Query(None, description="Filter by capability"),
    requires_api_key: bool | None = Query(None, description="Filter by API key requirement"),
    current_user: User = Depends(get_current_user),
):
    """
    Get available models with optional filtering.
    """
    try:
        # Get models from catalog
        models = model_catalog.get_all_models()

        # Apply filters
        if provider:
            models = [m for m in models if m.provider == provider]

        if capability:
            models = [m for m in models if capability in m.capabilities]

        if requires_api_key is not None:
            models = [m for m in models if m.requires_api_key == requires_api_key]

        # Convert to response format
        response_models = []
        for model in models:
            response_model = ModelDefinitionResponse(
                id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                provider=model.provider,
                model_name=model.model_name,
                litellm_model_name=model.litellm_model_name,
                display_name=model.display_name,
                description=model.description,
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                input_price_per_1m_tokens=model.input_price_per_1m_tokens,
                output_price_per_1m_tokens=model.output_price_per_1m_tokens,
                capabilities=model.capabilities,
                requires_api_key=model.requires_api_key,
                requires_region=model.requires_region,
                requires_project_id=model.requires_project_id,
                is_active=True,
            )
            response_models.append(response_model)

        return response_models

    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models")


@router.get("/models/{model_id}", response_model=ModelDefinitionResponse)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get details for a specific model.
    """
    try:
        # Parse model ID to get provider and model name
        # Format: model_{model_name}_{provider}
        parts = model_id.split("_")
        if len(parts) < 3:
            raise HTTPException(status_code=400, detail="Invalid model ID format")

        provider_str = parts[-1]
        model_name_parts = parts[1:-1]
        model_name = "_".join(model_name_parts).replace("_", "-")

        try:
            provider = ProviderType(provider_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid provider in model ID")

        # Find model in catalog
        models = model_catalog.get_models_by_provider(provider)
        model = None
        for m in models:
            if m.model_name == model_name:
                model = m
                break

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return ModelDefinitionResponse(
            id=model_id,
            provider=model.provider,
            model_name=model.model_name,
            litellm_model_name=model.litellm_model_name,
            display_name=model.display_name,
            description=model.description,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            input_price_per_1m_tokens=model.input_price_per_1m_tokens,
            output_price_per_1m_tokens=model.output_price_per_1m_tokens,
            capabilities=model.capabilities,
            requires_api_key=model.requires_api_key,
            requires_region=model.requires_region,
            requires_project_id=model.requires_project_id,
            is_active=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model")


@router.post("/recommendations", response_model=ModelRecommendationResponse)
async def get_model_recommendations(
    request: ModelRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get model recommendations based on task requirements.
    """
    try:
        # Get user's available credentials
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == current_user.id,
                ProviderCredential.is_active == True
            )
        )
        user_credentials = result.all()

        available_providers = {cred.provider for cred in user_credentials}

        # Get all models
        all_models = model_catalog.get_all_models()

        # Filter by available providers or models that don't require API keys
        available_models = [
            m for m in all_models
            if not m.requires_api_key or m.provider in available_providers
        ]

        # Simple recommendation logic based on task type and preferences
        recommendations = []

        # Analyze prompt for task type
        prompt_lower = request.prompt.lower()

        # Code-related tasks
        if any(keyword in prompt_lower for keyword in ["code", "programming", "debug", "implement", "function"]):
            # Prioritize models good for coding
            coding_models = [
                m for m in available_models
                if any(cap in [ModelCapability.FUNCTION_CALLING, ModelCapability.TEXT_COMPLETION] for cap in m.capabilities)
            ]

            if request.performance_preference == "quality":
                # Prefer high-quality models
                quality_models = [m for m in coding_models if "gpt-4" in m.model_name.lower() or "claude" in m.model_name.lower()]
                for model in quality_models[:3]:
                    recommendations.append(ModelRecommendation(
                        model_definition_id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                        confidence_score=0.9,
                        reasoning=f"{model.display_name} is excellent for code analysis and generation tasks"
                    ))
            elif request.performance_preference == "speed":
                # Prefer fast models
                speed_models = [m for m in coding_models if "turbo" in m.model_name.lower() or "mini" in m.model_name.lower()]
                for model in speed_models[:3]:
                    recommendations.append(ModelRecommendation(
                        model_definition_id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                        confidence_score=0.8,
                        reasoning=f"{model.display_name} provides fast responses for coding tasks"
                    ))

        # Analysis tasks
        elif any(keyword in prompt_lower for keyword in ["analyze", "review", "examine", "study"]):
            # Prioritize models good for analysis
            analysis_models = [
                m for m in available_models
                if ModelCapability.CHAT_COMPLETION in m.capabilities
            ]

            # Prefer high-context models for analysis
            high_context_models = [m for m in analysis_models if m.context_window and m.context_window > 32000]
            for model in high_context_models[:3]:
                recommendations.append(ModelRecommendation(
                    model_definition_id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                    confidence_score=0.85,
                    reasoning=f"{model.display_name} has large context window ({model.context_window} tokens) ideal for analysis"
                ))

        # Default recommendations if no specific task type detected
        if not recommendations:
            # Get balanced recommendations
            balanced_models = [
                m for m in available_models
                if ModelCapability.CHAT_COMPLETION in m.capabilities
            ]

            # Sort by a simple scoring system
            def score_model(model):
                score = 0
                if "gpt-4" in model.model_name.lower():
                    score += 3
                elif "claude" in model.model_name.lower():
                    score += 2
                elif "gemini" in model.model_name.lower():
                    score += 1

                # Budget consideration
                if request.budget_preference == "low" and model.input_price_per_1m_tokens:
                    if model.input_price_per_1m_tokens < 1.0:
                        score += 2
                elif request.budget_preference == "high" and model.input_price_per_1m_tokens:
                    if model.input_price_per_1m_tokens > 10.0:
                        score += 1

                return score

            balanced_models.sort(key=score_model, reverse=True)

            for model in balanced_models[:3]:
                recommendations.append(ModelRecommendation(
                    model_definition_id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                    confidence_score=0.7,
                    reasoning=f"{model.display_name} is a reliable choice for general tasks"
                ))

        # Ensure we have at least some recommendations
        if not recommendations:
            # Fallback to any available model
            for model in available_models[:3]:
                recommendations.append(ModelRecommendation(
                    model_definition_id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                    confidence_score=0.5,
                    reasoning=f"{model.display_name} is available with your current credentials"
                ))

        explanation = "Based on your task description and preferences, here are the recommended models. "
        if request.task_type:
            explanation += f"Task type: {request.task_type}. "
        if request.budget_preference:
            explanation += f"Budget preference: {request.budget_preference}. "
        if request.performance_preference:
            explanation += f"Performance preference: {request.performance_preference}. "

        return ModelRecommendationResponse(
            recommendations=recommendations,
            explanation=explanation
        )

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/providers", response_model=list[ProviderSummary])
async def get_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get available providers with user credential status.
    """
    try:
        # Get user's existing credentials
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == current_user.id,
                ProviderCredential.is_active == True
            )
        )
        user_credentials = result.all()

        user_provider_map = {cred.provider: True for cred in user_credentials}

        # Get providers from catalog
        providers = model_catalog.get_providers()

        provider_summaries = []
        for provider in providers:
            models = model_catalog.get_models_by_provider(provider)

            summary = ProviderSummary(
                provider=provider,
                display_name=provider.value.title(),
                description=f"{provider.value.title()} AI models",
                requires_api_key=any(m.requires_api_key for m in models),
                model_count=len(models),
                user_has_credentials=user_provider_map.get(provider, False),
            )
            provider_summaries.append(summary)

        return provider_summaries

    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get providers")


@router.get("/capabilities", response_model=list[ModelCapability])
async def get_capabilities(
    current_user: User = Depends(get_current_user),
):
    """
    Get all available model capabilities.
    """
    try:
        return model_catalog.get_capabilities()

    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to get capabilities")


@router.get("/available", response_model=ModelCatalogResponse)
async def get_available_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get models that are currently available based on configured Kubernetes secrets.
    This endpoint checks which API keys are actually available in the cluster.
    """
    try:

        # Check which API keys are available in the environment
        # These would typically be mounted from Kubernetes secrets
        available_keys = {}

        # Check for API keys that are configured
        api_key_mapping = {
            ProviderType.OPENAI: settings.openai_api_key,
            ProviderType.ANTHROPIC: settings.anthropic_api_key,
            ProviderType.GEMINI: settings.gemini_api_key,
        }

        for provider, api_key in api_key_mapping.items():
            available_keys[provider] = bool(api_key and api_key.strip() and len(api_key) > 5)

        # Get models that can be used with available keys
        available_models = model_catalog.get_available_models_for_keys(
            {provider.value: available for provider, available in available_keys.items()}
        )

        # Convert to response format
        model_responses = []
        for model in available_models:
            model_response = ModelDefinitionResponse(
                id=f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}",
                provider=model.provider,
                model_name=model.model_name,
                litellm_model_name=model.litellm_model_name,
                display_name=model.display_name,
                description=model.description,
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                input_price_per_1m_tokens=model.input_price_per_1m_tokens,
                output_price_per_1m_tokens=model.output_price_per_1m_tokens,
                capabilities=model.capabilities,
                requires_api_key=model.requires_api_key,
                requires_region=model.requires_region,
                requires_project_id=model.requires_project_id,
                is_active=True,
            )
            model_responses.append(model_response)

        # Create provider summaries for available providers only
        provider_summaries = []
        available_providers = set(model.provider for model in available_models)

        provider_names = {
            ProviderType.OPENAI: "OpenAI",
            ProviderType.ANTHROPIC: "Anthropic",
            ProviderType.GEMINI: "Google Gemini",
            ProviderType.VERTEX_AI: "Google Vertex AI",
            ProviderType.MISTRAL: "Mistral AI",
            ProviderType.COHERE: "Cohere",
            ProviderType.BEDROCK: "AWS Bedrock",
            ProviderType.AZURE: "Azure OpenAI",
            ProviderType.HUGGINGFACE: "Hugging Face",
            ProviderType.GROQ: "Groq",
            ProviderType.PERPLEXITY: "Perplexity",
            ProviderType.DEEPSEEK: "DeepSeek",
            ProviderType.TOGETHER: "Together AI",
            ProviderType.OLLAMA: "Ollama",
        }

        for provider in available_providers:
            provider_models = [m for m in model_responses if m.provider == provider]
            provider_summary = ProviderSummary(
                provider=provider,
                display_name=provider_names.get(provider, provider.value.title()),
                description=f"Available {provider.value.title()} models",
                requires_api_key=any(m.requires_api_key for m in provider_models),
                model_count=len(provider_models),
                user_has_credentials=available_keys.get(provider, False),
            )
            provider_summaries.append(provider_summary)

        # Sort providers by name
        provider_summaries.sort(key=lambda x: x.display_name)

        return ModelCatalogResponse(
            models=model_responses,
            providers=provider_summaries,
            total_models=len(model_responses),
            available_providers=len(provider_summaries),
        )

    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")
