from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column, Enum as SQLEnum
from sqlmodel import Field, SQLModel


class ProviderType(str, Enum):
    """Provider type enumeration."""

    # Main providers
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    VERTEX_AI = "vertex_ai"
    BEDROCK = "bedrock"
    MISTRAL = "mistral"
    COHERE = "cohere"
    
    # Cloud providers
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    
    # Specialized providers
    HUGGINGFACE = "huggingface"
    REPLICATE = "replicate"
    OLLAMA = "ollama"
    NVIDIA_NIM = "nvidia_nim"
    
    # Other providers
    DEEPINFRA = "deepinfra"
    FIREWORKS = "fireworks"
    TOGETHER = "together"
    GROQ = "groq"
    XAI = "xai"
    VOYAGE = "voyage"
    PERPLEXITY = "perplexity"
    ANYSCALE = "anyscale"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    SAMBANOVA = "sambanova"
    NEBIUS = "nebius"
    PREDIBASE = "predibase"
    VLLM = "vllm"
    GALADRIEL = "galadriel"
    AI21 = "ai21"
    BASETEN = "baseten"
    CLOUDFLARE = "cloudflare"
    DATABRICKS = "databricks"
    TRITON = "triton"
    SAGEMAKER = "sagemaker"
    PALM = "palm"
    WATSON = "watson"
    MARITALK = "maritalk"
    NLP_CLOUD = "nlp_cloud"
    ALEPH_ALPHA = "aleph_alpha"
    PETALS = "petals"
    CLARIFAI = "clarifai"
    CUSTOM = "custom"


class ModelCapability(str, Enum):
    """Model capability enumeration."""

    TEXT_COMPLETION = "text_completion"
    CHAT_COMPLETION = "chat_completion"
    VISION = "vision"
    EMBEDDING = "embedding"
    EMBEDDINGS = "embeddings"  # Some providers use plural
    AUDIO_INPUT = "audio_input"
    AUDIO_OUTPUT = "audio_output"
    IMAGE_GENERATION = "image_generation"
    WEB_SEARCH = "web_search"
    FUNCTION_CALLING = "function_calling"
    ASSISTANT_PREFILL = "assistant_prefill"
    JSON_SCHEMA = "json_schema"
    PDF_INPUT = "pdf_input"
    STREAMING = "streaming"
    PARALLEL_TOOL_CALLS = "parallel_tool_calls"


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
    encrypted_credentials: dict = Field(sa_column=Column(JSON))
    
    # Metadata
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)
    
    # Usage tracking
    total_requests: int = Field(default=0)
    total_cost_usd: Optional[float] = Field(default=None)
    
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
    litellm_model_name: str = Field(index=True)  # e.g., "openai/gpt-4", "anthropic/claude-3-sonnet"
    display_name: str  # Human-friendly name
    description: Optional[str] = Field(default=None)
    
    # Model characteristics
    context_window: Optional[int] = Field(default=None)
    max_output_tokens: Optional[int] = Field(default=None)
    
    # Pricing (per 1M tokens)
    input_price_per_1m_tokens: Optional[float] = Field(default=None)
    output_price_per_1m_tokens: Optional[float] = Field(default=None)
    
    # Capabilities
    capabilities: list[ModelCapability] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )
    
    # Authentication requirements
    requires_api_key: bool = Field(default=True)
    requires_region: bool = Field(default=False)
    requires_project_id: bool = Field(default=False)
    
    # Configuration
    default_parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
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
                "capabilities": ["text_completion", "chat_completion", "function_calling"],
                "requires_api_key": True,
                "is_active": True,
            }
        }


class ModelVariant(SQLModel, table=True):
    """Database model for model variants in a comparison run."""

    __tablename__ = "model_variants"

    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    variation_id: int = Field(index=True)
    model_definition_id: str = Field(foreign_key="model_definitions.id", index=True)
    provider_credential_id: Optional[str] = Field(
        foreign_key="provider_credentials.id", 
        default=None,
        index=True
    )
    
    # Runtime configuration
    model_parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Results
    status: str = Field(default="pending")  # pending, running, completed, failed
    output: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    
    # Metrics
    tokens_used: Optional[int] = Field(default=None)
    cost_usd: Optional[float] = Field(default=None)
    response_time_ms: Optional[int] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    class Config:
        """Pydantic config."""

        protected_namespaces = ()
        json_schema_extra = {
            "example": {
                "id": "variant_123abc",
                "run_id": "run_123abc",
                "variation_id": 0,
                "model_definition_id": "model_gpt4",
                "provider_credential_id": "cred_123abc",
                "status": "completed",
                "tokens_used": 150,
                "cost_usd": 0.004,
                "response_time_ms": 2500,
            }
        }