from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
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
    provider: str = Field(index=True)
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


# Removed ModelDefinition and ModelVariant - no LiteLLM functionality needed
