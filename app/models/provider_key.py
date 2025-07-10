"""
Database models for secure provider API key storage.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import JSON, Column, Field, SQLModel


class ProviderAPIKeyDB(SQLModel, table=True):
    """Secure storage for user's provider API keys.
    
    This table stores encrypted API keys for various LLM providers (OpenAI, Anthropic, etc).
    Keys are encrypted at rest and can be configured at provider or model level.
    """
    __tablename__ = "provider_api_keys"

    model_config = {
        "protected_namespaces": ()
    }

    # Primary key
    id: str = Field(primary_key=True, description="Unique identifier, format: provkey_xxx")

    # Ownership
    user_id: str = Field(foreign_key="users.id", nullable=False, index=True)

    # Provider configuration
    provider: str = Field(nullable=False, index=True, description="Provider name: openai, anthropic, etc")
    model_name: str | None = Field(default=None, index=True, description="Optional: specific model override")

    # Encrypted storage
    encrypted_key: str = Field(nullable=False, description="Fernet-encrypted API key")
    key_hint: str = Field(nullable=False, description="Last 4 chars for UI display: ...abc123")
    encryption_version: int = Field(default=1, description="Encryption algorithm version")

    # Metadata
    name: str | None = Field(default=None, description="User-friendly name for this key")
    description: str | None = Field(default=None, description="Optional description")

    # Status and tracking
    is_active: bool = Field(default=True, index=True)
    is_valid: bool | None = Field(default=None, description="Last validation status")
    last_validated_at: datetime | None = Field(default=None)
    last_used_at: datetime | None = Field(default=None)
    last_error: str | None = Field(default=None, description="Last error message if validation failed")

    # Usage metrics
    total_requests: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None, description="Optional expiration date")

    # Additional settings
    extra_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    __table_args__ = (
        # Ensure one active key per provider per user (when model_name is null)
        UniqueConstraint("user_id", "provider", "model_name", "is_active",
                        name="unique_active_provider_key"),
        Index("idx_provider_key_lookup", "user_id", "provider", "is_active"),
        Index("idx_provider_key_model", "user_id", "model_name", "is_active"),
        {"extend_existing": True}
    )


class ProviderAPIKeyAuditLog(SQLModel, table=True):
    """Audit log for provider API key operations."""
    __tablename__ = "provider_api_key_audit_logs"

    id: str = Field(primary_key=True, description="Unique identifier")
    user_id: str = Field(foreign_key="users.id", nullable=False, index=True)
    provider_key_id: str = Field(foreign_key="provider_api_keys.id", nullable=False, index=True)

    action: str = Field(nullable=False, description="Action: created, updated, deleted, used, validated")
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    ip_address: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_user_time", "user_id", "created_at"),
        Index("idx_audit_key_time", "provider_key_id", "created_at"),
    )
