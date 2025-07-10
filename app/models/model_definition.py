"""
Database models for LiteLLM model definitions.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import JSON, Index, Column
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
    
    # Primary key - using LiteLLM's model name as unique identifier
    model_name: str = Field(primary_key=True, description="LiteLLM model name (e.g., 'gpt-4', 'claude-3-opus')")
    
    # From LiteLLM proxy discovery
    litellm_provider: str = Field(description="Provider as determined by LiteLLM (e.g., 'openai', 'anthropic')")
    display_name: str = Field(description="Human-friendly display name")
    max_tokens: Optional[int] = Field(default=None, description="Maximum total tokens")
    max_input_tokens: Optional[int] = Field(default=None, description="Maximum input tokens")
    max_output_tokens: Optional[int] = Field(default=None, description="Maximum output tokens")
    input_cost_per_token: Optional[float] = Field(default=None, description="Cost per input token in USD")
    output_cost_per_token: Optional[float] = Field(default=None, description="Cost per output token in USD")
    supports_function_calling: bool = Field(default=False)
    supports_vision: bool = Field(default=False)
    supports_streaming: bool = Field(default=True)
    
    # Our enriched metadata
    description: Optional[str] = Field(default=None, description="Detailed description for UI")
    category: Optional[str] = Field(default=None, description="Category like 'general', 'code', 'vision'")
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_recommended: bool = Field(default=False, description="Whether we recommend this model")
    is_popular: bool = Field(default=False, description="Whether this is a popular model")
    requires_api_key: bool = Field(default=True, description="Whether an API key is required")
    api_key_env_var: Optional[str] = Field(default=None, description="Environment variable name for API key")
    
    # Tracking fields
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Whether this model is currently available")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
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
    
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    status: str = Field(description="success, failed, or in_progress")
    models_discovered: int = Field(default=0)
    models_added: int = Field(default=0)
    models_updated: int = Field(default=0)
    models_deactivated: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    __table_args__ = (
        {"extend_existing": True}
    )