from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, SQLModel


class RunStatus(str, Enum):
    """Run status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Run(SQLModel, table=True):
    """Database model for agent runs."""

    __tablename__ = "runs"

    id: str = Field(primary_key=True)
    github_url: str = Field(index=True)
    prompt: str
    variations: int
    status: RunStatus = Field(
        default=RunStatus.PENDING,
        sa_column=Column(SQLEnum(RunStatus), nullable=False, index=True),
    )
    winning_variation_id: int | None = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # Configuration
    agent_config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # User information
    user_id: str | None = Field(default=None, index=True)
    api_key_id: str | None = Field(default=None, index=True)

    # Turn association
    session_id: str | None = Field(default=None, index=True)
    turn_id: str | None = Field(default=None, index=True)

    # Results
    results: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    error_message: str | None = Field(default=None)

    # Statistics
    total_tokens_used: int | None = Field(default=None)
    total_cost_usd: float | None = Field(default=None)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "run_123abc",
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "Add comprehensive error handling",
                "variations": 3,
                "status": "running",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }


class AgentOutput(SQLModel, table=True):
    """Database model for agent outputs."""

    __tablename__ = "agent_outputs"

    id: int = Field(primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    variation_id: int = Field(index=True)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    output_type: str = Field(
        default="stdout"
    )  # stdout, stderr, system, status, summary, diffs, logging, addinfo

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": 1,
                "run_id": "run_123abc",
                "variation_id": 0,
                "content": "[Agent 0] Analyzing repository...",
                "timestamp": "2024-01-01T00:00:00Z",
                "output_type": "stdout",
            }
        }


class LiteLLMAnalytics(SQLModel, table=True):
    """Database model for LiteLLM analytics data."""

    __tablename__ = "litellm_analytics"

    id: int = Field(primary_key=True)
    run_id: str = Field(foreign_key="runs.id", index=True)
    variation_id: int = Field(index=True)
    
    # Request metadata
    request_id: str | None = Field(default=None, index=True)
    model: str = Field(index=True)
    provider: str = Field(index=True)
    
    # Token usage
    prompt_tokens: int | None = Field(default=None)
    completion_tokens: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
    
    # Cost tracking
    cost_usd: float | None = Field(default=None)
    input_cost_per_token: float | None = Field(default=None)
    output_cost_per_token: float | None = Field(default=None)
    
    # Performance metrics
    response_time_ms: int | None = Field(default=None)
    time_to_first_token_ms: int | None = Field(default=None)
    tokens_per_second: float | None = Field(default=None)
    
    # Request details
    temperature: float | None = Field(default=None)
    max_tokens: int | None = Field(default=None)
    stream: bool = Field(default=False)
    
    # Status and errors
    status: str = Field(default="success")  # success, error, timeout
    error_type: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    
    # Timestamps
    request_start_time: datetime | None = Field(default=None, index=True)
    request_end_time: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Raw LiteLLM data
    litellm_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": 1,
                "run_id": "run_123abc",
                "variation_id": 0,
                "request_id": "req_abc123",
                "model": "gpt-4o-mini",
                "provider": "openai",
                "prompt_tokens": 150,
                "completion_tokens": 80,
                "total_tokens": 230,
                "cost_usd": 0.0023,
                "response_time_ms": 2500,
                "temperature": 0.7,
                "status": "success",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }
