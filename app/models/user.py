from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Database model for users."""

    __tablename__ = "users"

    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Profile
    full_name: str | None = Field(default=None)
    company: str | None = Field(default=None)

    # GitHub OAuth fields
    github_id: str | None = Field(default=None, unique=True, index=True)
    github_username: str | None = Field(default=None, index=True)
    github_avatar_url: str | None = Field(default=None)
    github_access_token_encrypted: str | None = Field(default=None)
    auth_provider: str = Field(default="local")  # "local" or "github"

    # Usage limits
    max_runs_per_day: int = Field(default=100)
    max_variations_per_run: int = Field(default=5)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "user_123abc",
                "email": "user@example.com",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
            }
        }


class APIKey(SQLModel, table=True):
    """Database model for API keys."""

    __tablename__ = "api_keys"

    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    key_hash: str = Field(unique=True, index=True)
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)

    # Permissions
    scopes: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Usage tracking
    total_requests: int = Field(default=0)
    total_runs: int = Field(default=0)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "key_123abc",
                "user_id": "user_123abc",
                "name": "Production API Key",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "scopes": ["runs:create", "runs:read"],
            }
        }
