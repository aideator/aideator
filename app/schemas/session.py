from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class SessionBase(BaseModel):
    """Base schema for session."""
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    models_used: List[str] = Field(default_factory=list)


class SessionCreate(SessionBase):
    """Schema for creating a session."""
    pass


class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None


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
    sessions: List[SessionResponse]
    total: int
    limit: int
    offset: int


class TurnBase(BaseModel):
    """Base schema for turn."""
    prompt: str = Field(..., min_length=1)
    context: Optional[str] = None
    models_requested: List[str] = Field(..., min_items=1)


class TurnCreate(TurnBase):
    """Schema for creating a turn."""
    pass


class TurnResponse(TurnBase):
    """Schema for turn response."""
    id: str
    session_id: str
    turn_number: int
    responses: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_cost: float
    status: str

    class Config:
        """Pydantic config."""
        from_attributes = True


class PreferenceBase(BaseModel):
    """Base schema for preference."""
    preferred_model: str = Field(..., min_length=1)
    preferred_response_id: str = Field(..., min_length=1)
    compared_models: List[str] = Field(..., min_items=2)
    response_quality_scores: Dict[str, int] = Field(default_factory=dict)
    feedback_text: Optional[str] = None
    confidence_score: Optional[int] = Field(None, ge=1, le=5)
    preference_type: str = Field(default="response")

    @validator('response_quality_scores')
    def validate_quality_scores(cls, v):
        """Validate quality scores are between 1-5."""
        for model, score in v.items():
            if not isinstance(score, int) or score < 1 or score > 5:
                raise ValueError(f"Quality score for {model} must be between 1-5")
        return v


class PreferenceCreate(PreferenceBase):
    """Schema for creating a preference."""
    pass


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
    most_used_models: List[Dict[str, Any]]
    model_preference_stats: Dict[str, Dict[str, Any]]


class ModelPerformanceMetrics(BaseModel):
    """Schema for model performance metrics."""
    model_name: str
    total_requests: int
    total_cost: float
    average_response_time: float
    preference_win_rate: float
    average_quality_score: float
    usage_percentage: float


class SessionExport(BaseModel):
    """Schema for session export."""
    session: SessionResponse
    turns: List[TurnResponse]
    preferences: List[PreferenceResponse]
    export_format: str = Field(default="json")  # json, markdown, csv