from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field


class GitHubAuthResponse(BaseModel):
    """GitHub OAuth authentication response."""

    access_token: str = Field(..., description="GitHub access token")
    token_type: str = Field(default="github", description="Token type")
    user: "UserResponse" = Field(..., description="User information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "ghp_1234567890abcdef...",
                "token_type": "github",
                "user": {
                    "id": "user_github_abc123",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "github_username": "johndoe",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                },
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
    name: str | None = Field(None, description="User's display name")
    company: str | None = Field(None, description="Company name")
    github_username: str | None = Field(None, description="GitHub username")
    max_runs_per_day: int = Field(..., description="Daily run limit")
    max_variations_per_run: int = Field(..., description="Variations per run limit")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "user_github_abc123",
                "email": "user@example.com",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00Z",
                "name": "John Doe",
                "company": "Acme Corp",
                "github_username": "johndoe",
                "max_runs_per_day": 100,
                "max_variations_per_run": 5,
            }
        },
    }


class UserUpdate(BaseModel):
    """User profile update request."""

    name: str | None = Field(None, description="User's display name")
    company: str | None = Field(None, description="Company name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Jane Doe",
                "company": "New Company Inc",
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
        },
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
