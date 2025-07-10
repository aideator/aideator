from functools import lru_cache
from typing import Any, Optional

from pydantic import Field, HttpUrl, field_validator, model_validator
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
    workers: int = 4
    reload: bool = False
    log_level: str = "info"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    openai_api_key: str  # Required for LiteLLM
    openai_api_key_env_var: str = "OPENAI_API_KEY"  # Environment variable name for containers
    anthropic_api_key: str  # Required for Claude Code CLI
    anthropic_api_key_env_var: str = "ANTHROPIC_API_KEY"  # Environment variable name for containers
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
    kubernetes_job_ttl: int = 3600  # 1 hour
    kubernetes_workdir: str = "/workspace"

    # Agent Configuration
    max_variations: int = Field(default=5, ge=1, le=10)
    max_prompt_length: int = Field(default=2000, ge=10, le=5000)
    agent_container_image: str = "python:3.11-slim"
    agent_memory_limit: str = "512m"
    agent_cpu_limit: float = Field(default=0.5, ge=0.1, le=2.0)
    agent_timeout: int = 300  # 5 minutes
    default_agent_model: str = "gpt-4o-mini"
    debug_agent_container: bool = False  # Enable debug logs for agent containers

    # Repository Configuration
    clone_timeout: int = 300  # 5 minutes
    max_repo_size_mb: int = Field(default=100, ge=1, le=500)
    allowed_git_hosts: list[str] = ["github.com", "gitlab.com"]

    # SSE Configuration
    sse_ping_interval: int = 30
    sse_retry_timeout: int = 3000
    sse_max_connections: int = 100

    # Redis (optional, for production)
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_decode_responses: bool = True

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_tracing: bool = False
    jaeger_agent_host: Optional[str] = None
    jaeger_agent_port: Optional[int] = None

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # Storage
    upload_max_size_mb: int = Field(default=50, ge=1, le=200)
    temp_dir: str = "/tmp/aideator"
    results_retention_days: int = Field(default=30, ge=1, le=365)

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
                return json.loads(v)
            except json.JSONDecodeError:
                return [item.strip() for item in v.split(",")]
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is strong enough."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format."""
        if not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format."""
        if not v.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")
        return v

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Validate settings combinations."""
        if self.enable_tracing and not (
            self.jaeger_agent_host and self.jaeger_agent_port
        ):
            raise ValueError(
                "Jaeger agent host and port must be set when tracing is enabled"
            )
        return self

    def get_kubernetes_secrets(self) -> dict[str, str]:
        """Get secrets to mount in Kubernetes containers."""
        return {
            "openai-api-key": self.openai_api_key,
            "anthropic-api-key": self.anthropic_api_key,
        }

    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        if "postgresql" in self.database_url:
            # Handle both postgresql:// and postgresql+asyncpg:// formats
            if self.database_url.startswith("postgresql+asyncpg://"):
                return self.database_url
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
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