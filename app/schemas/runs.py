from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.core.config import get_settings
from app.models.run import RunStatus
# Removed LiteLLM model schemas - using simple model names now

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


class CreateRunRequest(BaseModel):
    """Request to create a new agent run."""

    github_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL",
        examples=["https://github.com/fastapi/fastapi"],
    )
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=settings.max_prompt_length,
        description="Prompt for the LLM agents",
        examples=["Add comprehensive error handling to all API endpoints"],
    )

    # Multiple model variants for comparison
    model_names: list[str] = Field(
        default=["claude-3-5-sonnet"],
        description="List of models to run in parallel for comparison",
        examples=[["claude-3-5-sonnet", "gpt-4o-mini", "gemini-pro"]],
        min_length=1,
        max_length=6,
    )
    use_claude_code: bool = Field(
        default=False,
        description="Use Claude Code CLI instead of basic Claude API",
    )
    agent_mode: str | None = Field(
        default="claude-cli",
        description="Agent execution mode: 'litellm', 'claude-cli', 'gemini-cli', or 'openai-codex'",
        examples=["claude-cli", "litellm", "gemini-cli", "openai-codex"],
    )

    # Removed session and turn management - runs are standalone now

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure URL is from allowed Git hosts."""
        url_str = str(v)
        allowed = any(
            url_str.startswith(f"https://{host}/")
            for host in settings.allowed_git_hosts
        )
        if not allowed:
            raise ValueError(
                f"URL must be from allowed hosts: {', '.join(settings.allowed_git_hosts)}"
            )
        return v

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Clean and validate prompt."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Prompt must be at least 10 characters after trimming")
        return v

    @field_validator("agent_mode")
    @classmethod
    def validate_agent_mode(cls, v: str | None) -> str:
        """Validate agent mode."""
        valid_modes = ["litellm", "claude-cli", "gemini-cli", "openai-codex"]
        if v not in [*valid_modes, None]:
            raise ValueError(f"Agent mode must be one of: {', '.join(valid_modes)}")
        return v or "claude-cli"

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "Add comprehensive error handling to all API endpoints",
                "model_names": ["claude-3-5-sonnet", "gpt-4o-mini"],
            }
        },
    }


class CreateRunResponse(BaseModel):
    """Response after creating a run."""

    task_id: int = Field(..., description="User-facing task identifier")
    run_id: str = Field(..., description="Kubernetes job identifier")
    websocket_url: str = Field(..., description="WebSocket URL for real-time streaming")
    stream_url: str = Field(
        ..., description="Stream URL for real-time streaming (alias for websocket_url)"
    )
    polling_url: str = Field(..., description="HTTP polling endpoint for outputs")
    status: str = Field(..., description="Initial status of the run")
    estimated_duration_seconds: int = Field(
        ..., description="Estimated time to complete"
    )
    # Removed session_id and turn_id - runs are standalone now

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "task_id": 1,
                "run_id": "run_1234567890abcdef",
                "websocket_url": "ws://localhost:8000/ws/tasks/1",
                "stream_url": "ws://localhost:8000/ws/tasks/1",
                "polling_url": "/api/v1/runs/1/outputs",
                "status": "accepted",
                "estimated_duration_seconds": 120,
                # Removed session/turn references
            }
        },
    }


class RunDetails(BaseModel):
    """Detailed information about a run."""

    id: str = Field(..., description="Unique identifier")
    github_url: str = Field(..., description="Repository URL")
    prompt: str = Field(..., description="Agent prompt")
    model_names: list[str] = Field(..., description="Models used in this run")
    status: RunStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    results: dict[str, Any] = Field(default_factory=dict, description="Run results")
    total_tokens_used: int | None = Field(None, description="Total tokens consumed")
    total_cost_usd: float | None = Field(None, description="Total cost in USD")

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "id": "run_1234567890abcdef",
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "Add error handling",
                "model_names": ["claude-3-5-sonnet", "gpt-4o-mini"],
                "status": "completed",
                "created_at": "2024-01-01T00:00:00Z",
                "started_at": "2024-01-01T00:00:10Z",
                "completed_at": "2024-01-01T00:02:00Z",
                "results": {"outputs": []},
                "total_tokens_used": 12500,
                "total_cost_usd": 0.25,
            }
        },
    }


class RunListItem(BaseModel):
    """Summary information for run listings."""

    id: str
    github_url: str
    prompt: str
    model_count: int = Field(..., description="Number of model variants")
    status: RunStatus
    created_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def model_validate(cls, obj):
        """Custom validation to map variations to model_count."""
        if hasattr(obj, "variations") and not hasattr(obj, "model_count"):
            # Convert Run model to dict and map variations to model_count
            if hasattr(obj, "__dict__"):
                data = {**obj.__dict__}
                data["model_count"] = data.get("variations", 0)
            else:
                data = dict(obj)
                data["model_count"] = data.get("variations", 0)
            return super().model_validate(data)
        return super().model_validate(obj)

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),  # Allow model_ prefixed fields
    }


# Removed SelectWinnerRequest - no variation comparison needed
