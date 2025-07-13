from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, SQLModel


class ProviderType(str, Enum):
    """Provider type enumeration."""

    # Main providers
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GEMINI = "GEMINI"
    VERTEX_AI = "VERTEX_AI"
    BEDROCK = "BEDROCK"
    MISTRAL = "MISTRAL"
    COHERE = "COHERE"

    # Cloud providers
    AZURE = "AZURE"

    # Specialized providers (only ones actually used in the codebase)
    HUGGINGFACE = "HUGGINGFACE"
    TOGETHER = "TOGETHER"
    GROQ = "GROQ"
    DEEPSEEK = "DEEPSEEK"
    PERPLEXITY = "PERPLEXITY"
    OLLAMA = "OLLAMA"


class ModelCapability(str, Enum):
    """Model capability enumeration."""

    TEXT_COMPLETION = "text_completion"
    CHAT_COMPLETION = "chat_completion"
    VISION = "vision"
    EMBEDDINGS = "embeddings"  # Used in model_catalog.py
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"


class ProviderCredential(SQLModel, table=True):
    """Database model for provider API credentials."""

    __tablename__ = "provider_credentials"

    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    provider: ProviderType = Field(
        sa_column=Column(SQLEnum(ProviderType), nullable=False, index=True)
    )
    name: str  # User-friendly name like "My OpenAI Key"

    # Encrypted credentials
    encrypted_credentials: dict[str, str] = Field(sa_column=Column(JSON))

    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = Field(default=None)

    # Usage tracking
    total_requests: int = Field(default=0)
    total_cost_usd: float | None = Field(default=None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "cred_123abc",
                "user_id": "user_123abc",
                "provider": "openai",
                "name": "My OpenAI Production Key",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
            }
        }


class ModelDefinition(SQLModel, table=True):
    """Database model for available models."""

    __tablename__ = "model_definitions"

    id: str = Field(primary_key=True)
    provider: ProviderType = Field(
        sa_column=Column(SQLEnum(ProviderType), nullable=False, index=True)
    )
    model_name: str = Field(index=True)  # e.g., "gpt-4", "claude-3-sonnet"
    litellm_model_name: str = Field(
        index=True
    )  # e.g., "openai/gpt-4", "anthropic/claude-3-sonnet"
    display_name: str  # Human-friendly name
    description: str | None = Field(default=None)

    # Model characteristics
    context_window: int | None = Field(default=None)
    max_output_tokens: int | None = Field(default=None)

    # Pricing (per 1M tokens)
    input_price_per_1m_tokens: float | None = Field(default=None)
    output_price_per_1m_tokens: float | None = Field(default=None)

    # Capabilities
    capabilities: list[ModelCapability] = Field(
        default_factory=list, sa_column=Column(JSON)
    )

    # Authentication requirements
    requires_api_key: bool = Field(default=True)
    requires_region: bool = Field(default=False)
    requires_project_id: bool = Field(default=False)

    # Configuration
    default_parameters: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "id": "model_gpt4",
                "provider": "openai",
                "model_name": "gpt-4",
                "litellm_model_name": "openai/gpt-4",
                "display_name": "GPT-4",
                "description": "Most capable GPT-4 model",
                "context_window": 8192,
                "max_output_tokens": 4096,
                "input_price_per_1m_tokens": 30.0,
                "output_price_per_1m_tokens": 60.0,
                "capabilities": [
                    "text_completion",
                    "chat_completion",
                    "function_calling",
                ],
                "requires_api_key": True,
                "is_active": True,
            }
        }


class ModelVariant(SQLModel, table=True):
    """Database model for model variants in a comparison run."""

    __tablename__ = "model_variants"

    id: str = Field(primary_key=True)
    task_id: int = Field(foreign_key="runs.task_id", index=True)
    variation_id: int = Field(index=True)
    model_definition_id: str = Field(
        foreign_key="model_definitions.model_name", index=True
    )
    provider_credential_id: str | None = Field(
        foreign_key="provider_credentials.id", default=None, index=True
    )

    # Runtime configuration
    model_parameters: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Results
    status: str = Field(default="pending")  # pending, running, completed, failed
    output: str | None = Field(default=None)
    error_message: str | None = Field(default=None)

    # Metrics
    tokens_used: int | None = Field(default=None)
    cost_usd: float | None = Field(default=None)
    response_time_ms: int | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    class Config:
        """Pydantic config."""

        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "id": "variant_123abc",
                "task_id": 1,
                "variation_id": 0,
                "model_definition_id": "model_gpt4",
                "provider_credential_id": "cred_123abc",
                "status": "completed",
                "tokens_used": 150,
                "cost_usd": 0.004,
                "response_time_ms": 2500,
            }
        }
