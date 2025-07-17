from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Database model for users."""

    __tablename__ = "users"

    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # GitHub OAuth fields
    github_id: str | None = Field(default=None, unique=True, index=True)
    github_username: str | None = Field(default=None, index=True)

    # Profile
    name: str | None = Field(default=None)
    company: str | None = Field(default=None)

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
