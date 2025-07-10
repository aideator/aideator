from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

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
    system_prompt: Optional[str] = Field(
        None,
        description="Optional system prompt to prepend",
    )
    stop_sequences: Optional[List[str]] = Field(
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
    model_variants: List[ModelVariantCreate] = Field(
        ...,
        description="List of model variants to run in parallel",
        min_length=1,
        max_length=settings.max_variations,
    )
    use_claude_code: bool = Field(
        default=False,
        description="Use Claude Code CLI instead of basic Claude API",
    )
    agent_mode: Optional[str] = Field(
        default="litellm",
        description="Agent execution mode: 'litellm' or 'claude-cli'",
        examples=["litellm", "claude-cli"],
    )

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure URL is from allowed Git hosts."""
        url_str = str(v)
        allowed = any(
            url_str.startswith(f"https://{host}/") for host in settings.allowed_git_hosts
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
    def validate_agent_mode(cls, v: Optional[str]) -> str:
        """Validate agent mode."""
        if v not in ["litellm", "claude-cli", None]:
            raise ValueError("Agent mode must be 'litellm' or 'claude-cli'")
        return v or "litellm"
    

    model_config = {
        "json_schema_extra": {
            "example": {
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "Add comprehensive error handling to all API endpoints",
                "model_variants": [
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "provider_credential_id": "cred_openai_123",
                        "model_parameters": {"temperature": 0.7}
                    },
                    {
                        "model_definition_id": "model_claude_3_5_sonnet_anthropic",
                        "provider_credential_id": "cred_anthropic_456",
                        "model_parameters": {"temperature": 0.5}
                    },
                    {
                        "model_definition_id": "model_gpt4_openai",
                        "provider_credential_id": "cred_openai_123",
                        "model_parameters": {"temperature": 0.9}
                    }
                ]
            }
        }
    }


class CreateRunResponse(BaseModel):
    """Response after creating a run."""

    run_id: str = Field(..., description="Unique identifier for the run")
    stream_url: str = Field(..., description="URL to stream agent outputs via SSE")
    status: str = Field(..., description="Initial status of the run")
    estimated_duration_seconds: int = Field(
        ..., description="Estimated time to complete"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "run_id": "run_1234567890abcdef",
                "stream_url": "/api/v1/runs/run_1234567890abcdef/stream",
                "status": "accepted",
                "estimated_duration_seconds": 120,
            }
        }
    }


class RunDetails(BaseModel):
    """Detailed information about a run."""

    id: str = Field(..., description="Unique identifier")
    github_url: str = Field(..., description="Repository URL")
    prompt: str = Field(..., description="Agent prompt")
    model_variants: List[ModelVariantResponse] = Field(..., description="Model variants in this run")
    status: RunStatus = Field(..., description="Current status")
    winning_variation_id: Optional[int] = Field(
        None, description="ID of selected variation"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    results: Dict[str, Any] = Field(default_factory=dict, description="Run results")
    total_tokens_used: Optional[int] = Field(None, description="Total tokens consumed")
    total_cost_usd: Optional[float] = Field(None, description="Total cost in USD")

    model_config = {
        "from_attributes": True,
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
                        "response_time_ms": 2500
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
        }
    }


class RunListItem(BaseModel):
    """Summary information for run listings."""

    id: str
    github_url: str
    prompt: str
    model_count: int = Field(..., description="Number of model variants")
    status: RunStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
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


class AgentOutputEvent(BaseModel):
    """Agent output event for SSE streaming."""

    variation_id: int = Field(..., description="Agent variation ID")
    content: str = Field(..., description="Output content")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(default="agent_output", description="Event type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "variation_id": 0,
                "content": "[Agent 0] Analyzing repository structure...",
                "timestamp": "2024-01-01T00:00:00Z",
                "event_type": "agent_output",
            }
        }
    }