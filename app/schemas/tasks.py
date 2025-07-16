"""Schemas for task list responses (replacing mock sessions data)."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.task import TaskStatus


class TaskListItem(BaseModel):
    """Task item for the main page list (maps to frontend 'sessions' format)."""

    id: str = Field(description="Unique task/run identifier")
    title: str = Field(description="Human-readable task title (truncated prompt)")
    details: str = Field(description="Timestamp and repository info")
    status: Literal["Completed", "Open", "Failed"] = Field(description="Task outcome status")
    versions: int | None = Field(None, description="Number of agent variations")
    additions: int | None = Field(None, description="Total lines added")
    deletions: int | None = Field(None, description="Total lines deleted")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "run-abc123",
                "title": "Make hello world label more ominous",
                "details": "8:15 PM · aideator/helloworld",
                "status": "Completed",
                "versions": 3,
                "additions": 5,
                "deletions": 2
            }
        }


class TaskListResponse(BaseModel):
    """Response containing list of tasks for the main page."""

    tasks: list[TaskListItem] = Field(description="List of user tasks")
    total: int = Field(description="Total number of tasks")
    has_more: bool = Field(description="Whether more tasks are available")

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "id": "run-abc123",
                        "title": "Make hello world label more ominous",
                        "details": "8:15 PM · aideator/helloworld",
                        "status": "Completed",
                        "versions": 3,
                        "additions": 5,
                        "deletions": 2
                    }
                ],
                "total": 15,
                "has_more": True
            }
        }


# New unified task schemas
class ModelVariant(BaseModel):
    """Model variant configuration for task execution."""
    model_definition_id: str = Field(..., description="Model identifier")
    custom_params: dict[str, Any] = Field(default_factory=dict)


class TaskCreate(BaseModel):
    """Task creation request."""
    github_url: str = Field(..., description="GitHub repository URL")
    prompt: str = Field(..., description="Analysis prompt")
    agent_mode: str = Field(default="claude-cli", description="Agent execution mode")
    model_variants: list[ModelVariant] = Field(..., min_items=1, max_items=5)

    class Config:
        json_schema_extra = {
            "example": {
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "What is the main FastAPI class and how does routing work?",
                "agent_mode": "claude-cli",
                "model_variants": [
                    {"model_definition_id": "claude-3-5-sonnet-20241022"}
                ]
            }
        }


class TaskResponse(BaseModel):
    """Task response for API calls."""
    id: int = Field(..., description="Task ID")
    github_url: str
    prompt: str
    agent_mode: str
    status: TaskStatus
    variations: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: dict[str, Any] = Field(default_factory=dict)
    task_metadata: dict[str, Any] = Field(default_factory=dict)
    total_tokens_used: int | None = None
    total_cost_usd: float | None = None
    error_message: str | None = None
    polling_url: str
    websocket_url: str | None = None
    estimated_duration_seconds: int | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": 7,
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "What is the main FastAPI class?",
                "agent_mode": "claude-cli",
                "status": "running",
                "variations": 1,
                "created_at": "2025-07-16T05:41:29.336044+00:00",
                "polling_url": "/api/v1/tasks/7/outputs"
            }
        }


class TaskOutputResponse(BaseModel):
    """Task output response."""
    id: int
    task_id: int
    variation_id: int
    content: str
    timestamp: datetime
    output_type: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "task_id": 7,
                "variation_id": 0,
                "content": "The main FastAPI class is...",
                "timestamp": "2025-07-16T05:41:29.336044+00:00",
                "output_type": "assistant_response"
            }
        }
