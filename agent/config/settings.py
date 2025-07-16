"""
Agent configuration management.

Handles environment variable parsing and configuration validation.
"""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    """Centralized agent configuration."""

    # Core identifiers
    run_id: str
    variation_id: str
    task_id: int | None  # NEW – unified tasks primary key

    # Repository and prompt
    repo_url: str
    prompt: str

    # LLM configuration
    model: str
    temperature: float
    max_tokens: int

    # Services
    database_url: str
    # redis_url: Optional[str]  # COMMENTED OUT: Redis references removed per user request

    # LiteLLM Gateway (to be removed)
    gateway_url: str
    gateway_key: str

    # Working directories
    work_dir: Path
    repo_dir: Path
    log_file: Path

    # Agent mode
    agent_mode: str

    # Feature flags
    require_api_keys_for_agents: bool

    @classmethod
    def from_environment(cls) -> "AgentConfig":
        """Create configuration from environment variables."""
        run_id = os.getenv("RUN_ID", "local-test")
        variation_id = os.getenv("VARIATION_ID", "0")
        task_id_env = os.getenv("TASK_ID")
        task_id = int(task_id_env) if task_id_env and task_id_env.isdigit() else None

        # Core settings
        repo_url = os.getenv("REPO_URL", "")
        prompt = os.getenv("PROMPT", "Analyze this repository")

        # LLM configuration
        model = os.getenv("MODEL", "gpt-4")
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("MAX_TOKENS", "4000"))

        # Services
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # redis_url = os.getenv("REDIS_URL")  # COMMENTED OUT: Redis references removed per user request

        # LiteLLM Gateway (will be removed)
        gateway_url = os.getenv("LITELLM_GATEWAY_URL", "http://aideator-litellm:4000")
        gateway_key = os.getenv("LITELLM_GATEWAY_KEY", "sk-1234")

        # Working directories
        work_dir = Path(tempfile.mkdtemp(prefix="agent-workspace-"))
        repo_dir = work_dir / "repo"
        log_file = work_dir / f"agent_{run_id}_{variation_id}.log"

        # Agent mode
        agent_mode = os.getenv("AGENT_MODE", "claude-cli")

        # Feature flags
        require_api_keys_for_agents = os.getenv("REQUIRE_API_KEYS_FOR_AGENTS", "true").lower() == "true"

        return cls(
            run_id=run_id,
            variation_id=variation_id,
            task_id=task_id,  # NEW
            repo_url=repo_url,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            database_url=database_url,
            # redis_url=redis_url,  # COMMENTED OUT: Redis references removed per user request
            gateway_url=gateway_url,
            gateway_key=gateway_key,
            work_dir=work_dir,
            repo_dir=repo_dir,
            log_file=log_file,
            agent_mode=agent_mode,
            require_api_keys_for_agents=require_api_keys_for_agents,
        )

    @property
    def is_code_mode(self) -> bool:
        """Check if this is a code mode that requires repository."""
        return self.agent_mode in ["claude-cli", "gemini-cli", "openai-codex"]

    def setup_api_keys(self) -> None:
        """Set up API keys in environment if available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
