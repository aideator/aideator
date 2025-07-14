from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SessionBase(BaseModel):
    """Base schema for session."""

    title: str = Field(..., max_length=200)
    description: str | None = Field(None, max_length=1000)
    models_used: list[str] = Field(default_factory=list)


class SessionCreate(SessionBase):
    """Schema for creating a session."""


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    title: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None
    is_archived: bool | None = None


class SessionResponse(SessionBase):
    """Schema for session response."""

    id: str
    user_id: str
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime
    total_turns: int
    total_cost: float

    class Config:
        """Pydantic config."""

        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for session list response."""

    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


class TurnBase(BaseModel):
    """Base schema for turn."""

    prompt: str = Field(..., min_length=1)
    context: str | None = None
    models_requested: list[str] = Field(..., min_length=1)


class TurnCreate(TurnBase):
    """Schema for creating a turn."""


class TurnResponse(TurnBase):
    """Schema for turn response."""

    id: str
    session_id: str
    turn_number: int
    responses: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    total_cost: float
    status: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class PreferenceBase(BaseModel):
    """Base schema for preference."""

    preferred_model: str = Field(..., min_length=1)
    preferred_response_id: str = Field(..., min_length=1)
    compared_models: list[str] = Field(..., min_length=2)
    response_quality_scores: dict[str, int] = Field(default_factory=dict)
    feedback_text: str | None = None
    confidence_score: int | None = Field(None, ge=1, le=5)
    preference_type: str = Field(default="response")

    @field_validator("response_quality_scores")
    @classmethod
    def validate_quality_scores(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate quality scores are between 1-5."""
        for model, score in v.items():
            if not isinstance(score, int) or score < 1 or score > 5:
                raise ValueError(f"Quality score for {model} must be between 1-5")
        return v


class PreferenceCreate(PreferenceBase):
    """Schema for creating a preference."""


class PreferenceResponse(PreferenceBase):
    """Schema for preference response."""

    id: str
    user_id: str
    session_id: str
    turn_id: str
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class SessionAnalytics(BaseModel):
    """Schema for session analytics."""

    total_sessions: int
    active_sessions: int
    archived_sessions: int
    total_turns: int
    total_cost: float
    average_cost_per_session: float
    average_turns_per_session: float
    most_used_models: list[dict[str, Any]]
    model_preference_stats: dict[str, dict[str, Any]]

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
    }


class ModelPerformanceMetrics(BaseModel):
    """Schema for model performance metrics."""

    model_name: str
    total_requests: int
    total_cost: float
    average_response_time: float
    preference_win_rate: float
    average_quality_score: float
    usage_percentage: float

    model_config = {
        "protected_namespaces": (),  # Allow model_ prefixed fields
    }


class SessionExport(BaseModel):
    """Schema for session export."""

    session: SessionResponse
    turns: list[TurnResponse]
    preferences: list[PreferenceResponse]
    export_format: str = Field(default="json")  # json, markdown, csv


class ModelVariantRequest(BaseModel):
    """Schema for model variant in request."""

    model_config = {"protected_namespaces": ()}

    id: str = Field(..., description="Unique variant ID")
    model_definition_id: str = Field(..., description="Model definition ID")
    model_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Model parameters like temperature, max_tokens, etc.",
    )


class CodeRequest(BaseModel):
    """Schema for code execution request."""

    model_config = {"protected_namespaces": ()}

    prompt: str = Field(..., min_length=1, description="The coding prompt/instruction")
    context: str | None = Field(None, description="Additional context or codebase URL")
    model_variants: list[ModelVariantRequest] = Field(
        ..., description="List of model variants with parameters"
    )
    max_models: int = Field(
        default=5, ge=1, le=5, description="Maximum number of models to run"
    )


class CodeResponse(BaseModel):
    """Schema for code execution response."""

    turn_id: str = Field(..., description="ID of the created turn")
    run_id: str = Field(..., description="ID of the created run")
    websocket_url: str = Field(..., description="WebSocket URL for streaming results")
    debug_websocket_url: str = Field(..., description="WebSocket URL for debug logs")
    status: str = Field(default="accepted", description="Initial status")
    models_used: list[str] = Field(
        ..., description="List of models that will be executed"
    )
