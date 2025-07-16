"""Schemas for task list responses (replacing mock sessions data)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import get_settings

settings = get_settings()


class AgentConfig(BaseModel):
    """Configuration for AI agents."""

    model: str = Field(
        default=settings.default_agent_model,
        description="Model to use for the agent",
        examples=["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for model generation",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=8192,
        description="Maximum tokens to generate",
    )
    system_prompt: str | None = Field(
        None,
        description="Optional system prompt to prepend",
    )
    stop_sequences: list[str] | None = Field(
        None,
        description="Stop sequences for generation",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model": "claude-3-opus-20240229",
                "temperature": 0.7,
                "max_tokens": 4096,
            }
        }
    }


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


class CreateTaskRequest(BaseModel):
    """Request body for creating a new task."""

    github_url: str = Field(..., description="Public Git repository URL")
    prompt: str = Field(..., min_length=10, description="LLM prompt for agents")
    model_names: list[str] = Field(
        default=["gpt-4o-mini"],
        min_length=1,
        max_length=6,
        description="List of model names (one per variation)",
    )
    agent_mode: str | None = Field(
        default="claude-cli",
        description="Execution mode for agents (claude-cli, gemini-cli, litellm, etc.)",
    )
    variations: int | None = Field(
        default=None,
        ge=1,
        le=6,
        description="Override number of variations (defaults to len(model_names))",
    )


class CreateTaskResponse(BaseModel):
    """Response payload after task creation."""

    task_id: int = Field(..., description="Primary key of the new task")
    websocket_url: str = Field(..., description="WebSocket stream for live outputs")
    polling_url: str = Field(..., description="HTTP polling endpoint for outputs")
    status: Literal["pending"] = Field("pending", description="Initial status")
