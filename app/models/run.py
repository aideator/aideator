from datetime import datetime
from enum import Enum

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
    agent_config: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # User information
    user_id: str | None = Field(default=None, index=True)
    api_key_id: str | None = Field(default=None, index=True)

    # Results
    results: dict = Field(default_factory=dict, sa_column=Column(JSON))
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
    output_type: str = Field(default="stdout")  # stdout, stderr, system

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
