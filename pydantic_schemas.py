"""
Comprehensive Pydantic schemas for AIdeator
Provides runtime validation for all API requests, responses, and internal models
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from pydantic import (
    BaseModel, 
    Field, 
    HttpUrl, 
    field_validator, 
    model_validator,
    ConfigDict,
    conint,
    constr,
    confloat
)


# Enums
class RunStatus(str, Enum):
    """Status of a run"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VariationStatus(str, Enum):
    """Status of an individual variation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentModel(str, Enum):
    """Available LLM models"""
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"


class EventType(str, Enum):
    """SSE event types"""
    AGENT_OUTPUT = "agent_output"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    COMPLETE = "complete"


class OutputType(str, Enum):
    """Types of agent output"""
    THOUGHT = "thought"
    ACTION = "action"
    RESULT = "result"
    ERROR = "error"


# Request Models
class AgentConfig(BaseModel):
    """Configuration for LLM agents"""
    model: AgentModel = Field(
        default=AgentModel.CLAUDE_3_OPUS,
        description="LLM model to use"
    )
    max_tokens: conint(ge=1000, le=8000) = Field(
        default=4000,
        description="Maximum tokens for response"
    )
    temperature: confloat(ge=0.0, le=1.0) = Field(
        default=0.7,
        description="Temperature for response generation"
    )
    
    model_config = ConfigDict(use_enum_values=True)


class CreateRunRequest(BaseModel):
    """Request to create a new run"""
    github_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL",
        examples=["https://github.com/fastapi/fastapi"]
    )
    prompt: constr(min_length=10, max_length=2000) = Field(
        ...,
        description="Prompt for the LLM agents",
        examples=["Add comprehensive error handling to the main API endpoints"]
    )
    variations: conint(ge=1, le=5) = Field(
        default=3,
        description="Number of agent variations to run"
    )
    agent_config: Optional[AgentConfig] = Field(
        default=None,
        description="Optional agent configuration overrides"
    )
    
    @field_validator('github_url')
    @classmethod
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        """Ensure URL is a valid GitHub repository"""
        url_str = str(v)
        if not url_str.startswith('https://github.com/'):
            raise ValueError('URL must be a GitHub repository')
        
        # Basic validation of repo format
        parts = url_str.replace('https://github.com/', '').split('/')
        if len(parts) < 2 or not all(parts[:2]):
            raise ValueError('Invalid GitHub repository URL format')
        
        # Remove .git suffix if present
        if url_str.endswith('.git'):
            return HttpUrl(url_str[:-4])
        
        return v
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Clean and validate prompt"""
        # Strip whitespace
        v = v.strip()
        
        # Check it's not just whitespace
        if not v:
            raise ValueError('Prompt cannot be empty')
        
        # Check for reasonable content
        if len(v.split()) < 3:
            raise ValueError('Prompt is too short. Please provide more detail.')
        
        return v


class SelectVariationRequest(BaseModel):
    """Request to select a winning variation"""
    variation_id: conint(ge=0, le=4) = Field(
        ...,
        description="ID of the winning variation"
    )
    feedback: Optional[constr(max_length=1000)] = Field(
        None,
        description="Optional user feedback about the selection"
    )


# Response Models
class CreateRunResponse(BaseModel):
    """Response after creating a run"""
    run_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this run"
    )
    stream_url: str = Field(
        ...,
        description="URL to connect for SSE stream",
        examples=["/api/v1/runs/550e8400-e29b-41d4-a716-446655440000/stream"]
    )
    status: str = Field(
        default="accepted",
        description="Initial status of the run"
    )
    estimated_duration_seconds: int = Field(
        ...,
        description="Estimated time to complete all variations"
    )


class VariationStatusInfo(BaseModel):
    """Status information for a single variation"""
    variation_id: int
    status: VariationStatus
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class RunDetails(BaseModel):
    """Detailed information about a run"""
    run_id: UUID
    github_url: HttpUrl
    prompt: str
    variations: int
    status: RunStatus
    winning_variation: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    variation_statuses: List[VariationStatusInfo] = Field(default_factory=list)
    
    @model_validator(mode='after')
    def validate_timestamps(self) -> 'RunDetails':
        """Ensure timestamp consistency"""
        if self.started_at and self.created_at > self.started_at:
            raise ValueError('created_at cannot be after started_at')
        
        if self.completed_at:
            if not self.started_at:
                raise ValueError('completed_at requires started_at')
            if self.started_at > self.completed_at:
                raise ValueError('started_at cannot be after completed_at')
        
        return self


class SelectVariationResponse(BaseModel):
    """Response after selecting a variation"""
    status: str = Field(default="success")
    run_id: UUID
    selected_variation: int
    message: str = Field(default="Selection recorded successfully")


class CancelRunResponse(BaseModel):
    """Response after cancelling a run"""
    status: str = Field(default="cancelled")
    run_id: UUID
    cancelled_variations: List[int] = Field(
        default_factory=list,
        description="IDs of variations that were cancelled"
    )


# SSE Event Models
class BaseSSEEvent(BaseModel):
    """Base class for all SSE events"""
    event_type: EventType
    variation_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentOutputEvent(BaseSSEEvent):
    """Agent output event"""
    event_type: EventType = EventType.AGENT_OUTPUT
    output_type: OutputType
    content: str
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty"""
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v


class StatusUpdateEvent(BaseSSEEvent):
    """Status update event"""
    event_type: EventType = EventType.STATUS_UPDATE
    status: VariationStatus
    message: Optional[str] = None


class ErrorEvent(BaseSSEEvent):
    """Error event"""
    event_type: EventType = EventType.ERROR
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


class CompleteEvent(BaseSSEEvent):
    """Completion event"""
    event_type: EventType = EventType.COMPLETE
    status: VariationStatus
    duration_seconds: float
    tokens_used: Optional[int] = None


# Health Check Models
class ServiceHealth(str, Enum):
    """Health status of a service"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"


class HealthResponse(BaseModel):
    """Health check response"""
    status: ServiceHealth
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    services: Dict[str, ServiceHealth] = Field(
        default_factory=lambda: {
            "database": ServiceHealth.HEALTHY,
            "dagger_engine": ServiceHealth.HEALTHY,
            "redis": ServiceHealth.NOT_CONFIGURED
        }
    )


# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )


class ValidationError(BaseModel):
    """Validation error detail"""
    field: str
    message: str
    type: str


class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    error: str = Field(default="VALIDATION_ERROR")
    validation_errors: List[ValidationError]


# Internal Domain Models
class DaggerContainerConfig(BaseModel):
    """Configuration for a Dagger container"""
    image: str = Field(default="python:3.11-slim")
    memory_limit: str = Field(default="512m")
    cpu_limit: float = Field(default=0.5)
    timeout_seconds: int = Field(default=600)
    environment: Dict[str, str] = Field(default_factory=dict)
    secrets: Dict[str, str] = Field(default_factory=dict)
    cache_volumes: List[str] = Field(
        default_factory=lambda: ["apt-cache", "pip-cache"]
    )
    
    @field_validator('memory_limit')
    @classmethod
    def validate_memory_limit(cls, v: str) -> str:
        """Validate memory limit format"""
        import re
        if not re.match(r'^\d+[kmg]$', v.lower()):
            raise ValueError('Invalid memory limit format. Use format like "512m" or "1g"')
        return v


class AgentExecutionContext(BaseModel):
    """Context for agent execution"""
    run_id: UUID
    variation_id: int
    repo_url: HttpUrl
    prompt: str
    config: AgentConfig
    container_config: DaggerContainerConfig
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


# Database Models (SQLModel)
from sqlmodel import SQLModel, Field as SQLField


class RunRecord(SQLModel, table=True):
    """Database model for runs"""
    __tablename__ = "runs"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    github_url: str = SQLField(index=True)
    prompt: str
    variations: int
    status: RunStatus = SQLField(default=RunStatus.PENDING)
    winning_variation: Optional[int] = SQLField(default=None)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = SQLField(default=None)
    completed_at: Optional[datetime] = SQLField(default=None)
    agent_config: Optional[str] = SQLField(default=None)  # JSON string


class VariationRecord(SQLModel, table=True):
    """Database model for variations"""
    __tablename__ = "variations"
    
    id: int = SQLField(primary_key=True)
    run_id: UUID = SQLField(foreign_key="runs.id", index=True)
    variation_id: int
    status: VariationStatus = SQLField(default=VariationStatus.PENDING)
    started_at: Optional[datetime] = SQLField(default=None)
    completed_at: Optional[datetime] = SQLField(default=None)
    duration_seconds: Optional[float] = SQLField(default=None)
    tokens_used: Optional[int] = SQLField(default=None)
    error_message: Optional[str] = SQLField(default=None)


# Utility functions for conversion
def run_record_to_details(
    record: RunRecord, 
    variations: List[VariationRecord]
) -> RunDetails:
    """Convert database records to API response model"""
    return RunDetails(
        run_id=record.id,
        github_url=HttpUrl(record.github_url),
        prompt=record.prompt,
        variations=record.variations,
        status=record.status,
        winning_variation=record.winning_variation,
        created_at=record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
        variation_statuses=[
            VariationStatusInfo(
                variation_id=v.variation_id,
                status=v.status,
                duration_seconds=v.duration_seconds,
                error_message=v.error_message
            )
            for v in variations
        ]
    )