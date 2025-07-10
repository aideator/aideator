"""
Database models for LiteLLM model definitions.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Index
from sqlmodel import Field, SQLModel


class ModelDefinitionDB(SQLModel, table=True):
    """Database model for storing LiteLLM model definitions.
    
    This table stores model information discovered from the LiteLLM proxy,
    enriched with our own metadata for better UX.
    """
    __tablename__ = "model_definitions"

    model_config = {
        "protected_namespaces": ()
    }

    # Primary key - auto-incrementing ID for better database performance
    id: int | None = Field(default=None, primary_key=True)

    # Core model identification
    model_name: str = Field(unique=True, index=True, description="LiteLLM model name (e.g., 'gpt-4', 'claude-3-opus')")
    provider: str = Field(description="Model provider (e.g., 'openai', 'anthropic')")
    litellm_model_name: str = Field(description="Full LiteLLM model identifier")
    litellm_provider: str = Field(description="Provider as determined by LiteLLM")

    # Display information
    display_name: str = Field(description="Human-friendly display name")
    description: str | None = Field(default=None, description="Detailed description for UI")

    # Model capabilities and limits
    context_window: int | None = Field(default=None, description="Context window size")
    max_tokens: int | None = Field(default=None, description="Maximum total tokens")
    max_input_tokens: int | None = Field(default=None, description="Maximum input tokens")
    max_output_tokens: int | None = Field(default=None, description="Maximum output tokens")

    # Pricing information
    input_price_per_1m_tokens: float | None = Field(default=None, description="Cost per 1M input tokens in USD")
    output_price_per_1m_tokens: float | None = Field(default=None, description="Cost per 1M output tokens in USD")
    input_cost_per_token: float | None = Field(default=None, description="Cost per input token in USD")
    output_cost_per_token: float | None = Field(default=None, description="Cost per output token in USD")

    # Capabilities
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_streaming: bool = Field(default=True)

    # Configuration requirements
    requires_api_key: bool = Field(default=True, description="Whether an API key is required")
    requires_region: bool = Field(default=False, description="Whether a region is required")
    requires_project_id: bool = Field(default=False, description="Whether a project ID is required")
    api_key_env_var: str | None = Field(default=None, description="Environment variable name for API key")
    default_parameters: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # UI and recommendation metadata
    category: str | None = Field(default=None, description="Category like 'general', 'code', 'vision'")
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_recommended: bool = Field(default=False, description="Whether we recommend this model")
    is_popular: bool = Field(default=False, description="Whether this is a popular model")

    # Status and tracking
    is_active: bool = Field(default=True, description="Whether this model is currently available")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)

    # Additional metadata
    extra_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Indexes for common queries
    __table_args__ = (
        Index("idx_model_provider", "litellm_provider"),
        Index("idx_model_active", "is_active"),
        Index("idx_model_category", "category"),
        {"extend_existing": True}
    )


class ModelSyncLog(SQLModel, table=True):
    """Log of model synchronization runs."""
    __tablename__ = "model_sync_logs"

    id: int | None = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)
    status: str = Field(description="success, failed, or in_progress")
    models_discovered: int = Field(default=0)
    models_added: int = Field(default=0)
    models_updated: int = Field(default=0)
    models_deactivated: int = Field(default=0)
    error_message: str | None = Field(default=None)
    extra_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    __table_args__ = (
        {"extend_existing": True}
    )
