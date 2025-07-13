#!/usr/bin/env python
"""
AIdeator Agent - Containerized LLM agent for code analysis and generation.
Runs inside Kubernetes jobs and streams output via stdout.
"""

import asyncio
import asyncio.subprocess
import builtins
import contextlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import git
import requests
from litellm import acompletion, completion_cost, stream_chunk_builder
from tenacity import retry, stop_after_attempt, wait_exponential

# Constants
MIN_API_KEY_LENGTH = 10
MIN_GENERIC_KEY_LENGTH = 5
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 4
RETRY_MAX_WAIT = 10
DEFAULT_TEMPERATURE = 0.7
MAX_KEY_FILE_SIZE = 50000
MAX_KEY_FILES_TO_READ = 10
MAX_FILE_PREVIEW_CHARS = 2000
CHUNK_READ_SIZE = 1024


class DatabaseStreamWriter:
    """Intercepts stdout/stderr and writes to database."""
    
    def __init__(self, original_stream, stream_type: str, agent: 'AIdeatorAgent'):
        self.original_stream = original_stream
        self.stream_type = stream_type  # 'stdout' or 'stderr'
        self.agent = agent
        self.buffer = ""
        self.line_buffer = []  # Buffer multiple lines before writing
        self.max_lines = 10  # Batch up to 10 lines
        self.last_write_time = datetime.now(UTC)
        
    def write(self, text: str) -> int:
        """Write to both original stream and database."""
        # Write to original stream first
        result = self.original_stream.write(text)
        
        # Buffer text and collect complete lines
        self.buffer += text
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            if line.strip():
                self.line_buffer.append(line)
                
                # Check if we should write batch
                current_time = datetime.now(UTC)
                time_elapsed = (current_time - self.last_write_time).total_seconds()
                
                if len(self.line_buffer) >= self.max_lines or time_elapsed > 1.0:
                    self._write_batch()
                    self.last_write_time = current_time
                    
        return result
    
    def _write_batch(self):
        """Write buffered lines as a single database entry."""
        if not self.line_buffer or not self.agent.db_service:
            return
            
        # Combine lines into a single content block
        combined_content = '\n'.join(self.line_buffer)
        line_count = len(self.line_buffer)
        self.line_buffer = []
        
        # Schedule async write in background
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = loop.create_task(
                    self.agent.db_service.write_agent_output(
                        run_id=self.agent.run_id,
                        variation_id=int(self.agent.variation_id),
                        content=combined_content,
                        output_type=self.stream_type,
                        metadata={"source": "python_print", "line_count": line_count}
                    )
                )
                # Add to background tasks
                if not hasattr(self.agent, '_bg_tasks'):
                    self.agent._bg_tasks = set()
                self.agent._bg_tasks.add(task)
                task.add_done_callback(self.agent._bg_tasks.discard)
        except Exception:
            # Silently ignore if no event loop
            pass
        
    def flush(self):
        """Flush the stream."""
        # Flush any remaining complete lines
        if self.line_buffer:
            self._write_batch()
            
        # Flush any remaining partial buffer
        if self.buffer.strip():
            self.line_buffer.append(self.buffer)
            self._write_batch()
            self.buffer = ""
            
        return self.original_stream.flush()
        
    def __getattr__(self, name):
        """Delegate all other attributes to original stream."""
        return getattr(self.original_stream, name)


class AIdeatorAgent:
    """Main agent class for repository analysis and code generation."""

    def __init__(self):
        """Initialize agent with configuration from environment."""
        self.run_id = os.getenv("RUN_ID", "local-test")
        self.variation_id = int(os.getenv("VARIATION_ID", "0"))
        self.repo_url = os.getenv("REPO_URL", "")
        self.prompt = os.getenv("PROMPT", "Analyze this repository")

        # LLM configuration
        self.config = {
            "model": os.getenv("MODEL", "gpt-4"),
            "temperature": float(os.getenv("TEMPERATURE", str(DEFAULT_TEMPERATURE))),
            "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
        }

        # LiteLLM Gateway configuration
        self.gateway_url = os.getenv(
            "LITELLM_GATEWAY_URL", "http://aideator-litellm:4000"
        )
        self.gateway_key = os.getenv("LITELLM_GATEWAY_KEY", "sk-1234")

        # Job token for secure API key retrieval
        self.job_token = os.getenv("JOB_TOKEN")
        self.orchestrator_url = os.getenv("ORCHESTRATOR_API_URL", "http://aideator-fastapi:8000/api/v1")

        # API keys will be fetched from orchestrator
        self.api_keys = {}

        # Working directory - use a secure temp directory
        self.work_dir = Path(tempfile.mkdtemp(prefix="agent-workspace-"))
        self.repo_dir = self.work_dir / "repo"

        # Setup logging to file only (not stdout to avoid mixing with LLM output)
        self.log_file = self.work_dir / f"agent_{self.run_id}_{self.variation_id}.log"
        self._setup_file_logging()

        # Fetch API keys from orchestrator before checking availability
        self._fetch_api_keys_from_orchestrator()

        # Check available API keys for graceful error handling
        self.available_api_keys = self._check_available_api_keys()

        # Redis setup (required for streaming)
        self.redis_url = os.getenv("REDIS_URL")
        if not self.redis_url:
            print(
                json.dumps(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "run_id": self.run_id,
                        "variation_id": self.variation_id,
                        "level": "ERROR",
                        "message": "REDIS_URL environment variable not set",
                    }
                ),
                flush=True,
            )
            raise RuntimeError("REDIS_URL is required for agent operation")

        self.redis_client = None  # Will be initialized in async context

        # Database setup (required for dual-write persistence)
        self.database_url = os.getenv("DATABASE_URL_ASYNC")
        if not self.database_url:
            print(
                json.dumps(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "run_id": self.run_id,
                        "variation_id": self.variation_id,
                        "level": "ERROR",
                        "message": "DATABASE_URL_ASYNC environment variable not set",
                    }
                ),
                flush=True,
            )
            raise RuntimeError("DATABASE_URL_ASYNC is required for agent operation")

        self.db_service = None  # Will be initialized in async context

    async def _init_redis(self):
        """Initialize Redis connection in async context."""
        try:
            import redis.asyncio as redis

            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.log(f"[REDIS-CONNECT] Connected to Redis at: {self.redis_url}", "INFO")

            # Test stream access
            test_stream = f"run:{self.run_id}:test"
            test_id = await self.redis_client.xadd(test_stream, {"test": "connection"})
            self.log(
                f"[REDIS-CONNECT] Test stream write successful: {test_id}", "DEBUG"
            )

            # Clean up test stream
            await self.redis_client.delete(test_stream)

        except Exception as e:
            self.log(f"[REDIS-CONNECT] Redis connection failed: {e}", "ERROR")
            raise RuntimeError(f"Failed to connect to Redis: {e}")

    async def _init_database(self):
        """Initialize database connection in async context."""
        try:
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 About to import AgentDatabaseService"
            }), flush=True)
            from agent.services.database_service import AgentDatabaseService

            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 About to create AgentDatabaseService instance"
            }), flush=True)
            self.db_service = AgentDatabaseService()
            
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 About to call db_service.connect()"
            }), flush=True)
            await self.db_service.connect()
            
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 Database connection successful"
            }), flush=True)
            self.log("[DB-CONNECT] Connected to database", "INFO")

        except Exception as e:
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "ERROR",
                "message": f"🔧 Database connection failed: {e}",
                "exception_type": type(e).__name__,
                "exception_str": str(e)
            }), flush=True)
            self.log(f"[DB-CONNECT] Database connection failed: {e}", "ERROR")
            raise RuntimeError(f"Failed to connect to database: {e}")

    async def _fetch_api_keys(self):
        """Fetch API keys from orchestrator using job token."""
        if not self.job_token:
            self.log("[API-KEYS] No job token provided - skipping API key fetch", "WARNING")
            return

        try:
            import aiohttp

            # Make request to orchestrator API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.orchestrator_url}/jobs/keys",
                    json={"job_token": self.job_token},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.api_keys = data.get("keys", {})

                        # Set environment variables for compatibility
                        for key, value in self.api_keys.items():
                            os.environ[key] = value

                        self.log(f"[API-KEYS] Successfully fetched {len(self.api_keys)} API keys", "INFO")

                        # Log which providers are available (without exposing keys)
                        providers = [key.replace("_API_KEY", "") for key in self.api_keys]
                        self.log(f"[API-KEYS] Available providers: {providers}", "INFO")

                    else:
                        error_text = await response.text()
                        self.log(f"[API-KEYS] Failed to fetch API keys: {response.status} - {error_text}", "ERROR")

        except Exception as e:
            self.log(f"[API-KEYS] Error fetching API keys: {e}", "ERROR")

    def _fetch_api_keys_from_orchestrator(self):
        """Fetch API keys from orchestrator using job token."""
        if not self.job_token:
            print(
                json.dumps(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "run_id": self.run_id,
                        "variation_id": self.variation_id,
                        "level": "WARNING",
                        "message": "No job token provided, skipping API key retrieval",
                    }
                ),
                flush=True,
            )
            return

        try:
            import requests
            
            response = requests.post(
                f"{self.orchestrator_url}/jobs/keys",
                json={"job_token": self.job_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.api_keys = data.get("keys", {})
                
                # Set environment variables for the API keys
                for key_name, key_value in self.api_keys.items():
                    os.environ[key_name] = key_value
                
                # Update available API keys after setting environment variables
                self.available_api_keys = self._check_available_api_keys()
                
                print(
                    json.dumps(
                        {
                            "timestamp": datetime.now(UTC).isoformat(),
                            "run_id": self.run_id,
                            "variation_id": self.variation_id,
                            "level": "INFO",
                            "message": f"✅ Successfully fetched {len(self.api_keys)} API keys from orchestrator",
                        }
                    ),
                    flush=True,
                )
            else:
                print(
                    json.dumps(
                        {
                            "timestamp": datetime.now(UTC).isoformat(),
                            "run_id": self.run_id,
                            "variation_id": self.variation_id,
                            "level": "ERROR",
                            "message": f"Failed to fetch API keys: {response.status_code} - {response.text}",
                        }
                    ),
                    flush=True,
                )
        except Exception as e:
            print(
                json.dumps(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "run_id": self.run_id,
                        "variation_id": self.variation_id,
                        "level": "ERROR",
                        "message": f"Error fetching API keys: {str(e)}",
                    }
                ),
                flush=True,
            )

    def _setup_file_logging(self):
        """Setup file-only logging to avoid stdout pollution."""
        # Create a logger that only writes to file
        self.file_logger = logging.getLogger(f"agent_{self.run_id}_{self.variation_id}")
        self.file_logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.file_logger.handlers = []

        # Add file handler only
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self.file_logger.addHandler(fh)

        # Prevent propagation to root logger (which might log to stdout)
        self.file_logger.propagate = False

    def _check_available_api_keys(self) -> dict:
        """Check which API keys are available for different providers."""
        available_keys = {}

        # Check OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if (
            openai_key
            and openai_key.strip()
            and openai_key != "sk-"
            and len(openai_key) > MIN_API_KEY_LENGTH
        ):
            available_keys["openai"] = True
        else:
            available_keys["openai"] = False

        # Check Anthropic API Key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if (
            anthropic_key
            and anthropic_key.strip()
            and anthropic_key.startswith("sk-ant-")
        ):
            available_keys["anthropic"] = True
        else:
            available_keys["anthropic"] = False

        # Check Gemini API Key
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and gemini_key.strip() and gemini_key.startswith("AIza"):
            available_keys["gemini"] = True
        else:
            available_keys["gemini"] = False

        # Check other provider keys
        for provider, env_var in [
            ("mistral", "MISTRAL_API_KEY"),
            ("cohere", "COHERE_API_KEY"),
            ("groq", "GROQ_API_KEY"),
            ("perplexity", "PERPLEXITY_API_KEY"),
            ("deepseek", "DEEPSEEK_API_KEY"),
        ]:
            key = os.getenv(env_var)
            available_keys[provider] = bool(
                key and key.strip() and len(key) > MIN_GENERIC_KEY_LENGTH
            )

        return available_keys

    def _get_model_provider(self, model_name: str) -> str:
        """Get the provider for a given model name."""
        model_lower = model_name.lower()

        if model_lower.startswith(("gpt", "openai", "o1")):
            return "openai"
        if model_lower.startswith(("claude", "anthropic")):
            return "anthropic"
        if model_lower.startswith(("gemini", "google")):
            return "gemini"
        if model_lower.startswith(("mistral", "mixtral")):
            return "mistral"
        if model_lower.startswith(("cohere", "command")):
            return "cohere"
        if model_lower.startswith("groq"):
            return "groq"
        if model_lower.startswith("perplexity"):
            return "perplexity"
        if model_lower.startswith("deepseek"):
            return "deepseek"
        # Default to openai for unknown models
        return "openai"


    def _validate_model_credentials(self, model_name: str) -> tuple[bool, str]:
        """Validate that credentials are available for the requested model.

        Returns:
            tuple: (is_valid, error_message)
        """
        provider = self._get_model_provider(model_name)

        if not self.available_api_keys.get(provider, False):
            provider_names = {
                "openai": "OpenAI",
                "anthropic": "Anthropic (Claude)",
                "gemini": "Google Gemini",
                "mistral": "Mistral AI",
                "cohere": "Cohere",
                "groq": "Groq",
                "perplexity": "Perplexity",
                "deepseek": "DeepSeek",
            }

            readable_provider = provider_names.get(provider, provider.title())

            error_msg = f"""
🚫 **Missing API Key for {readable_provider}**

The model '{model_name}' requires a {readable_provider} API key, but none was found.

**To fix this issue:**

1. **Get an API key** from {readable_provider}:
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/
   - Google Gemini: https://ai.google.dev/
   - Mistral AI: https://console.mistral.ai/
   - Cohere: https://dashboard.cohere.ai/
   - Groq: https://console.groq.com/
   - Perplexity: https://www.perplexity.ai/settings/api
   - DeepSeek: https://platform.deepseek.com/

2. **Add the secret to Kubernetes**:
   ```bash
   kubectl create secret generic {provider}-secret \\
     --from-literal=api-key="your-api-key-here" \\
     -n aideator
   ```

3. **Try again** - The model should work once the API key is configured.

**Available models:** Try using a model from a provider that has been configured with API keys.

{self._get_available_models_suggestion()}
"""
            return False, error_msg

        return True, ""

    def _get_available_models_suggestion(self) -> str:
        """Get a helpful suggestion of available models based on configured API keys."""
        available_providers = [
            provider
            for provider, available in self.available_api_keys.items()
            if available
        ]

        if not available_providers:
            return "No API keys are currently configured. Please add at least one API key to use any models."

        suggestions = []
        for provider in available_providers:
            if provider == "openai":
                suggestions.append("- OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo")
            elif provider == "anthropic":
                suggestions.append("- Anthropic: claude-3-5-sonnet, claude-3-haiku")
            elif provider == "gemini":
                suggestions.append("- Google: gemini-1.5-pro, gemini-1.5-flash")
            elif provider == "mistral":
                suggestions.append(
                    "- Mistral: mistral-large-latest, mistral-small-latest"
                )
            elif provider == "cohere":
                suggestions.append("- Cohere: command-r-plus, command-r")
            elif provider == "groq":
                suggestions.append("- Groq: llama3-8b-8192")
            elif provider == "perplexity":
                suggestions.append("- Perplexity: llama-3.1-sonar-small-128k-online")
            elif provider == "deepseek":
                suggestions.append("- DeepSeek: deepseek-chat")

        return "**Available models with configured API keys:**\n" + "\n".join(
            suggestions
        )

    def log(self, message: str, level: str = "INFO", **kwargs):
        """
        Structured logging with JSON output to database.
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "level": level,
            "message": message,
            **kwargs,
        }

        # For now, just print to stdout for debugging
        if os.getenv("DEBUG") == "true":
            print(json.dumps(log_entry), flush=True)

        # Also log to file
        self.file_logger.log(
            getattr(logging, level, logging.INFO),
            f"{message} | {json.dumps(kwargs) if kwargs else ''}",
        )

        # Publish to database (async operation, fire and forget)
        if hasattr(self, "db_service") and self.db_service:
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Include run_id and variation_id in kwargs for database
                    db_kwargs = {
                        "run_id": self.run_id,
                        "variation_id": self.variation_id,
                        **kwargs
                    }
                    # Schedule as a task if loop is running
                    task = loop.create_task(
                        self.db_service.publish_log(message, level, **db_kwargs)
                    )
                    # Store task reference to avoid warning
                    if not hasattr(self, "_bg_tasks"):
                        self._bg_tasks = set()
                    self._bg_tasks.add(task)
                    task.add_done_callback(self._bg_tasks.discard)
                else:
                    # If no loop is running, this is likely during initialization
                    pass
            except RuntimeError:
                # No event loop available, skip database logging
                pass

    def log_progress(self, message: str, detail: str = ""):
        """Log progress updates for user visibility."""
        self.log(f"⚡ {message}", "INFO", detail=detail)

    async def log_progress_async(self, message: str, detail: str = ""):
        """Async log progress updates that stream to Redis."""
        await self.log_async(f"⚡ {message}", "INFO", detail=detail)

    async def log_async(self, message: str, level: str = "INFO", **kwargs):
        """Async structured logging with dual write to Redis Streams and PostgreSQL."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "level": level,
            "message": message,
            **kwargs,
        }

        # Log to file first
        self.file_logger.log(
            getattr(logging, level, logging.INFO),
            f"{message} | {json.dumps(kwargs) if kwargs else ''}",
        )

        # Dual write: Redis + Database
        redis_success = False
        db_success = False

        # Publish to Redis Streams
        try:
            if self.redis_client:
                stream_name = f"run:{self.run_id}:stdout"
                fields = {
                    "variation_id": self.variation_id,
                    "content": json.dumps(log_entry),
                    "level": level,
                    "timestamp": log_entry["timestamp"],
                }
                await self.redis_client.xadd(stream_name, fields)
                redis_success = True
        except Exception as e:
            self.file_logger.error(f"Failed to publish log to Redis Streams: {e}")

        # Write to database
        try:
            if self.db_service:
                await self.db_service.write_agent_output(
                    run_id=self.run_id,
                    variation_id=int(self.variation_id),
                    content=message,
                    output_type="logging",
                    metadata={"level": level, **kwargs}
                )
                db_success = True
        except Exception as e:
            self.file_logger.error(f"Failed to write log to database: {e}")

        # Log dual write status in debug mode
        if os.getenv("DEBUG") == "true":
            if redis_success and db_success:
                self.file_logger.debug("[DUAL-WRITE] Log written to both Redis and DB")
            elif redis_success:
                self.file_logger.debug("[DUAL-WRITE] Log written to Redis only (DB failed)")
            elif db_success:
                self.file_logger.debug("[DUAL-WRITE] Log written to DB only (Redis failed)")
            else:
                self.file_logger.debug("[DUAL-WRITE] Failed to write log to both Redis and DB")

        # Also print to stdout in debug mode
        if os.getenv("DEBUG") == "true":
            print(json.dumps(log_entry), flush=True)

    async def publish_output(self, content: str):
        """Publish agent output with dual write to Redis Streams and PostgreSQL."""
        # Don't log LLM output as it creates duplicate content in logs
        
        # Dual write: Write to both Redis and database
        success_redis = False
        success_db = False

        # Write to Redis Streams (for real-time streaming)
        try:
            if self.redis_client:
                stream_name = f"run:{self.run_id}:llm"
                fields = {
                    "variation_id": self.variation_id,
                    "content": content,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "metadata": json.dumps({"content_length": len(content)}),
                }

                message_id = await self.redis_client.xadd(stream_name, fields)
                self.log(
                    f"[REDIS-STREAMS] Published LLM output to stream: {stream_name}, ID: {message_id}",
                    "DEBUG",
                )
                success_redis = True
            else:
                self.log("[REDIS-STREAMS] Redis client not initialized", "ERROR")

        except Exception as e:
            self.log(
                f"[REDIS-STREAMS] Failed to publish output to Redis Streams: {e}",
                "ERROR",
            )

        # Write to database (for persistence)
        try:
            if self.db_service:
                await self.db_service.write_agent_output(
                    run_id=self.run_id,
                    variation_id=int(self.variation_id),
                    content=content,
                    output_type="llm",
                    metadata={"content_length": len(content)},
                )
                success_db = True
            else:
                self.log("[DB-WRITE] Database service not initialized", "ERROR")

        except Exception as e:
            self.log(
                f"[DB-WRITE] Failed to write output to database: {e}",
                "ERROR",
            )

        # Log dual write status
        if success_redis and success_db:
            self.log(
                "[DUAL-WRITE] Successfully wrote LLM output to both Redis and DB",
                "DEBUG",
            )
        elif success_redis:
            self.log(
                "[DUAL-WRITE] LLM output written to Redis only (DB failed)",
                "WARNING",
            )
        elif success_db:
            self.log(
                "[DUAL-WRITE] LLM output written to DB only (Redis failed)",
                "WARNING",
            )
        else:
            self.log(
                "[DUAL-WRITE] Failed to write LLM output to both Redis and DB",
                "ERROR",
            )

    async def _publish_to_redis_only(self, content: str):
        """Publish agent output to Redis Streams only (database handled by DatabaseStreamWriter)."""
        try:
            if self.redis_client:
                stream_name = f"run:{self.run_id}:llm"
                fields = {
                    "variation_id": self.variation_id,
                    "content": content,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "metadata": json.dumps({"content_length": len(content)}),
                }

                message_id = await self.redis_client.xadd(stream_name, fields)
                self.log(
                    f"[REDIS-ONLY] Published LLM output to stream: {stream_name}, ID: {message_id}",
                    "DEBUG",
                )
            else:
                self.log("[REDIS-ONLY] Redis client not initialized", "ERROR")

        except Exception as e:
            self.log(
                f"[REDIS-ONLY] Failed to publish output to Redis Streams: {e}",
                "ERROR",
            )

    async def publish_status(self, status: str, metadata: dict[str, Any] | None = None):
        """Publish status update with dual write to Redis Streams and PostgreSQL."""
        # Dual write: Write to both Redis and database
        success_redis = False
        success_db = False

        # Write to Redis Streams (for real-time streaming)
        try:
            if self.redis_client:
                stream_name = f"run:{self.run_id}:status"
                fields = {
                    "status": status,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "metadata": json.dumps(metadata or {}),
                }
                message_id = await self.redis_client.xadd(stream_name, fields)
                self.log(
                    f"[REDIS-STREAMS] Published status '{status}' to stream: {message_id}",
                    "DEBUG",
                )
                success_redis = True
            else:
                self.log("[REDIS-STREAMS] Redis client not initialized", "ERROR")
        except Exception as e:
            self.log(
                f"[REDIS-STREAMS] Failed to publish status to Redis Streams: {e}",
                "ERROR",
            )

        # Write to database (for persistence)
        try:
            if self.db_service:
                await self.db_service.update_run_status(
                    run_id=self.run_id,
                    status=status,
                    metadata=metadata,
                )
                success_db = True
            else:
                self.log("[DB-WRITE] Database service not initialized", "ERROR")
        except Exception as e:
            self.log(
                f"[DB-WRITE] Failed to update status in database: {e}",
                "ERROR",
            )

        # Log dual write status
        if success_redis and success_db:
            self.log(
                f"[DUAL-WRITE] Successfully wrote status '{status}' to both Redis and DB",
                "DEBUG",
            )
        elif success_redis:
            self.log(
                f"[DUAL-WRITE] Status '{status}' written to Redis only (DB failed)",
                "WARNING",
            )
        elif success_db:
            self.log(
                f"[DUAL-WRITE] Status '{status}' written to DB only (Redis failed)",
                "WARNING",
            )
        else:
            self.log(
                f"[DUAL-WRITE] Failed to write status '{status}' to both Redis and DB",
                "ERROR",
            )

    def log_error(self, error: str, exception: Exception | None = None):
        """Log errors with details."""
        error_data = {"error": error}
        if exception:
            error_data["exception"] = str(exception)
            error_data["exception_type"] = type(exception).__name__
        self.log(f"❌ {error}", "ERROR", **error_data)

    async def run(self) -> None:
        """Main agent execution flow."""
        print(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "DEBUG",
            "message": "🔧 Entered agent.run() method"
        }), flush=True)
        
        self.log("🚀 Starting AIdeator Agent", "INFO", config=self.config)

        # Initialize Redis and Database connections
        print(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "DEBUG",
            "message": "🔧 About to initialize Redis"
        }), flush=True)
        await self._init_redis()
        
        print(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "DEBUG",
            "message": "🔧 About to initialize Database"
        }), flush=True)
        await self._init_database()
        
        # Install stdout/stderr interceptors to capture all output
        if self.db_service:
            sys.stdout = DatabaseStreamWriter(sys.stdout, "stdout", self)
            sys.stderr = DatabaseStreamWriter(sys.stderr, "stderr", self)
            self.log("📝 Installed stdout/stderr interceptors for database persistence", "INFO")

        # Fetch API keys from orchestrator
        print(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "DEBUG",
            "message": "🔧 About to fetch API keys (async method)"
        }), flush=True)
        await self._fetch_api_keys()

        print(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "DEBUG",
            "message": "🔧 API keys fetched, about to log availability"
        }), flush=True)

        # Log available API keys for debugging
        await self.log_async(
            "🔑 API Key availability check",
            "INFO",
            available_keys=self.available_api_keys,
        )

        # Validate model credentials before proceeding
        is_valid, error_msg = self._validate_model_credentials(self.config["model"])
        if not is_valid:
            # Output the user-friendly error message
            print(error_msg, flush=True)
            self.log_error(f"Missing API key for model {self.config['model']}", None)
            raise RuntimeError(f"Missing API key for model {self.config['model']}")

        # Log agent mode
        agent_mode = os.getenv("AGENT_MODE", "litellm")
        self.log(f"🎯 Agent mode: {agent_mode}", "INFO", agent_mode=agent_mode)

        # Check if this is a code mode that requires repository
        is_code_mode = agent_mode in ["claude-cli", "gemini-cli", "openai-codex"]

        if is_code_mode:
            # Log CLI tool versions for code modes
            if agent_mode == "claude-cli":
                claude_version = self._get_cli_version("claude")
                self.log(
                    f"🤖 Claude CLI version: {claude_version}",
                    "INFO",
                    claude_version=claude_version,
                )
            elif agent_mode == "gemini-cli":
                gemini_version = self._get_cli_version("gemini")
                self.log(
                    f"💎 Gemini CLI version: {gemini_version}",
                    "INFO",
                    gemini_version=gemini_version,
                )
            elif agent_mode == "openai-codex":
                codex_version = self._get_cli_version("codex")
                self.log(
                    f"🔥 OpenAI Codex CLI version: {codex_version}",
                    "INFO",
                    codex_version=codex_version,
                )

        # Log LiteLLM Gateway configuration
        self.log(
            "🔧 Using LiteLLM Gateway",
            "INFO",
            gateway_url=self.gateway_url,
            model=self.config["model"],
            note="Routing through LiteLLM Gateway for unified API access",
        )

        # Log file location to file only, not stdout
        self.log(f"Debug logs location: {self.log_file}", "INFO")

        try:
            if is_code_mode:
                # Code mode: Clone repository and analyze codebase
                self.log("📁 Code mode detected - cloning repository", "INFO")
                await self._clone_repository()

                # Analyze codebase
                codebase_summary = await self._analyze_codebase()

                # Generate response with LLM
                response = await self._generate_llm_response(codebase_summary)
            else:
                # Chat mode: Skip repository cloning, just pass prompt directly
                self.log("💬 Chat mode detected - skipping repository clone", "INFO")
                response = await self._generate_llm_response(None)

            # Output final response
            self.log(
                "✅ Generation complete",
                "INFO",
                response_length=len(response),
                status="success",
            )

        except Exception as e:
            self.log_error("Agent execution failed", e)
            raise

    async def _clone_repository(self) -> None:
        """Clone the repository to analyze."""
        self.log_progress("Cloning repository", self.repo_url)

        try:
            if self.repo_dir.exists():
                shutil.rmtree(self.repo_dir)

            # Clone with minimal depth
            git.Repo.clone_from(
                self.repo_url, self.repo_dir, depth=1, single_branch=True
            )

            self.log_progress(
                "Repository cloned successfully",
                f"Size: {self._get_directory_size(self.repo_dir)} MB",
            )

        except Exception as e:
            self.log_error("Failed to clone repository", e)
            raise RuntimeError(f"Repository clone failed: {e}") from e

    async def _analyze_codebase(self) -> str:
        """Analyze the codebase structure and content."""
        self.log_progress("Analyzing codebase structure")

        analysis = {
            "files": [],
            "total_files": 0,
            "total_size_mb": 0,
            "languages": {},
            "key_files": [],
        }

        try:
            # Walk through repository
            for root, dirs, files in os.walk(self.repo_dir):
                # Skip hidden and vendor directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "vendor", "__pycache__"]
                ]

                for file in files:
                    if file.startswith("."):
                        continue

                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.repo_dir)

                    # Track file extension
                    ext = file_path.suffix.lower()
                    if ext:
                        analysis["languages"][ext] = (
                            analysis["languages"].get(ext, 0) + 1
                        )

                    analysis["total_files"] += 1

                    # Add file info
                    file_info = {
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                    }
                    analysis["files"].append(file_info)

            # Calculate total size
            analysis["total_size_mb"] = self._get_directory_size(self.repo_dir)

            # Identify key files
            analysis["key_files"] = self._identify_key_files()

            # Read key file contents
            summary_parts = [
                f"Repository: {self.repo_url}",
                f"Total files: {analysis['total_files']}",
                f"Total size: {analysis['total_size_mb']} MB",
                f"Languages: {', '.join(f'{k}({v})' for k, v in sorted(analysis['languages'].items(), key=lambda x: x[1], reverse=True)[:5])}",
                "",
                "Key files:",
            ]

            # Read contents of key files
            for key_file in analysis["key_files"][
                :MAX_KEY_FILES_TO_READ
            ]:  # Limit to top files
                file_path = self.repo_dir / key_file
                if (
                    file_path.exists() and file_path.stat().st_size < MAX_KEY_FILE_SIZE
                ):  # Skip large files
                    try:
                        async with aiofiles.open(
                            file_path, encoding="utf-8", errors="ignore"
                        ) as f:
                            content = await f.read()
                            summary_parts.extend(
                                [
                                    f"\n--- {key_file} ---",
                                    content[:MAX_FILE_PREVIEW_CHARS],  # First chars
                                    "..."
                                    if len(content) > MAX_FILE_PREVIEW_CHARS
                                    else "",
                                    "",
                                ]
                            )
                    except Exception as e:
                        self.file_logger.warning(f"Failed to read {key_file}: {e}")

            summary = "\n".join(summary_parts)

            self.log_progress(
                "Codebase analysis complete",
                f"Files: {analysis['total_files']}, Size: {analysis['total_size_mb']}MB",
            )

            return summary

        except Exception as e:
            self.log_error("Codebase analysis failed", e)
            raise RuntimeError(f"Failed to analyze codebase: {e}") from e

    def _identify_key_files(self) -> list:
        """Identify important files in the repository."""
        key_patterns = [
            "README*",
            "readme*",
            "package.json",
            "requirements.txt",
            "setup.py",
            "Cargo.toml",
            "go.mod",
            "Dockerfile",
            "docker-compose*",
            ".github/workflows/*",
            "main.*",
            "app.*",
            "index.*",
            "config.*",
            "settings.*",
        ]

        key_files = []
        for pattern in key_patterns:
            if "*" in pattern:
                # Handle wildcards
                import glob

                matches = glob.glob(str(self.repo_dir / pattern), recursive=True)
                for match in matches:
                    try:
                        rel_path = Path(match).relative_to(self.repo_dir)
                        key_files.append(str(rel_path))
                    except:
                        pass
            else:
                # Direct file check
                file_path = self.repo_dir / pattern
                if file_path.exists():
                    key_files.append(pattern)

        return key_files

    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB."""
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return round(total_size / (1024 * 1024), 2)

    def _get_cli_version(self, command: str) -> str:
        """Get version of a CLI tool."""
        try:
            result = subprocess.run(
                [command, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return f"Error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except FileNotFoundError:
            return "Error: Command not found"
        except Exception as e:
            return f"Error: {e!s}"

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def _generate_llm_response(self, codebase_summary: str) -> str:
        """Generate LLM response based on codebase analysis."""
        agent_mode = os.getenv("AGENT_MODE", "litellm")

        if agent_mode == "claude-cli":
            return await self._generate_claude_cli_response()
        if agent_mode == "gemini-cli":
            return await self._generate_gemini_cli_response()
        if agent_mode == "openai-codex":
            return await self._generate_openai_codex_response()
        return await self._generate_litellm_response(codebase_summary)

    async def _generate_claude_cli_response(self) -> str:
        """Generate response using Claude CLI with real-time streaming."""
        self.log_progress(
            "Generating response using Claude CLI",
            "Executing claude command with streaming output",
        )

        try:
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.repo_dir)

            # Execute Claude CLI with streaming arguments (matching TypeScript version)
            self.log_progress(
                "Executing Claude CLI", f"Working directory: {self.repo_dir}"
            )

            # Use the same arguments as the working TypeScript version
            args = [
                "claude",
                "--verbose",
                "--output-format",
                "stream-json",
                "--dangerously-skip-permissions",
                "-p",
                self.prompt,
            ]

            self.log_progress("Spawning Claude CLI", f"Args: {' '.join(args)}")

            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=os.environ,  # Includes ANTHROPIC_API_KEY
            )

            # Close stdin immediately since we're using -p flag (like TypeScript version)
            process.stdin.close()

            # Stream processing variables
            collected_output = []
            buffer = ""
            data_chunks = 0
            total_bytes = 0

            self.log_progress("Claude CLI process started", f"PID: {process.pid}")

            try:
                # Read stdout in real-time chunks (like TypeScript version)
                while True:
                    # Read a chunk of data
                    chunk = await process.stdout.read(CHUNK_READ_SIZE)
                    if not chunk:
                        break

                    data_chunks += 1
                    total_bytes += len(chunk)

                    chunk_text = chunk.decode("utf-8", errors="ignore")
                    self.log_progress(
                        f"Received stdout chunk #{data_chunks}",
                        f"({len(chunk)} bytes) - {chunk_text[:100]}{'...' if len(chunk_text) > 100 else ''}",
                    )

                    # Process the chunk immediately (streaming approach)
                    buffer += chunk_text
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # Keep incomplete line in buffer

                    for line in lines:
                        if line.strip():
                            try:
                                # Try to parse as JSON first (Claude CLI stream format)
                                json_data = json.loads(line)
                                self.log_progress(
                                    "Parsed JSON message",
                                    f"Type: {json_data.get('type', 'unknown')}",
                                )

                                # Extract content from JSON message
                                if json_data.get(
                                    "type"
                                ) == "assistant" and json_data.get("message", {}).get(
                                    "content"
                                ):
                                    for content_item in json_data["message"]["content"]:
                                        if content_item.get(
                                            "type"
                                        ) == "text" and content_item.get("text"):
                                            text_content = content_item["text"]
                                            # Output immediately for streaming (like TypeScript)
                                            print(text_content, end="", flush=True)
                                            # Stream to Redis only (database handled by DatabaseStreamWriter)
                                            await self._publish_to_redis_only(text_content)
                                            # Note: stdout database writing is handled by DatabaseStreamWriter
                                            collected_output.append(text_content)
                                        elif content_item.get("type") == "tool_use":
                                            tool_info = f"🔧 Using tool: {content_item.get('name', 'unknown')}"
                                            print(tool_info, flush=True)
                                            # Note: stdout database writing is handled by DatabaseStreamWriter
                                            collected_output.append(tool_info + "\n")

                            except json.JSONDecodeError:
                                # If not JSON, treat as plain text output (like TypeScript fallback)
                                self.log_progress(
                                    "Plain text output",
                                    f"{line[:50]}{'...' if len(line) > 50 else ''}",
                                )
                                print(line, flush=True)
                                collected_output.append(line + "\n")

                # Handle any remaining buffer content
                if buffer.strip():
                    self.log_progress(
                        "Processing remaining buffer",
                        f"{buffer[:50]}{'...' if len(buffer) > 50 else ''}",
                    )
                    print(buffer, flush=True)
                    collected_output.append(buffer)

                # Wait for process to complete
                await process.wait()

                # Change back to original directory
                os.chdir(original_dir)

                # Handle stderr if there were errors
                if process.returncode != 0:
                    stderr_output = await process.stderr.read()
                    error_msg = (
                        stderr_output.decode() if stderr_output else "Unknown error"
                    )
                    self.log_error(
                        "Claude CLI process failed",
                        f"Exit code: {process.returncode}, Error: {error_msg}",
                    )
                    # Persist stderr to database
                    if self.db_service and error_msg:
                        await self.db_service.write_agent_output(
                            run_id=self.run_id,
                            variation_id=int(self.variation_id),
                            content=error_msg,
                            output_type="stderr",
                            metadata={"source": "claude_cli", "exit_code": process.returncode}
                        )

                    # Still return collected output if we got some
                    if collected_output:
                        self.log_progress(
                            "Returning partial output despite error",
                            f"Collected {len(collected_output)} chunks",
                        )
                        return "".join(collected_output)
                    raise RuntimeError(
                        f"Claude CLI failed with exit code {process.returncode}: {error_msg}"
                    )

                # Success case
                response = "".join(collected_output)
                self.log_progress(
                    "Claude CLI streaming completed successfully",
                    f"Total chunks: {data_chunks}, Total bytes: {total_bytes}, Response length: {len(response)} characters",
                )

                # Write analytics data for Claude CLI
                if self.db_service:
                    try:
                        request_end_time = datetime.now(UTC)
                        analytics_data = {
                            "model": "claude-cli",
                            "provider": "anthropic",
                            "stream": True,
                            "status": "success",
                            "request_end_time": request_end_time,
                            "response_time_ms": int((request_end_time - datetime.now(UTC)).total_seconds() * 1000),
                            "metadata": {
                                "agent_mode": "claude-cli",
                                "chunks_received": data_chunks,
                                "total_bytes": total_bytes,
                                "response_length": len(response),
                                "working_directory": str(self.repo_dir),
                            }
                        }
                        
                        await self.db_service.write_litellm_analytics(
                            run_id=self.run_id,
                            variation_id=int(self.variation_id),
                            analytics_data=analytics_data
                        )
                        self.log(
                            "Wrote Claude CLI analytics to database",
                            "INFO",
                            analytics_summary=analytics_data
                        )
                    except Exception as analytics_error:
                        self.log(
                            f"Failed to write Claude CLI analytics: {analytics_error}",
                            "ERROR"
                        )

                return response if response else "No output received from Claude CLI"

            except Exception as stream_error:
                # Clean up process if still running
                if process.returncode is None:
                    process.terminate()
                    await process.wait()
                raise stream_error

        except Exception as e:
            # Change back to original directory in case of error
            with contextlib.suppress(builtins.BaseException):
                os.chdir(original_dir)

            self.log_error("Claude CLI streaming execution failed", e)
            raise RuntimeError(f"Failed to generate Claude CLI response: {e}") from e

    async def _generate_gemini_cli_response(self) -> str:
        """Generate response using Gemini CLI."""
        self.log_progress(
            "Generating response using Gemini CLI", "Executing gemini command"
        )

        try:
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.repo_dir)

            # Execute Gemini CLI
            self.log_progress(
                "Executing Gemini CLI", f"Working directory: {self.repo_dir}"
            )

            result = await asyncio.create_subprocess_exec(
                "gemini",
                "prompt",
                self.prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ,  # Includes GEMINI_API_KEY
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=30.0
                )
            except TimeoutError:
                result.terminate()
                await result.wait()
                raise RuntimeError("Gemini CLI execution timed out after 30 seconds")

            # Change back to original directory
            os.chdir(original_dir)

            if result.returncode == 0:
                # Gemini CLI returns plain text output
                response = stdout.decode().strip()
                self.log(
                    "Gemini CLI response received",
                    "INFO",
                    response_length=len(response),
                )

                # Persist stdout to database
                if self.db_service and response:
                    await self.db_service.write_agent_output(
                        run_id=self.run_id,
                        variation_id=int(self.variation_id),
                        content=response,
                        output_type="stdout",
                        metadata={"source": "gemini_cli"}
                    )

                # Stream the response line by line
                for line in response.split("\n"):
                    if line.strip():
                        print(f"🔸 {line}", flush=True)

                # Write analytics data for Gemini CLI
                if self.db_service:
                    try:
                        request_end_time = datetime.now(UTC)
                        analytics_data = {
                            "model": "gemini-cli",
                            "provider": "google",
                            "stream": False,
                            "status": "success",
                            "request_end_time": request_end_time,
                            "response_time_ms": int((request_end_time - datetime.now(UTC)).total_seconds() * 1000),
                            "metadata": {
                                "agent_mode": "gemini-cli",
                                "response_length": len(response),
                                "working_directory": str(self.repo_dir),
                            }
                        }
                        
                        await self.db_service.write_litellm_analytics(
                            run_id=self.run_id,
                            variation_id=int(self.variation_id),
                            analytics_data=analytics_data
                        )
                        self.log(
                            "Wrote Gemini CLI analytics to database",
                            "INFO",
                            analytics_summary=analytics_data
                        )
                    except Exception as analytics_error:
                        self.log(
                            f"Failed to write Gemini CLI analytics: {analytics_error}",
                            "ERROR"
                        )

                return response
            error_msg = stderr.decode() if stderr else "Unknown error"
            
            # Persist stderr to database
            if self.db_service and error_msg:
                await self.db_service.write_agent_output(
                    run_id=self.run_id,
                    variation_id=int(self.variation_id),
                    content=error_msg,
                    output_type="stderr",
                    metadata={"source": "gemini_cli", "exit_code": result.returncode}
                )
            
            raise RuntimeError(
                f"Gemini CLI failed with exit code {result.returncode}: {error_msg}"
            )

        except Exception as e:
            self.log_error("Gemini CLI execution failed", e)
            raise RuntimeError(f"Failed to generate Gemini CLI response: {e}") from e

    async def _generate_openai_codex_response(self) -> str:
        """Generate response using OpenAI Codex CLI."""
        self.log_progress(
            "Generating response using OpenAI Codex CLI",
            "Executing codex in full-auto quiet mode for one-shot execution",
        )

        try:
            # Track start time for analytics
            request_start_time = datetime.now(UTC)
            
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.repo_dir)

            # Execute OpenAI Codex CLI
            self.log_progress(
                "Executing OpenAI Codex CLI", f"Working directory: {self.repo_dir}"
            )

            # Use codex in full-auto quiet mode for containerized CI/CD environment
            result = await asyncio.create_subprocess_exec(
                "codex",
                "--full-auto",
                "--quiet",
                self.prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ,  # Includes OPENAI_API_KEY
            )

            # Wait for completion with timeout (increased for code analysis)
            try:
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=120.0
                )
            except TimeoutError:
                result.terminate()
                await result.wait()
                self.log_error("OpenAI Codex CLI execution timed out after 120 seconds", None)
                raise RuntimeError("OpenAI Codex CLI execution timed out after 120 seconds")

            # Change back to original directory
            os.chdir(original_dir)

            # Handle output
            if result.returncode == 0:
                response_text = stdout.decode("utf-8")
                self.log_progress(
                    "OpenAI Codex CLI completed successfully",
                    f"Generated {len(response_text)} characters",
                )

                # Stream the response line by line for consistency with other CLI tools
                for line in response_text.split("\n"):
                    if line.strip():
                        print(f"🔥 {line}", flush=True)
                
                # Persist output to database
                if self.db_service:
                    await self.db_service.write_agent_output(
                        run_id=self.run_id,
                        variation_id=int(self.variation_id),
                        content=response_text,
                        output_type="stdout",
                        metadata={"source": "openai_codex_cli", "exit_code": result.returncode}
                    )

                # Write analytics data for OpenAI Codex CLI
                if self.db_service:
                    try:
                        request_end_time = datetime.now(UTC)
                        response_time_ms = int((request_end_time - request_start_time).total_seconds() * 1000)
                        analytics_data = {
                            "model": "openai-codex-cli",
                            "provider": "openai",
                            "stream": False,
                            "status": "success",
                            "request_end_time": request_end_time,
                            "response_time_ms": response_time_ms,
                            "metadata": {
                                "agent_mode": "openai-codex",
                                "response_length": len(response_text),
                                "working_directory": str(self.repo_dir),
                                "codex_flags": ["--full-auto", "--quiet"]
                            }
                        }
                        
                        await self.db_service.write_litellm_analytics(
                            run_id=self.run_id,
                            variation_id=int(self.variation_id),
                            analytics_data=analytics_data
                        )
                        self.log(
                            "Wrote OpenAI Codex CLI analytics to database",
                            "INFO",
                            analytics_summary=analytics_data
                        )
                    except Exception as analytics_error:
                        self.log(
                            f"Failed to write OpenAI Codex CLI analytics: {analytics_error}",
                            "ERROR"
                        )
                
                return response_text
            else:
                error_msg = stderr.decode("utf-8")
                self.log_error(
                    "OpenAI Codex CLI process failed",
                    f"Exit code: {result.returncode}, Error: {error_msg}",
                )
                # Persist stderr to database
                if self.db_service and error_msg:
                    await self.db_service.write_agent_output(
                        run_id=self.run_id,
                        variation_id=int(self.variation_id),
                        content=error_msg,
                        output_type="stderr",
                        metadata={"source": "openai_codex_cli", "exit_code": result.returncode}
                    )
                raise RuntimeError(
                    f"OpenAI Codex CLI failed with exit code {result.returncode}: {error_msg}"
                )

        except Exception as e:
            self.log_error("OpenAI Codex CLI execution failed", e)
            raise RuntimeError(f"Failed to generate OpenAI Codex CLI response: {e}") from e

    async def _generate_litellm_response(self, codebase_summary: str | None) -> str:
        """Generate response using LiteLLM (original implementation)."""
        self.log(
            "Generating LLM response",
            "INFO",
            step="llm_start",
            model=self.config["model"],
            temperature=self.config["temperature"],
        )

        try:
            # Prepare the full prompt based on mode
            if codebase_summary is not None:
                # Code mode: Include codebase analysis
                full_prompt = f"""
You are an expert software engineer analyzing a codebase. Here's the codebase analysis:

{codebase_summary}

User Request: {self.prompt}

Please provide a comprehensive analysis and recommendations. Focus on:
1. Understanding the codebase structure and purpose
2. Addressing the specific user request
3. Providing actionable recommendations
4. Identifying potential improvements or issues

Be thorough but concise in your response.
"""
            else:
                # Chat mode: Direct prompt without codebase context
                full_prompt = self.prompt

            # Make API call via LiteLLM Gateway with streaming
            self.log("Starting LLM streaming", "INFO", step="streaming_start")

            response_text = ""
            chunk_count = 0
            buffer = ""
            collected_chunks = []  # Collect chunks for usage extraction

            # Call THROUGH the LiteLLM Gateway
            # The gateway will handle routing to the actual provider
            # Get the provider API key for this model
            provider = self._get_model_provider(self.config["model"])
            provider_key_env = f"{provider.upper()}_API_KEY"
            api_key = os.getenv(provider_key_env)
            
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": f"🔧 Using provider={provider}, has_api_key={bool(api_key)}, gateway_key={self.gateway_key}"
            }), flush=True)
            
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 About to prepare completion kwargs"
            }), flush=True)
            
            # Use LiteLLM Gateway with clientside API key injection
            completion_kwargs = {
                "model": self.config["model"],
                "max_tokens": self.config["max_tokens"],
                "temperature": self.config["temperature"],
                "messages": [{"role": "user", "content": full_prompt}],
                "stream": True,
                "stream_options": {"include_usage": True},
                "api_base": self.gateway_url,  # Point to LiteLLM Gateway
                "api_key": self.gateway_key,   # Use Gateway master key for auth
            }
            
            # Pass provider API key via extra_body (clientside auth)
            if api_key:
                completion_kwargs["extra_body"] = {"api_key": api_key}
            
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": f"🔧 About to call acompletion with model={completion_kwargs['model']}"
            }), flush=True)
            
            response = await acompletion(**completion_kwargs)
            
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 acompletion call successful, starting to process stream"
            }), flush=True)
            
            # Debug: Verify response object
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": f"🔧 Response object type: {type(response)}"
            }), flush=True)

            # CRITICAL DEBUG: This should appear if we reach here
            print(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "DEBUG",
                "message": "🔧 REACHED AFTER acompletion - about to enter streaming loop"
            }), flush=True)
            
            # Add debug logging before streaming loop  
            self.log("🔧 About to enter async streaming loop", "DEBUG")
            
            async for chunk in response:
                # Collect chunk for usage extraction
                collected_chunks.append(chunk)

                # Extract text from chunk
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    response_text += chunk_text
                    chunk_count += 1
                    
                    # Debug log for first few chunks
                    if chunk_count <= 3:
                        self.log(f"🔧 Processing chunk #{chunk_count}: '{chunk_text}'", "DEBUG")

                    # Add to buffer
                    buffer += chunk_text

                    # Stream output in reasonable chunks
                    # Wait for complete lines or reasonable amount of content
                    while len(buffer) >= 200 or '\n' in buffer[:200]:
                        # If we have a newline, output up to that
                        newline_pos = buffer.find('\n')
                        if newline_pos != -1 and newline_pos < 200:
                            output_chunk = buffer[:newline_pos + 1]
                        else:
                            # Otherwise take a reasonable chunk
                            chunk_size = min(200, len(buffer))
                            output_chunk = buffer[:chunk_size]
                            
                            # Try to break at word boundary
                            space_pos = output_chunk.rfind(" ")
                            if space_pos > 100:  # Only adjust if we have substantial content
                                output_chunk = buffer[: space_pos + 1]

                        # Output to stdout (DatabaseStreamWriter handles database persistence)
                        print(output_chunk, end="", flush=True)
                        
                        # Stream to Redis only (database handled by DatabaseStreamWriter)
                        await self._publish_to_redis_only(output_chunk)
                        buffer = buffer[len(output_chunk) :]


            # Add debug logging after streaming loop
            self.log(f"🔧 Streaming loop completed, processed {chunk_count} chunks", "DEBUG")
            
            # Output any remaining buffer
            if buffer.strip():
                self.log(f"🔧 Outputting remaining buffer: '{buffer[:50]}...'", "DEBUG")
                import sys
                
                # Output remaining buffer
                print(buffer, end="", flush=True)
                
                # Stream to Redis only (database handled by DatabaseStreamWriter)
                await self._publish_to_redis_only(buffer)

            # Extract usage data from collected chunks and collect analytics
            tokens_used = None
            cost_usd = None
            provider = self._get_model_provider(self.config["model"])
            request_start_time = datetime.now(UTC)
            
            # Prepare analytics data
            analytics_data = {
                "model": self.config["model"],
                "provider": provider,
                "temperature": self.config.get("temperature"),
                "max_tokens": self.config.get("max_tokens"),
                "stream": True,
                "status": "success",
                "request_start_time": request_start_time,
                "metadata": {
                    "litellm_version": "proxy",
                    "gateway_url": self.gateway_url,
                    "agent_mode": "litellm",
                    "chunks_received": chunk_count,
                }
            }

            try:
                # Try to build complete response from chunks to get usage data
                if collected_chunks:
                    # Check if the last chunk has usage information
                    last_chunk = collected_chunks[-1] if collected_chunks else None
                    if last_chunk and hasattr(last_chunk, "usage") and last_chunk.usage:
                        tokens_used = last_chunk.usage.total_tokens
                        prompt_tokens = getattr(last_chunk.usage, "prompt_tokens", None)
                        completion_tokens = getattr(last_chunk.usage, "completion_tokens", None)
                        
                        # Update analytics data with token usage
                        analytics_data.update({
                            "total_tokens": tokens_used,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                        })
                        
                        self.log(
                            "Extracted token usage from stream",
                            "INFO",
                            tokens_used=tokens_used,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens
                        )

                        # Try to calculate cost
                        try:
                            # Create a mock response object for cost calculation
                            mock_response = type("obj", (object,), {
                                "model": self.config["model"],
                                "usage": last_chunk.usage
                            })()
                            cost_usd = completion_cost(completion_response=mock_response)
                            analytics_data["cost_usd"] = cost_usd
                            
                            self.log(
                                "Calculated completion cost",
                                "INFO",
                                cost_usd=cost_usd,
                                model=self.config["model"]
                            )
                        except Exception as cost_error:
                            self.log(
                                f"Failed to calculate cost: {cost_error}",
                                "WARNING"
                            )

                    # If no usage in last chunk, try to rebuild complete response
                    if tokens_used is None:
                        try:
                            complete_response = stream_chunk_builder(
                                chunks=collected_chunks,
                                messages=[{"role": "user", "content": full_prompt}]
                            )
                            if hasattr(complete_response, "usage") and complete_response.usage:
                                tokens_used = complete_response.usage.total_tokens
                                prompt_tokens = getattr(complete_response.usage, "prompt_tokens", None)
                                completion_tokens = getattr(complete_response.usage, "completion_tokens", None)
                                
                                # Calculate cost from complete response
                                cost_usd = completion_cost(completion_response=complete_response)
                                
                                # Update analytics data
                                analytics_data.update({
                                    "total_tokens": tokens_used,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "cost_usd": cost_usd,
                                })
                                
                                self.log(
                                    "Extracted usage from rebuilt response",
                                    "INFO",
                                    tokens_used=tokens_used,
                                    cost_usd=cost_usd
                                )
                        except Exception as rebuild_error:
                            self.log(
                                f"Failed to rebuild response for usage: {rebuild_error}",
                                "WARNING"
                            )

            except Exception as usage_error:
                self.log(
                    f"Failed to extract usage data: {usage_error}",
                    "WARNING"
                )
                analytics_data["status"] = "error"
                analytics_data["error_type"] = type(usage_error).__name__
                analytics_data["error_message"] = str(usage_error)

            # Calculate response time and performance metrics
            request_end_time = datetime.now(UTC)
            response_time_ms = int((request_end_time - request_start_time).total_seconds() * 1000)
            analytics_data.update({
                "request_end_time": request_end_time,
                "response_time_ms": response_time_ms,
            })
            
            # Calculate tokens per second if we have token data
            if tokens_used and response_time_ms > 0:
                tokens_per_second = (tokens_used / response_time_ms) * 1000
                analytics_data["tokens_per_second"] = tokens_per_second

            # Update run statistics if we have usage data
            if self.db_service and (tokens_used is not None or cost_usd is not None):
                try:
                    await self.db_service.update_run_stats(
                        run_id=self.run_id,
                        tokens_used=tokens_used,
                        cost_usd=cost_usd,
                        model=self.config["model"],
                        provider=provider
                    )
                    self.log(
                        "Updated run statistics in database",
                        "INFO",
                        tokens_used=tokens_used,
                        cost_usd=cost_usd
                    )
                except Exception as stats_error:
                    self.log(
                        f"Failed to update run statistics: {stats_error}",
                        "ERROR"
                    )
            
            # Write detailed LiteLLM analytics data
            if self.db_service:
                try:
                    await self.db_service.write_litellm_analytics(
                        run_id=self.run_id,
                        variation_id=int(self.variation_id),
                        analytics_data=analytics_data
                    )
                    self.log(
                        "Wrote LiteLLM analytics to database",
                        "INFO",
                        analytics_summary={
                            "model": analytics_data.get("model"),
                            "tokens": analytics_data.get("total_tokens"),
                            "cost": analytics_data.get("cost_usd"),
                            "response_time_ms": analytics_data.get("response_time_ms"),
                        }
                    )
                except Exception as analytics_error:
                    self.log(
                        f"Failed to write LiteLLM analytics: {analytics_error}",
                        "ERROR"
                    )

            self.log(
                "Streaming LLM response complete",
                "INFO",
                step="streaming_complete",
                chunks_received=chunk_count,
                total_length=len(response_text),
                tokens_used=tokens_used,
                cost_usd=cost_usd
            )

            return response_text
                
        except Exception as api_error:
            # Handle specific API errors with user-friendly messages
            error_str = str(api_error).lower()

            if (
                "authentication" in error_str
                or "api key" in error_str
                or "unauthorized" in error_str
            ):
                provider = self._get_model_provider(self.config["model"])
                error_message = f"""
🔑 **Authentication Error**

The {provider.title()} API rejected the request due to authentication issues.

**Possible causes:**
- API key is invalid or expired
- API key lacks necessary permissions
- Model '{self.config["model"]}' requires a different tier of access

**Next steps:**
1. Verify your {provider.title()} API key is valid
2. Check if your API key has access to model '{self.config["model"]}'
3. Try using a different model from the same provider

Original error: {api_error!s}
"""
                print(error_message, flush=True)
                raise RuntimeError(
                    f"Authentication failed for {provider}: {api_error}"
                )

            if "rate limit" in error_str or "quota" in error_str:
                provider = self._get_model_provider(self.config["model"])
                error_message = f"""
⏱️ **Rate Limit Exceeded**

The {provider.title()} API rate limit has been exceeded.

**What this means:**
- Too many requests have been made to the API
- Your account may have reached its usage quota

**Next steps:**
1. Wait a few minutes and try again
2. Check your {provider.title()} account usage limits
3. Consider upgrading your API plan if needed

Original error: {api_error!s}
"""
                print(error_message, flush=True)
                raise RuntimeError(
                    f"Rate limit exceeded for {provider}: {api_error}"
                )

            if "model" in error_str and (
                "not found" in error_str or "does not exist" in error_str
            ):
                error_message = f"""
🤖 **Model Not Available**

The model '{self.config["model"]}' is not available or does not exist.

**Possible causes:**
- Model name is misspelled
- Model is not available in your region
- Model requires special access

**Next steps:**
1. Check the model name spelling
2. Try a different model like 'gpt-4o-mini' or 'claude-3-haiku'
3. Verify the model is available through your API provider

Original error: {api_error!s}
"""
                print(error_message, flush=True)
                raise RuntimeError(f"Model not available: {api_error}")

            # Generic error
            error_message = f"""
⚠️ **API Request Failed**

An error occurred while calling the model API.

**Error details:**
{api_error!s}

**Next steps:**
1. Check if the API service is available
2. Verify your internet connection
3. Try again in a few moments

If the problem persists, contact support with the error details above.
"""
            print(error_message, flush=True)
            raise RuntimeError(f"API request failed: {api_error}")



async def main():
    """Main entry point."""
    print(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "DEBUG",
        "message": "🔧 Starting main() function"
    }), flush=True)
    
    agent = AIdeatorAgent()
    print(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "DEBUG", 
        "message": "🔧 Agent initialized successfully"
    }), flush=True)
    
    try:
        # Run the agent
        print(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "DEBUG",
            "message": "🔧 About to call agent.run()"
        }), flush=True)
        await agent.run()

        # Publish completion status
        await agent.publish_status(
            "variation_completed", {"variation_id": agent.variation_id, "success": True}
        )

        # Sleep for 30 seconds before exit on success (to allow final logs to flush)
        agent.log("⏱️ Sleeping for 30 seconds before exit", "INFO")
        await asyncio.sleep(30)

        # Wait for any background tasks to complete
        if hasattr(agent, '_bg_tasks') and agent._bg_tasks:
            agent.log(f"⏳ Waiting for {len(agent._bg_tasks)} background tasks to complete", "INFO")
            await asyncio.gather(*agent._bg_tasks, return_exceptions=True)
        
        # Clean up connections
        if agent.redis_client:
            await agent.redis_client.close()
        if agent.db_service:
            await agent.db_service.disconnect()
        sys.exit(0)
    except Exception as e:
        # Ensure error is visible in logs
        agent.log(f"💥 Fatal error: {e!s}", "ERROR", exception_type=type(e).__name__)
        # Log failure and exit immediately
        agent.log("❌ Agent failed", "INFO", status="failed")
        agent.log("🏁 Exiting agent container", "INFO")
        sys.exit(1)
    finally:
        # Restore original stdout/stderr
        if isinstance(sys.stdout, DatabaseStreamWriter):
            sys.stdout.flush()
            sys.stdout = sys.stdout.original_stream
        if isinstance(sys.stderr, DatabaseStreamWriter):
            sys.stderr.flush()
            sys.stderr = sys.stderr.original_stream
        
        # Wait for any remaining background tasks
        if hasattr(agent, '_bg_tasks') and agent._bg_tasks:
            try:
                await asyncio.gather(*agent._bg_tasks, return_exceptions=True)
            except Exception:
                pass  # Best effort
            
        # Clean up temp directory
        if hasattr(agent, "work_dir") and agent.work_dir.exists():
            try:
                shutil.rmtree(agent.work_dir)
            except Exception:
                pass  # Best effort cleanup


if __name__ == "__main__":
    asyncio.run(main())
