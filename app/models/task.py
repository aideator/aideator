from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column, Integer, String
from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(SQLModel, table=True):
    """
    Unified Task model - replaces the run/task duality.
    
    A task represents a user's request to analyze a repository.
    Each task can have multiple agent variations (0, 1, 2, etc.).
    """

    __tablename__ = "tasks"

    # Primary key - simple auto-incrementing ID
    id: int | None = Field(
        default=None,
        sa_column=Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
    )

    # Core task definition
    github_url: str = Field(index=True)
    prompt: str
    agent_mode: str = Field(default="claude-cli")
    
    # Execution configuration
    variations: int = Field(default=1, description="Number of model variations to run")
    model_configs: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Status tracking
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_column=Column("status", String, nullable=False, index=True)
    )
    archived: bool = Field(default=False, index=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # User association
    user_id: str | None = Field(default=None, index=True)
    
    # Results and metadata
    results: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    task_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON))
    error_message: str | None = Field(default=None)

    # Statistics
    total_tokens_used: int | None = Field(default=None)
    total_cost_usd: float | None = Field(default=None)
    
    # Legacy support for Kubernetes job names (internal use)
    internal_run_id: str | None = Field(default=None, sa_column=Column("internal_run_id", String))

    class Config:
        json_schema_extra = {
            "example": {
                "id": 7,
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "What is the main FastAPI class?",
                "agent_mode": "claude-cli",
                "variations": 1,
                "status": "pending",
            }
        }


class TaskOutput(SQLModel, table=True):
    """
    Task outputs from agent execution.
    
    Each output belongs to a specific variation (0, 1, 2, etc.) within a task.
    """

    __tablename__ = "task_outputs"

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    variation_id: int = Field(default=0, index=True)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    output_type: str = Field(default="stdout")  # stdout, stderr, assistant_response, job_data, error, debug
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": 7,
                "variation_id": 0,
                "content": "The main FastAPI class is...",
                "output_type": "assistant_response"
            }
        }