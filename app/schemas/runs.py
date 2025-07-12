from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.core.config import get_settings
from app.models.run import RunStatus
from app.schemas.models import ModelVariantCreate, ModelVariantResponse

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

    # Model selection system
    model_variants: list[ModelVariantCreate] = Field(
        ...,
        description="List of model variants to run in parallel",
        min_length=1,
        max_length=settings.max_variations,
    )
    use_claude_code: bool = Field(
        default=False,
        description="Use Claude Code CLI instead of basic Claude API",
    )
    agent_mode: str | None = Field(
        default="litellm",
        description="Agent execution mode: 'litellm', 'claude-cli', 'gemini-cli', or 'openai-codex'",
        examples=["litellm", "claude-cli", "gemini-cli", "openai-codex"],
    )

    # Session and turn management
    session_id: str | None = Field(
        None,
        description="Session ID for multi-turn conversations. If not provided, a new session will be created.",
    )
    turn_id: str | None = Field(
        None,
        description="Turn ID for this specific turn. If not provided, a new turn will be created.",
    )

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
        return v or "litellm"

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "Add comprehensive error handling to all API endpoints",
                "model_variants": [
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "provider_credential_id": "cred_openai_123",
                        "model_parameters": {"temperature": 0.7},
                    },
                    {
                        "model_definition_id": "model_claude_3_5_sonnet_anthropic",
                        "provider_credential_id": "cred_anthropic_456",
                        "model_parameters": {"temperature": 0.5},
                    },
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "provider_credential_id": "cred_openai_123",
                        "model_parameters": {"temperature": 0.9},
                    },
                ],
            }
        },
    }


class CreateRunResponse(BaseModel):
    """Response after creating a run."""

    run_id: str = Field(..., description="Unique identifier for the run")
    stream_url: str = Field(..., description="URL to stream agent outputs via SSE")
    status: str = Field(..., description="Initial status of the run")
    estimated_duration_seconds: int = Field(
        ..., description="Estimated time to complete"
    )
    session_id: str = Field(..., description="Session ID for this run")
    turn_id: str = Field(..., description="Turn ID for this run")

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
        "json_schema_extra": {
            "example": {
                "run_id": "run_1234567890abcdef",
                "stream_url": "/api/v1/runs/run_1234567890abcdef/stream",
                "status": "accepted",
                "estimated_duration_seconds": 120,
            }
        },
    }


class RunDetails(BaseModel):
    """Detailed information about a run."""

    id: str = Field(..., description="Unique identifier")
    github_url: str = Field(..., description="Repository URL")
    prompt: str = Field(..., description="Agent prompt")
    model_variants: list[ModelVariantResponse] = Field(
        ..., description="Model variants in this run"
    )
    status: RunStatus = Field(..., description="Current status")
    winning_variation_id: int | None = Field(
        None, description="ID of selected variation"
    )
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
                "model_variants": [
                    {
                        "id": "variant_123",
                        "run_id": "run_1234567890abcdef",
                        "variation_id": 0,
                        "model_definition_id": "model_gpt4_openai",
                        "status": "completed",
                        "tokens_used": 150,
                        "cost_usd": 0.004,
                        "response_time_ms": 2500,
                    }
                ],
                "status": "completed",
                "winning_variation_id": 1,
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


class SelectWinnerRequest(BaseModel):
    """Request to select a winning variation."""

    winning_variation_id: int = Field(
        ...,
        ge=0,
        description="ID of the winning variation",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "winning_variation_id": 2,
            }
        }
    }
