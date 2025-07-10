from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        description="User password (min 8 characters)",
    )
    full_name: str | None = Field(None, description="User's full name")
    company: str | None = Field(None, description="Company name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password meets complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "full_name": "John Doe",
                "company": "Acme Corp",
            }
        }
    }


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
            }
        }
    }


class Token(BaseModel):
    """Authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    }


class UserResponse(BaseModel):
    """User information response."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    created_at: datetime = Field(..., description="Account creation date")
    full_name: str | None = Field(None, description="User's full name")
    company: str | None = Field(None, description="Company name")
    max_runs_per_day: int = Field(..., description="Daily run limit")
    max_variations_per_run: int = Field(..., description="Variations per run limit")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "user_123abc",
                "email": "user@example.com",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00Z",
                "full_name": "John Doe",
                "company": "Acme Corp",
                "max_runs_per_day": 100,
                "max_variations_per_run": 5,
            }
        }
    }


class CreateAPIKeyRequest(BaseModel):
    """Request to create an API key."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name for the API key",
    )
    scopes: list[str] = Field(
        default_factory=lambda: ["runs:create", "runs:read"],
        description="Permission scopes for the key",
    )
    expires_in_days: int | None = Field(
        None,
        ge=1,
        le=365,
        description="Days until expiration (null for no expiration)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Production API Key",
                "scopes": ["runs:create", "runs:read"],
                "expires_in_days": 90,
            }
        }
    }


class APIKeyResponse(BaseModel):
    """API key information (without the actual key)."""

    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="Key name")
    is_active: bool = Field(..., description="Whether key is active")
    created_at: datetime = Field(..., description="Creation date")
    last_used_at: datetime | None = Field(None, description="Last usage date")
    expires_at: datetime | None = Field(None, description="Expiration date")
    scopes: list[str] = Field(..., description="Permission scopes")
    total_requests: int = Field(..., description="Total requests made")
    total_runs: int = Field(..., description="Total runs created")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "key_123abc",
                "name": "Production API Key",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_used_at": "2024-01-15T12:00:00Z",
                "expires_at": "2024-04-01T00:00:00Z",
                "scopes": ["runs:create", "runs:read"],
                "total_requests": 1500,
                "total_runs": 42,
            }
        }
    }


class CreateAPIKeyResponse(BaseModel):
    """Response after creating an API key."""

    api_key: str = Field(
        ...,
        description="The actual API key (only shown once)",
    )
    key_info: APIKeyResponse = Field(..., description="Key metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "api_key": "aid_sk_1234567890abcdef...",
                "key_info": {
                    "id": "key_123abc",
                    "name": "Production API Key",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "scopes": ["runs:create", "runs:read"],
                },
            }
        }
    }
