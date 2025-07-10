"""
Model catalog service for managing LiteLLM supported models.

This service dynamically discovers models from the LiteLLM proxy rather than
maintaining a hardcoded list. This ensures we always have the latest models
available without manual updates.
"""

import logging
import httpx
import os
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.models.provider import (
    ModelCapability,
    ModelDefinition,
    ProviderType,
)
from app.models.model_definition import ModelDefinitionDB
from app.core.database import get_sync_session

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a specific model."""
    
    provider: ProviderType
    model_name: str
    litellm_model_name: str
    display_name: str
    description: Optional[str] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_price_per_1m_tokens: Optional[float] = None
    output_price_per_1m_tokens: Optional[float] = None
    capabilities: List[ModelCapability] = None
    requires_api_key: bool = True
    requires_region: bool = False
    requires_project_id: bool = False
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ModelCatalogService:
    """Service for managing the model catalog.
    
    Dynamically discovers models from the LiteLLM proxy rather than maintaining
    a static list. Includes caching to reduce API calls.
    """
    
    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._models_loaded = False
        self._load_models_from_db()
    
    def _load_models_from_db(self):
        """Load models from database instead of hardcoding them."""
        try:
            for session in get_sync_session():
                # Query active models from database
                db_models = session.exec(
                    select(ModelDefinitionDB).where(
                        ModelDefinitionDB.is_active == True
                    )
                ).all()
                
                # Convert to ModelInfo objects
                for db_model in db_models:
                    # Map capabilities from tags
                    capabilities = []
                    if db_model.supports_streaming:
                        capabilities.append(ModelCapability.STREAMING)
                    if db_model.supports_function_calling:
                        capabilities.append(ModelCapability.FUNCTION_CALLING)
                    if db_model.supports_vision:
                        capabilities.append(ModelCapability.VISION)
                    if "embedding" in db_model.category:
                        capabilities.append(ModelCapability.EMBEDDINGS)
                    else:
                        capabilities.extend([
                            ModelCapability.TEXT_COMPLETION,
                            ModelCapability.CHAT_COMPLETION
                        ])
                    
                    # Map provider string to enum
                    provider_map = {
                        "openai": ProviderType.OPENAI,
                        "anthropic": ProviderType.ANTHROPIC,
                        "gemini": ProviderType.GEMINI,
                        "google": ProviderType.GEMINI,
                        "vertex_ai": ProviderType.VERTEX_AI,
                        "bedrock": ProviderType.BEDROCK,
                        "azure": ProviderType.AZURE,
                        "mistral": ProviderType.MISTRAL,
                        "cohere": ProviderType.COHERE,
                        "huggingface": ProviderType.HUGGING_FACE,
                        "together": ProviderType.TOGETHER,
                        "replicate": ProviderType.REPLICATE,
                        "groq": ProviderType.GROQ,
                        "deepseek": ProviderType.DEEPSEEK,
                        "perplexity": ProviderType.PERPLEXITY,
                        "ollama": ProviderType.OLLAMA,
                    }
                    
                    provider = provider_map.get(
                        db_model.litellm_provider.lower(), 
                        ProviderType.OPENAI
                    )
                    
                    model_info = ModelInfo(
                        provider=provider,
                        model_name=db_model.model_name,
                        litellm_model_name=db_model.model_name,  # Use same name
                        display_name=db_model.display_name,
                        description=db_model.description,
                        context_window=db_model.max_tokens,
                        max_output_tokens=db_model.max_output_tokens,
                        input_price_per_1m_tokens=db_model.input_cost_per_token * 1_000_000 if db_model.input_cost_per_token else None,
                        output_price_per_1m_tokens=db_model.output_cost_per_token * 1_000_000 if db_model.output_cost_per_token else None,
                        capabilities=capabilities,
                        requires_api_key=db_model.requires_api_key
                    )
                    
                    self._models[model_info.litellm_model_name] = model_info
                
                self._models_loaded = True
                logger.info(f"Loaded {len(self._models)} models from database")
                
        except Exception as e:
            logger.warning(f"Failed to load models from database: {str(e)}")
            logger.info("Falling back to static model initialization")
            self._initialize_model_catalog()
    
    def _initialize_model_catalog(self):
        """Initialize the model catalog with all LiteLLM supported models."""
        
        # OpenAI Models
        self._add_openai_models()
        
        # Anthropic Models
        self._add_anthropic_models()
        
        # Google Models (Gemini)
        self._add_google_models()
        
        # Vertex AI Models
        self._add_vertex_ai_models()
        
        # AWS Bedrock Models
        self._add_bedrock_models()
        
        # Azure OpenAI Models
        self._add_azure_models()
        
        # Mistral AI Models
        self._add_mistral_models()
        
        # Cohere Models
        self._add_cohere_models()
        
        # Meta/Llama Models (via various providers)
        self._add_meta_models()
        
        # Hugging Face Models
        self._add_huggingface_models()
        
        # Together AI Models
        self._add_together_models()
        
        # Replicate Models
        self._add_replicate_models()
        
        # Anyscale Models
        self._add_anyscale_models()
        
        # Perplexity Models
        self._add_perplexity_models()
        
        # DeepSeek Models
        self._add_deepseek_models()
        
        # Groq Models
        self._add_groq_models()
        
        # DeepInfra Models
        self._add_deepinfra_models()
        
        # AI21 Models
        self._add_ai21_models()
        
        # NLP Cloud Models
        self._add_nlp_cloud_models()
        
        # Voyage AI Models
        self._add_voyage_models()
        
        # Xinference Models
        self._add_xinference_models()
        
        # Ollama Models (Local)
        self._add_ollama_models()
        
        # Other Providers
        self._add_other_providers()
    
    def _add_openai_models(self):
        """Add OpenAI models to the catalog."""
        
        openai_models = [
            # GPT-4 models
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="gpt-4",
                litellm_model_name="gpt-4",
                display_name="GPT-4",
                description="Most capable GPT-4 model",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=30.0,
                output_price_per_1m_tokens=60.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="gpt-4-turbo",
                litellm_model_name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                description="Faster, cheaper GPT-4 with 128k context",
                context_window=128000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=10.0,
                output_price_per_1m_tokens=30.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="gpt-4o",
                litellm_model_name="gpt-4o",
                display_name="GPT-4o",
                description="Latest GPT-4 optimized for speed and cost",
                context_window=128000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=5.0,
                output_price_per_1m_tokens=15.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="gpt-4o-mini",
                litellm_model_name="gpt-4o-mini",
                display_name="GPT-4o Mini",
                description="Faster, cheaper GPT-4o for simple tasks",
                context_window=128000,
                max_output_tokens=16384,
                input_price_per_1m_tokens=0.15,
                output_price_per_1m_tokens=0.6,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            # GPT-3.5 models
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="gpt-3.5-turbo",
                litellm_model_name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                description="Fast, cost-effective model for simple tasks",
                context_window=16384,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.5,
                output_price_per_1m_tokens=1.5,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
            # O1 models
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="o1-preview",
                litellm_model_name="o1-preview",
                display_name="O1 Preview",
                description="Advanced reasoning model",
                context_window=128000,
                max_output_tokens=32768,
                input_price_per_1m_tokens=15.0,
                output_price_per_1m_tokens=60.0,
                capabilities=[
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OPENAI,
                model_name="o1-mini",
                litellm_model_name="o1-mini",
                display_name="O1 Mini",
                description="Faster reasoning model",
                context_window=128000,
                max_output_tokens=65536,
                input_price_per_1m_tokens=3.0,
                output_price_per_1m_tokens=12.0,
                capabilities=[
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in openai_models:
            self._models[model.litellm_model_name] = model
    
    def _add_anthropic_models(self):
        """Add Anthropic Claude models to the catalog."""
        
        anthropic_models = [
            # Claude 4 models
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-4-opus-20250514",
                litellm_model_name="claude-4-opus-20250514",
                display_name="Claude 4 Opus",
                description="Most capable Claude 4 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=15.0,
                output_price_per_1m_tokens=75.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-4-sonnet-20250514",
                litellm_model_name="claude-4-sonnet-20250514",
                display_name="Claude 4 Sonnet",
                description="Balanced Claude 4 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=3.0,
                output_price_per_1m_tokens=15.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            # Claude 3.5 models
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-5-sonnet-20241022",
                litellm_model_name="claude-3-5-sonnet-20241022",
                display_name="Claude 3.5 Sonnet",
                description="Most capable Claude 3.5 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=3.0,
                output_price_per_1m_tokens=15.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-5-haiku-20241022",
                litellm_model_name="claude-3-5-haiku-20241022",
                display_name="Claude 3.5 Haiku",
                description="Fastest Claude 3.5 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.8,
                output_price_per_1m_tokens=4.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            # Claude 3 models
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                litellm_model_name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                description="Most capable Claude 3 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=15.0,
                output_price_per_1m_tokens=75.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                litellm_model_name="claude-3-sonnet-20240229",
                display_name="Claude 3 Sonnet",
                description="Balanced Claude 3 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=3.0,
                output_price_per_1m_tokens=15.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                litellm_model_name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                description="Fastest Claude 3 model",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.25,
                output_price_per_1m_tokens=1.25,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
        ]
        
        for model in anthropic_models:
            self._models[model.litellm_model_name] = model
    
    def _add_google_models(self):
        """Add Google Gemini models to the catalog."""
        
        google_models = [
            # Gemini 2.0 models
            ModelInfo(
                provider=ProviderType.GEMINI,
                model_name="gemini-2.0-flash",
                litellm_model_name="gemini-2.0-flash",
                display_name="Gemini 2.0 Flash",
                description="Latest Gemini model with multimodal capabilities",
                context_window=2000000,
                max_output_tokens=8192,
                input_price_per_1m_tokens=0.075,
                output_price_per_1m_tokens=0.3,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                    ModelCapability.WEB_SEARCH,
                ]
            ),
            # Gemini 1.5 models
            ModelInfo(
                provider=ProviderType.GEMINI,
                model_name="gemini-1.5-pro",
                litellm_model_name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                description="Most capable Gemini model",
                context_window=2000000,
                max_output_tokens=8192,
                input_price_per_1m_tokens=1.25,
                output_price_per_1m_tokens=5.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.GEMINI,
                model_name="gemini-1.5-flash",
                litellm_model_name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                description="Fast, efficient Gemini model",
                context_window=1000000,
                max_output_tokens=8192,
                input_price_per_1m_tokens=0.075,
                output_price_per_1m_tokens=0.3,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            # Gemini Pro models
            ModelInfo(
                provider=ProviderType.GEMINI,
                model_name="gemini-pro",
                litellm_model_name="gemini-pro",
                display_name="Gemini Pro",
                description="Original Gemini Pro model",
                context_window=30720,
                max_output_tokens=2048,
                input_price_per_1m_tokens=0.5,
                output_price_per_1m_tokens=1.5,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in google_models:
            self._models[model.litellm_model_name] = model
    
    def _add_vertex_ai_models(self):
        """Add Vertex AI models to the catalog."""
        
        vertex_models = [
            # Gemini on Vertex AI
            ModelInfo(
                provider=ProviderType.VERTEX_AI,
                model_name="gemini-1.5-pro",
                litellm_model_name="vertex_ai/gemini-1.5-pro",
                display_name="Gemini 1.5 Pro (Vertex AI)",
                description="Gemini 1.5 Pro on Google Cloud",
                context_window=2000000,
                max_output_tokens=8192,
                input_price_per_1m_tokens=1.25,
                output_price_per_1m_tokens=5.0,
                requires_project_id=True,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            # Claude on Vertex AI
            ModelInfo(
                provider=ProviderType.VERTEX_AI,
                model_name="claude-4-opus",
                litellm_model_name="vertex_ai/claude-4-opus",
                display_name="Claude 4 Opus (Vertex AI)",
                description="Claude 4 Opus on Google Cloud",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=15.0,
                output_price_per_1m_tokens=75.0,
                requires_project_id=True,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
        ]
        
        for model in vertex_models:
            self._models[model.litellm_model_name] = model
    
    def _add_mistral_models(self):
        """Add Mistral models to the catalog."""
        
        mistral_models = [
            # Large models
            ModelInfo(
                provider=ProviderType.MISTRAL,
                model_name="mistral-large-latest",
                litellm_model_name="mistral/mistral-large-latest",
                display_name="Mistral Large",
                description="Most capable Mistral model",
                context_window=128000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=2.0,
                output_price_per_1m_tokens=6.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
            # Medium models
            ModelInfo(
                provider=ProviderType.MISTRAL,
                model_name="mistral-medium-latest",
                litellm_model_name="mistral/mistral-medium-latest",
                display_name="Mistral Medium",
                description="Balanced Mistral model",
                context_window=32000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.7,
                output_price_per_1m_tokens=2.1,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
            # Small models
            ModelInfo(
                provider=ProviderType.MISTRAL,
                model_name="mistral-small-latest",
                litellm_model_name="mistral/mistral-small-latest",
                display_name="Mistral Small",
                description="Fast, efficient Mistral model",
                context_window=32000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.2,
                output_price_per_1m_tokens=0.6,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
            # Open models
            ModelInfo(
                provider=ProviderType.MISTRAL,
                model_name="open-mistral-7b",
                litellm_model_name="mistral/open-mistral-7b",
                display_name="Mistral 7B",
                description="Open source Mistral model",
                context_window=32000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.25,
                output_price_per_1m_tokens=0.25,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.MISTRAL,
                model_name="open-mixtral-8x7b",
                litellm_model_name="mistral/open-mixtral-8x7b",
                display_name="Mixtral 8x7B",
                description="Open source mixture of experts model",
                context_window=32000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.7,
                output_price_per_1m_tokens=0.7,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in mistral_models:
            self._models[model.litellm_model_name] = model
    
    def _add_cohere_models(self):
        """Add Cohere models to the catalog."""
        
        cohere_models = [
            ModelInfo(
                provider=ProviderType.COHERE,
                model_name="command-r-plus",
                litellm_model_name="cohere/command-r-plus",
                display_name="Command R+",
                description="Most capable Cohere model",
                context_window=128000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=3.0,
                output_price_per_1m_tokens=15.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.COHERE,
                model_name="command-r",
                litellm_model_name="cohere/command-r",
                display_name="Command R",
                description="Balanced Cohere model",
                context_window=128000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.5,
                output_price_per_1m_tokens=1.5,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in cohere_models:
            self._models[model.litellm_model_name] = model
    
    def _add_bedrock_models(self):
        """Add AWS Bedrock models to the catalog."""
        
        bedrock_models = [
            # Claude on Bedrock
            ModelInfo(
                provider=ProviderType.BEDROCK,
                model_name="claude-3-5-sonnet",
                litellm_model_name="bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
                display_name="Claude 3.5 Sonnet (Bedrock)",
                description="Claude 3.5 Sonnet on AWS Bedrock",
                context_window=200000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=3.0,
                output_price_per_1m_tokens=15.0,
                requires_region=True,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
            # Titan models
            ModelInfo(
                provider=ProviderType.BEDROCK,
                model_name="titan-text-premier",
                litellm_model_name="bedrock/amazon.titan-text-premier-v1:0",
                display_name="Titan Text Premier",
                description="Amazon's premier text model",
                context_window=32000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.5,
                output_price_per_1m_tokens=1.5,
                requires_region=True,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            # Llama on Bedrock
            ModelInfo(
                provider=ProviderType.BEDROCK,
                model_name="llama3-70b-instruct",
                litellm_model_name="bedrock/meta.llama3-70b-instruct-v1:0",
                display_name="Llama 3 70B (Bedrock)",
                description="Meta's Llama 3 70B on AWS Bedrock",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=2.65,
                output_price_per_1m_tokens=3.5,
                requires_region=True,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in bedrock_models:
            self._models[model.litellm_model_name] = model
    
    def _add_azure_models(self):
        """Add Azure OpenAI models to the catalog."""
        
        azure_models = [
            ModelInfo(
                provider=ProviderType.AZURE,
                model_name="gpt-4o",
                litellm_model_name="azure/gpt-4o",
                display_name="GPT-4o (Azure)",
                description="GPT-4o on Azure OpenAI",
                context_window=128000,
                max_output_tokens=4096,
                input_price_per_1m_tokens=5.0,
                output_price_per_1m_tokens=15.0,
                requires_region=True,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STREAMING,
                    ModelCapability.VISION,
                ]
            ),
        ]
        
        for model in azure_models:
            self._models[model.litellm_model_name] = model
    
    def _add_huggingface_models(self):
        """Add popular Hugging Face models to the catalog."""
        
        hf_models = [
            # Open models that don't require API keys
            ModelInfo(
                provider=ProviderType.HUGGINGFACE,
                model_name="llama-3-8b-instruct",
                litellm_model_name="huggingface/meta-llama/Meta-Llama-3-8B-Instruct",
                display_name="Llama 3 8B Instruct",
                description="Meta's Llama 3 8B instruction model",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.2,
                output_price_per_1m_tokens=0.2,
                requires_api_key=False,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.HUGGINGFACE,
                model_name="llama-3-70b-instruct",
                litellm_model_name="huggingface/meta-llama/Meta-Llama-3-70B-Instruct",
                display_name="Llama 3 70B Instruct",
                description="Meta's Llama 3 70B instruction model",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.9,
                output_price_per_1m_tokens=0.9,
                requires_api_key=False,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in hf_models:
            self._models[model.litellm_model_name] = model
    
    def _add_other_providers(self):
        """Add models from other providers not covered by specific methods."""
        # Most providers now have dedicated methods
        # This is kept for any miscellaneous providers that might be added later
        pass
    
    def _add_meta_models(self):
        """Add Meta/Llama models available through various providers."""
        # These are covered by individual provider methods
        pass
    
    def _add_together_models(self):
        """Add Together AI models."""
        together_models = [
            ModelInfo(
                provider=ProviderType.TOGETHER,
                model_name="llama-3-70b-chat-hf",
                litellm_model_name="together_ai/meta-llama/Llama-3-70b-chat-hf",
                display_name="Llama 3 70B Chat",
                description="Llama 3 70B on Together AI",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.9,
                output_price_per_1m_tokens=0.9,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.TOGETHER,
                model_name="mixtral-8x7b-instruct",
                litellm_model_name="together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1",
                display_name="Mixtral 8x7B Instruct",
                description="Mixtral 8x7B on Together AI",
                context_window=32768,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.6,
                output_price_per_1m_tokens=0.6,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in together_models:
            self._models[model.litellm_model_name] = model
    
    def _add_replicate_models(self):
        """Add Replicate models."""
        # Replicate models typically require specific version hashes
        # Users can add custom models via Replicate
        pass
    
    def _add_anyscale_models(self):
        """Add Anyscale models."""
        anyscale_models = [
            ModelInfo(
                provider=ProviderType.ANYSCALE,
                model_name="llama-2-70b-chat",
                litellm_model_name="anyscale/meta-llama/Llama-2-70b-chat-hf",
                display_name="Llama 2 70B Chat",
                description="Llama 2 70B on Anyscale",
                context_window=4096,
                max_output_tokens=4096,
                input_price_per_1m_tokens=1.0,
                output_price_per_1m_tokens=1.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in anyscale_models:
            self._models[model.litellm_model_name] = model
    
    def _add_deepinfra_models(self):
        """Add DeepInfra models."""
        deepinfra_models = [
            ModelInfo(
                provider=ProviderType.DEEPINFRA,
                model_name="llama-3-70b-instruct",
                litellm_model_name="deepinfra/meta-llama/Meta-Llama-3-70B-Instruct",
                display_name="Llama 3 70B Instruct",
                description="Llama 3 70B on DeepInfra",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.59,
                output_price_per_1m_tokens=0.79,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.DEEPINFRA,
                model_name="mixtral-8x7b-instruct",
                litellm_model_name="deepinfra/mistralai/Mixtral-8x7B-Instruct-v0.1",
                display_name="Mixtral 8x7B Instruct",
                description="Mixtral 8x7B on DeepInfra",
                context_window=32768,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.27,
                output_price_per_1m_tokens=0.27,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in deepinfra_models:
            self._models[model.litellm_model_name] = model
    
    def _add_ai21_models(self):
        """Add AI21 models."""
        ai21_models = [
            ModelInfo(
                provider=ProviderType.AI21,
                model_name="j2-ultra",
                litellm_model_name="ai21/j2-ultra",
                display_name="Jurassic-2 Ultra",
                description="AI21's most powerful model",
                context_window=8192,
                max_output_tokens=8192,
                input_price_per_1m_tokens=15.0,
                output_price_per_1m_tokens=15.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                ]
            ),
            ModelInfo(
                provider=ProviderType.AI21,
                model_name="j2-mid",
                litellm_model_name="ai21/j2-mid",
                display_name="Jurassic-2 Mid",
                description="AI21's balanced model",
                context_window=8192,
                max_output_tokens=8192,
                input_price_per_1m_tokens=10.0,
                output_price_per_1m_tokens=10.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                ]
            ),
        ]
        
        for model in ai21_models:
            self._models[model.litellm_model_name] = model
    
    def _add_nlp_cloud_models(self):
        """Add NLP Cloud models."""
        nlp_cloud_models = [
            ModelInfo(
                provider=ProviderType.NLP_CLOUD,
                model_name="dolphin",
                litellm_model_name="nlp_cloud/dolphin",
                display_name="Dolphin",
                description="NLP Cloud's Dolphin model",
                context_window=2048,
                max_output_tokens=2048,
                input_price_per_1m_tokens=25.0,
                output_price_per_1m_tokens=25.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                ]
            ),
        ]
        
        for model in nlp_cloud_models:
            self._models[model.litellm_model_name] = model
    
    def _add_voyage_models(self):
        """Add Voyage AI embedding models."""
        voyage_models = [
            ModelInfo(
                provider=ProviderType.VOYAGE,
                model_name="voyage-2",
                litellm_model_name="voyage/voyage-2",
                display_name="Voyage 2",
                description="Voyage AI's latest embedding model",
                context_window=4096,
                max_output_tokens=None,
                input_price_per_1m_tokens=0.1,
                output_price_per_1m_tokens=0.0,
                capabilities=[
                    ModelCapability.EMBEDDINGS,
                ]
            ),
        ]
        
        for model in voyage_models:
            self._models[model.litellm_model_name] = model
    
    def _add_xinference_models(self):
        """Add Xinference models."""
        # Xinference is for local deployment - models vary by installation
        pass
    
    def _add_perplexity_models(self):
        """Add Perplexity models."""
        perplexity_models = [
            ModelInfo(
                provider=ProviderType.PERPLEXITY,
                model_name="llama-3.1-sonar-small-128k-online",
                litellm_model_name="perplexity/llama-3.1-sonar-small-128k-online",
                display_name="Llama 3.1 Sonar Small Online",
                description="Small model with web search capabilities",
                context_window=127072,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.2,
                output_price_per_1m_tokens=0.2,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                    ModelCapability.WEB_SEARCH,
                ]
            ),
            ModelInfo(
                provider=ProviderType.PERPLEXITY,
                model_name="llama-3.1-sonar-large-128k-online",
                litellm_model_name="perplexity/llama-3.1-sonar-large-128k-online",
                display_name="Llama 3.1 Sonar Large Online",
                description="Large model with web search capabilities",
                context_window=127072,
                max_output_tokens=4096,
                input_price_per_1m_tokens=1.0,
                output_price_per_1m_tokens=1.0,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                    ModelCapability.WEB_SEARCH,
                ]
            ),
        ]
        
        for model in perplexity_models:
            self._models[model.litellm_model_name] = model
    
    def _add_deepseek_models(self):
        """Add DeepSeek models."""
        deepseek_models = [
            ModelInfo(
                provider=ProviderType.DEEPSEEK,
                model_name="deepseek-chat",
                litellm_model_name="deepseek/deepseek-chat",
                display_name="DeepSeek Chat",
                description="DeepSeek's chat model",
                context_window=32768,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.14,
                output_price_per_1m_tokens=0.28,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.DEEPSEEK,
                model_name="deepseek-coder",
                litellm_model_name="deepseek/deepseek-coder",
                display_name="DeepSeek Coder",
                description="DeepSeek's code generation model",
                context_window=16384,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.14,
                output_price_per_1m_tokens=0.28,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in deepseek_models:
            self._models[model.litellm_model_name] = model
    
    def _add_groq_models(self):
        """Add Groq models."""
        groq_models = [
            ModelInfo(
                provider=ProviderType.GROQ,
                model_name="llama3-8b-8192",
                litellm_model_name="groq/llama3-8b-8192",
                display_name="Llama 3 8B (Groq)",
                description="Ultra-fast Llama 3 8B on Groq",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.05,
                output_price_per_1m_tokens=0.08,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.GROQ,
                model_name="llama3-70b-8192",
                litellm_model_name="groq/llama3-70b-8192",
                display_name="Llama 3 70B (Groq)",
                description="Ultra-fast Llama 3 70B on Groq",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.59,
                output_price_per_1m_tokens=0.79,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.GROQ,
                model_name="mixtral-8x7b-32768",
                litellm_model_name="groq/mixtral-8x7b-32768",
                display_name="Mixtral 8x7B (Groq)",
                description="Ultra-fast Mixtral on Groq",
                context_window=32768,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.27,
                output_price_per_1m_tokens=0.27,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in groq_models:
            self._models[model.litellm_model_name] = model
    
    def _add_ollama_models(self):
        """Add Ollama models (for local deployment)."""
        ollama_models = [
            ModelInfo(
                provider=ProviderType.OLLAMA,
                model_name="llama3",
                litellm_model_name="ollama/llama3",
                display_name="Llama 3 (Local)",
                description="Local Llama 3 via Ollama",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.0,
                output_price_per_1m_tokens=0.0,
                requires_api_key=False,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OLLAMA,
                model_name="llama2",
                litellm_model_name="ollama/llama2",
                display_name="Llama 2 (Local)",
                description="Local Llama 2 via Ollama",
                context_window=4096,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.0,
                output_price_per_1m_tokens=0.0,
                requires_api_key=False,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OLLAMA,
                model_name="mistral",
                litellm_model_name="ollama/mistral",
                display_name="Mistral (Local)",
                description="Local Mistral via Ollama",
                context_window=8192,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.0,
                output_price_per_1m_tokens=0.0,
                requires_api_key=False,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
            ModelInfo(
                provider=ProviderType.OLLAMA,
                model_name="codellama",
                litellm_model_name="ollama/codellama",
                display_name="Code Llama (Local)",
                description="Local Code Llama via Ollama",
                context_window=4096,
                max_output_tokens=4096,
                input_price_per_1m_tokens=0.0,
                output_price_per_1m_tokens=0.0,
                requires_api_key=False,
                capabilities=[
                    ModelCapability.TEXT_COMPLETION,
                    ModelCapability.CHAT_COMPLETION,
                    ModelCapability.STREAMING,
                ]
            ),
        ]
        
        for model in ollama_models:
            self._models[model.litellm_model_name] = model
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all available models."""
        return list(self._models.values())
    
    def get_models_by_provider(self, provider: ProviderType) -> List[ModelInfo]:
        """Get models from a specific provider."""
        return [model for model in self._models.values() if model.provider == provider]
    
    def get_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """Get models that support a specific capability."""
        return [
            model for model in self._models.values()
            if capability in model.capabilities
        ]
    
    def get_models_without_api_key(self) -> List[ModelInfo]:
        """Get models that don't require API keys."""
        return [model for model in self._models.values() if not model.requires_api_key]
    
    def get_model_by_litellm_name(self, litellm_model_name: str) -> Optional[ModelInfo]:
        """Get a model by its LiteLLM name."""
        return self._models.get(litellm_model_name)
    
    def validate_model_access(self, model_name: str, available_keys: dict) -> tuple[bool, str]:
        """Validate that a model can be accessed with available API keys.
        
        Args:
            model_name: The model name to validate (can be model_name, litellm_model_name, display_name, or model_definition_id)
            available_keys: Dict of provider -> bool indicating available API keys
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Find the model
        model_info = None
        
        # First try direct lookup by litellm_model_name (most common case)
        model_info = self._models.get(model_name)
        
        if not model_info:
            # Try other lookups
            for model in self._models.values():
                # Generate the model definition ID for comparison
                model_definition_id = f"model_{model.model_name.replace('-', '_').replace('.', '_')}_{model.provider.value}"
                
                if (model.model_name == model_name or 
                    model.display_name == model_name or
                    model_definition_id == model_name):
                    model_info = model
                    break
        
        if not model_info:
            available_models = self._get_available_models_list(available_keys)
            return False, f"Model '{model_name}' not found. Available models: {', '.join(available_models[:5])}..."
        
        # Check if API key is required and available
        if model_info.requires_api_key:
            provider_key = model_info.provider.value
            if not available_keys.get(provider_key, False):
                return False, f"Model '{model_name}' requires {model_info.provider.value.title()} API key, but none is configured."
        
        return True, ""
    
    def _get_available_models_list(self, available_keys: dict) -> List[str]:
        """Get list of available model names based on configured API keys."""
        available_models = []
        for model in self._models.values():
            if not model.requires_api_key or available_keys.get(model.provider.value, False):
                available_models.append(model.litellm_model_name)
        return sorted(available_models)
    
    def get_available_models_for_keys(self, available_keys: dict) -> List[ModelInfo]:
        """Get models that can be used with the available API keys."""
        available_models = []
        for model in self._models.values():
            if not model.requires_api_key or available_keys.get(model.provider.value, False):
                available_models.append(model)
        return available_models
    
    def get_providers(self) -> List[ProviderType]:
        """Get all providers that have models."""
        return list(set(model.provider for model in self._models.values()))
    
    def get_capabilities(self) -> List[ModelCapability]:
        """Get all capabilities supported by any model."""
        capabilities = set()
        for model in self._models.values():
            capabilities.update(model.capabilities)
        return list(capabilities)
    
    def to_model_definitions(self) -> List[ModelDefinition]:
        """Convert model info to database model definitions."""
        definitions = []
        
        for model in self._models.values():
            definition = ModelDefinition(
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
            )
            definitions.append(definition)
        
        return definitions


# Global model catalog instance
model_catalog = ModelCatalogService()