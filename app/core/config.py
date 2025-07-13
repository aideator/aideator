from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and Kubernetes support."""

    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "AIdeator"
    version: str = "1.0.0"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"

    # Security
    secret_key: str = Field(
        default="dev-secret-key-32-chars-minimum-length-for-development"
    )
    encryption_key: str = Field(default="dev-encryption-key-32-chars-minimum-for-aes")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    openai_api_key: str | None = None  # Required for LiteLLM
    anthropic_api_key: str | None = None  # Required for Claude Code CLI
    gemini_api_key: str | None = None  # Required for Gemini CLI
    api_key_header: str = "X-API-Key"
    allowed_origins: list[str] = ["*"]
    allowed_hosts: list[str] = ["*"]

    # Database
    database_url: str = "postgresql+asyncpg://aideator:aideator@localhost:5432/aideator"
    database_echo: bool = False
    database_pool_size: int = 5
    database_pool_recycle: int = 3600

    # Kubernetes Configuration
    kubernetes_namespace: str = "aideator"
    kubernetes_workdir: str = "/workspace"

    # Agent Configuration
    max_variations: int = Field(default=5, ge=1, le=10)
    max_prompt_length: int = Field(default=2000, ge=10, le=5000)
    default_agent_model: str = "gpt-4o-mini"
    debug_agent_container: bool = False  # Enable debug logs for agent containers

    # Concurrency limits
    max_concurrent_runs: int = Field(default=10, ge=1, le=50)
    max_concurrent_jobs: int = Field(
        default=20, ge=1, le=100
    )  # Total jobs across all runs

    # Repository Configuration
    allowed_git_hosts: list[str] = ["github.com", "gitlab.com"]

    # GitHub OAuth Configuration
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_oauth_scopes: str = "read:user,user:email"  # Only basic user info for auth
    # Note: OAuth redirect URI will be dynamically constructed based on request origin

    # GitHub Test Credentials (for testing OAuth)
    github_test_username: str | None = None
    github_test_password: str | None = None

    # Frontend URL
    frontend_url: str = "http://localhost:3000"

    # Redis Configuration (for LiteLLM Gateway caching only)
    redis_url: str | None = None  # Optional for LiteLLM Gateway caching
    redis_password: str | None = None
    redis_db: int = 0
    redis_decode_responses: bool = True
    redis_ttl_seconds: int = 3600  # 1 hour TTL for messages
    redis_max_connections: int = 100

    # SSE Configuration
    sse_ping_interval: int = 30
    sse_retry_timeout: int = 3000

    # Monitoring
    enable_metrics: bool = True
    enable_tracing: bool = False
    jaeger_agent_host: str | None = None
    jaeger_agent_port: int | None = None

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # LiteLLM Proxy Configuration
    LITELLM_PROXY_URL: str = "http://localhost:4000"
    LITELLM_MASTER_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("allowed_origins", "allowed_hosts", "allowed_git_hosts")
    @classmethod
    def parse_list_from_json(cls, v: Any) -> list[str]:
        """Parse JSON string lists from environment variables."""
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed] if isinstance(parsed, str) else []
            except json.JSONDecodeError:
                return [item.strip() for item in v.split(",")]
        if isinstance(v, list):
            return v
        return []

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is strong enough."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Ensure encryption key is strong enough."""
        if len(v) < 32:
            raise ValueError("Encryption key must be at least 32 characters long")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str | None) -> str | None:
        """Validate OpenAI API key format."""
        if v is not None and not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None) -> str | None:
        """Validate Anthropic API key format."""
        if v is not None and not v.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v: str | None) -> str | None:
        """Validate Gemini API key format."""
        if v is not None and not v.startswith("AIza"):
            raise ValueError("Invalid Gemini API key format")
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str | None) -> str | None:
        """Validate Redis URL format."""
        if v is not None and not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate settings for production readiness."""
        if self.debug:
            # In debug mode, allow weaker settings
            return self

        # Production validations
        if self.secret_key == "dev-secret-key-32-chars-minimum-length-for-development":
            raise ValueError(
                "Default secret key detected. Set a secure SECRET_KEY in production."
            )

        if self.encryption_key == "dev-encryption-key-32-chars-minimum-for-aes":
            raise ValueError(
                "Default encryption key detected. Set a secure ENCRYPTION_KEY in production."
            )

        return self

    def get_kubernetes_secrets(self) -> dict[str, str]:
        """Get secrets to mount in Kubernetes containers."""
        return {
            "openai-api-key": self.openai_api_key or "",
            "anthropic-api-key": self.anthropic_api_key or "",
            "gemini-api-key": self.gemini_api_key or "",
        }

    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        if "postgresql" in self.database_url:
            # Handle both postgresql:// and postgresql+asyncpg:// formats
            if self.database_url.startswith("postgresql+asyncpg://"):
                return self.database_url
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        if "sqlite" in self.database_url:
            # Use aiosqlite for SQLite async support
            return self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
        return self.database_url


class KubernetesEnvironment:
    """Manages environment variables for Kubernetes containers."""

    @staticmethod
    def get_agent_env(variation_id: int) -> dict[str, str]:
        """Get environment variables for agent container."""
        return {
            "PYTHONUNBUFFERED": "1",
            "AGENT_VARIATION_ID": str(variation_id),
            "LOG_LEVEL": "INFO",
        }

    @staticmethod
    def get_build_args() -> dict[str, str]:
        """Get build args for container construction."""
        settings = get_settings()
        return {
            "PYTHON_VERSION": "3.11",
            "WORKDIR": settings.kubernetes_workdir,
        }


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
