from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, JSON, Text
from sqlmodel import Field, SQLModel, Relationship


class Session(SQLModel, table=True):
    """Database model for user sessions."""

    __tablename__ = "sessions"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Session metadata
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = Field(default=True)
    is_archived: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Session configuration
    models_used: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    total_turns: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    
    # Relationships
    turns: List["Turn"] = Relationship(back_populates="session")
    preferences: List["Preference"] = Relationship(back_populates="session")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "session_123abc",
                "user_id": "user_123abc",
                "title": "Code Review Session",
                "description": "Reviewing Python API code with multiple models",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "models_used": ["gpt-4", "claude-3-sonnet"],
                "total_turns": 5,
                "total_cost": 0.25
            }
        }


class Turn(SQLModel, table=True):
    """Database model for conversation turns within a session."""

    __tablename__ = "turns"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    session_id: str = Field(foreign_key="sessions.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    turn_number: int = Field(index=True)
    
    # Turn content
    prompt: str = Field(sa_column=Column(Text))
    context: Optional[str] = Field(default=None, sa_column=Column(Text))
    model: str = Field(default="multi-model")  # For backwards compatibility with original schema
    
    # Models and responses
    models_requested: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    responses: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Timing and costs
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    total_cost: float = Field(default=0.0)
    
    # Status
    status: str = Field(default="pending")  # pending, streaming, completed, failed
    
    # Relationships
    session: Optional[Session] = Relationship(back_populates="turns")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "turn_123abc",
                "session_id": "session_123abc",
                "turn_number": 1,
                "prompt": "Analyze this Python code for potential improvements",
                "models_requested": ["gpt-4", "claude-3-sonnet"],
                "responses": {
                    "gpt-4": {"content": "Here's my analysis...", "tokens": 150},
                    "claude-3-sonnet": {"content": "I see several areas...", "tokens": 200}
                },
                "status": "completed",
                "duration_seconds": 12.5,
                "total_cost": 0.05
            }
        }


class Preference(SQLModel, table=True):
    """Database model for user preferences on model responses."""

    __tablename__ = "preferences"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    user_id: str = Field(foreign_key="users.id", index=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    turn_id: str = Field(foreign_key="turns.id", index=True)
    
    # Preference data
    preferred_model: str = Field(index=True)
    preferred_response_id: str
    
    # Comparison context
    compared_models: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    response_quality_scores: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # User feedback
    feedback_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    confidence_score: Optional[int] = Field(default=None, ge=1, le=5)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    preference_type: str = Field(default="response")  # response, style, accuracy, etc.
    
    # Relationships
    session: Optional[Session] = Relationship(back_populates="preferences")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "pref_123abc",
                "user_id": "user_123abc",
                "session_id": "session_123abc",
                "turn_id": "turn_123abc",
                "preferred_model": "claude-3-sonnet",
                "preferred_response_id": "response_abc123",
                "compared_models": ["gpt-4", "claude-3-sonnet"],
                "response_quality_scores": {
                    "gpt-4": 4,
                    "claude-3-sonnet": 5
                },
                "feedback_text": "Claude's response was more detailed and actionable",
                "confidence_score": 4,
                "preference_type": "response"
            }
        }