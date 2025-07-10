"""
Schemas for model management and selection.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.provider import ModelCapability, ProviderType


class ProviderCredentialCreate(BaseModel):
    """Schema for creating provider credentials."""

    provider: ProviderType
    name: str
    credentials: dict[str, str] = Field(
        description="Provider credentials (will be encrypted before storage)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "name": "My OpenAI Production Key",
                "credentials": {
                    "api_key": "sk-..."
                }
            }
        }


class ProviderCredentialUpdate(BaseModel):
    """Schema for updating provider credentials."""

    name: str | None = None
    credentials: dict[str, str] | None = None
    is_active: bool | None = None


class ProviderCredentialResponse(BaseModel):
    """Schema for provider credential responses."""

    id: str
    provider: ProviderType
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None
    total_requests: int
    total_cost_usd: float | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "cred_123abc",
                "provider": "openai",
                "name": "My OpenAI Production Key",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_used_at": "2024-01-01T12:00:00Z",
                "total_requests": 150,
                "total_cost_usd": 12.34
            }
        }


class ModelDefinitionResponse(BaseModel):
    """Schema for model definition responses."""

    id: str
    provider: ProviderType
    model_name: str
    litellm_model_name: str
    display_name: str
    description: str | None = None
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_price_per_1m_tokens: float | None = None
    output_price_per_1m_tokens: float | None = None
    capabilities: list[ModelCapability]
    requires_api_key: bool
    requires_region: bool
    requires_project_id: bool
    is_active: bool

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "id": "model_gpt4_openai",
                "provider": "openai",
                "model_name": "gpt-4",
                "litellm_model_name": "openai/gpt-4",
                "display_name": "GPT-4",
                "description": "Most capable GPT-4 model",
                "context_window": 8192,
                "max_output_tokens": 4096,
                "input_price_per_1m_tokens": 30.0,
                "output_price_per_1m_tokens": 60.0,
                "capabilities": ["text_completion", "chat_completion", "function_calling"],
                "requires_api_key": True,
                "requires_region": False,
                "requires_project_id": False,
                "is_active": True
            }
        }


class ModelVariantCreate(BaseModel):
    """Schema for creating model variants."""

    model_definition_id: str
    provider_credential_id: str | None = None
    model_parameters: dict[str, Any] = Field(default_factory=dict)

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "model_definition_id": "model_gpt4_openai",
                "provider_credential_id": "cred_123abc",
                "model_parameters": {
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            }
        }


class ModelVariantResponse(BaseModel):
    """Schema for model variant responses."""

    id: str
    run_id: str
    variation_id: int
    model_definition_id: str
    provider_credential_id: str | None = None
    model_parameters: dict[str, Any]
    status: str
    output: str | None = None
    error_message: str | None = None
    tokens_used: int | None = None
    cost_usd: float | None = None
    response_time_ms: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "id": "variant_123abc",
                "run_id": "run_123abc",
                "variation_id": 0,
                "model_definition_id": "model_gpt4_openai",
                "provider_credential_id": "cred_123abc",
                "model_parameters": {"temperature": 0.7},
                "status": "completed",
                "output": "Generated response here...",
                "tokens_used": 150,
                "cost_usd": 0.004,
                "response_time_ms": 2500,
                "created_at": "2024-01-01T00:00:00Z",
                "started_at": "2024-01-01T00:00:05Z",
                "completed_at": "2024-01-01T00:00:10Z"
            }
        }


class ModelSelectionRequest(BaseModel):
    """Schema for model selection in runs."""

    model_variants: list[ModelVariantCreate] = Field(
        description="List of model variants to run"
    )

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "model_variants": [
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "provider_credential_id": "cred_openai_123",
                        "model_parameters": {"temperature": 0.7}
                    },
                    {
                        "model_definition_id": "model_claude_3_5_sonnet_anthropic",
                        "provider_credential_id": "cred_anthropic_456",
                        "model_parameters": {"temperature": 0.5}
                    },
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "provider_credential_id": "cred_openai_123",
                        "model_parameters": {"temperature": 0.9}
                    }
                ]
            }
        }
    }


class ProviderSummary(BaseModel):
    """Schema for provider summary information."""

    provider: ProviderType
    display_name: str
    description: str
    requires_api_key: bool
    model_count: int
    user_has_credentials: bool

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "provider": "openai",
                "display_name": "OpenAI",
                "description": "Leading AI research company",
                "requires_api_key": True,
                "model_count": 8,
                "user_has_credentials": True
            }
        }
    }


class ModelCatalogResponse(BaseModel):
    """Schema for model catalog responses."""

    providers: list[ProviderSummary]
    models: list[ModelDefinitionResponse]
    capabilities: list[ModelCapability]

    class Config:
        json_schema_extra = {
            "example": {
                "providers": [
                    {
                        "provider": "openai",
                        "display_name": "OpenAI",
                        "description": "Leading AI research company",
                        "requires_api_key": True,
                        "model_count": 8,
                        "user_has_credentials": True
                    }
                ],
                "models": [
                    {
                        "id": "model_gpt4_openai",
                        "provider": "openai",
                        "model_name": "gpt-4",
                        "display_name": "GPT-4",
                        "capabilities": ["text_completion", "chat_completion"]
                    }
                ],
                "capabilities": ["text_completion", "chat_completion", "vision"]
            }
        }


class ModelRecommendation(BaseModel):
    """Schema for model recommendations."""

    model_definition_id: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "model_definition_id": "model_gpt4_openai",
                "confidence_score": 0.85,
                "reasoning": "GPT-4 is excellent for code analysis and complex reasoning tasks"
            }
        }
    }


class ModelRecommendationRequest(BaseModel):
    """Schema for requesting model recommendations."""

    prompt: str
    task_type: str | None = None
    budget_preference: str | None = Field(None, pattern="^(low|medium|high)$")
    performance_preference: str | None = Field(None, pattern="^(speed|quality|balanced)$")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Analyze this Python code and suggest improvements",
                "task_type": "code_analysis",
                "budget_preference": "medium",
                "performance_preference": "quality"
            }
        }


class ModelRecommendationResponse(BaseModel):
    """Schema for model recommendation responses."""

    recommendations: list[ModelRecommendation]
    explanation: str

    class Config:
        json_schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "confidence_score": 0.85,
                        "reasoning": "GPT-4 is excellent for code analysis"
                    }
                ],
                "explanation": "Based on your code analysis task, these models are recommended for their strong reasoning capabilities."
            }
        }
