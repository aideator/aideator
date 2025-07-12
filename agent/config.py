"""Configuration management for AIdeator agent."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Agent configuration from environment variables."""
    
    # Identity
    run_id: str
    variation_id: str
    
    # Repository
    repo_url: str
    prompt: str
    
    # LLM settings
    model: str
    temperature: float
    max_tokens: int
    agent_mode: str  # "litellm" or "claude-cli"
    
    # Redis
    redis_url: str
    
    # API keys
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]
    
    # Paths
    work_dir: str = "/tmp/agent-workspace"
    
    # Debug
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables."""
        # Required environment variables
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("REDIS_URL environment variable is required")
        
        config = cls(
            # Identity
            run_id=os.getenv("RUN_ID", "local-test"),
            variation_id=os.getenv("VARIATION_ID", "0"),
            
            # Repository
            repo_url=os.getenv("REPO_URL", ""),
            prompt=os.getenv("PROMPT", "Analyze this repository"),
            
            # LLM settings
            model=os.getenv("MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "4000")),
            agent_mode=os.getenv("AGENT_MODE", "litellm"),
            
            # Redis
            redis_url=redis_url,
            
            # API keys
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            
            # Debug
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )
        
        # Set API keys in environment for libraries
        if config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = config.openai_api_key
        if config.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = config.anthropic_api_key
            
        return config