#!/usr/bin/env python
"""
AIdeator Agent - Containerized LLM agent for code analysis and generation.
Runs inside Kubernetes jobs and streams output via stdout.
"""

import asyncio
import json
import os
import sys
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

import git
from litellm import acompletion
from tenacity import retry, stop_after_attempt, wait_exponential
import aiofiles


class AIdeatorAgent:
    """Main agent class for repository analysis and code generation."""
    
    def __init__(self):
        """Initialize agent with configuration from environment."""
        self.run_id = os.getenv("RUN_ID", "local-test")
        self.variation_id = os.getenv("VARIATION_ID", "0")
        self.repo_url = os.getenv("REPO_URL", "")
        self.prompt = os.getenv("PROMPT", "Analyze this repository")
        
        # LLM configuration
        self.config = {
            "model": os.getenv("MODEL", "gpt-4"),
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
        }
        
        # LiteLLM Gateway configuration
        self.gateway_url = os.getenv("LITELLM_GATEWAY_URL", "http://aideator-litellm:4000")
        self.gateway_key = os.getenv("LITELLM_GATEWAY_KEY", "sk-1234")
        
        # API key setup (for direct calls if needed)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        # Working directory
        self.work_dir = Path("/tmp/agent-workspace")
        self.work_dir.mkdir(exist_ok=True)
        self.repo_dir = self.work_dir / "repo"
        
        # Setup logging to file only (not stdout to avoid mixing with LLM output)
        self.log_file = self.work_dir / f"agent_{self.run_id}_{self.variation_id}.log"
        self._setup_file_logging()
        
        # Check available API keys for graceful error handling
        self.available_api_keys = self._check_available_api_keys()
    
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
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.file_logger.addHandler(fh)
        
        # Prevent propagation to root logger (which might log to stdout)
        self.file_logger.propagate = False
    
    def _check_available_api_keys(self) -> dict:
        """Check which API keys are available for different providers."""
        available_keys = {}
        
        # Check OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.strip() and openai_key != "sk-" and len(openai_key) > 10:
            available_keys["openai"] = True
        else:
            available_keys["openai"] = False
            
        # Check Anthropic API Key  
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key.strip() and anthropic_key.startswith("sk-ant-"):
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
            ("deepseek", "DEEPSEEK_API_KEY")
        ]:
            key = os.getenv(env_var)
            available_keys[provider] = bool(key and key.strip() and len(key) > 5)
            
        return available_keys
    
    def _get_model_provider(self, model_name: str) -> str:
        """Get the provider for a given model name."""
        model_lower = model_name.lower()
        
        if model_lower.startswith(("gpt", "openai", "o1")):
            return "openai"
        elif model_lower.startswith(("claude", "anthropic")):
            return "anthropic" 
        elif model_lower.startswith(("gemini", "google")):
            return "gemini"
        elif model_lower.startswith(("mistral", "mixtral")):
            return "mistral"
        elif model_lower.startswith("cohere"):
            return "cohere"
        elif model_lower.startswith("groq"):
            return "groq"
        elif model_lower.startswith("perplexity"):
            return "perplexity"
        elif model_lower.startswith("deepseek"):
            return "deepseek"
        else:
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
                "deepseek": "DeepSeek"
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
        available_providers = [provider for provider, available in self.available_api_keys.items() if available]
        
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
                suggestions.append("- Mistral: mistral-large-latest, mistral-small-latest")
            elif provider == "cohere":
                suggestions.append("- Cohere: command-r-plus, command-r")
            elif provider == "groq":
                suggestions.append("- Groq: llama3-8b-8192")
            elif provider == "perplexity":
                suggestions.append("- Perplexity: llama-3.1-sonar-small-128k-online")
            elif provider == "deepseek":
                suggestions.append("- DeepSeek: deepseek-chat")
        
        return f"**Available models with configured API keys:**\n" + "\n".join(suggestions)
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """
        Structured logging with JSON output.
        This goes to stdout for kubectl logs streaming.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "level": level,
            "message": message,
            **kwargs
        }
        
        # Output to stdout for streaming
        print(json.dumps(log_entry), flush=True)
        
        # Also log to file
        self.file_logger.log(
            getattr(logging, level, logging.INFO),
            f"{message} | {json.dumps(kwargs) if kwargs else ''}"
        )
    
    def log_progress(self, message: str, detail: str = ""):
        """Log progress updates for user visibility."""
        self.log(f"⚡ {message}", "INFO", detail=detail)
    
    def log_error(self, error: str, exception: Optional[Exception] = None):
        """Log errors with details."""
        error_data = {"error": error}
        if exception:
            error_data["exception"] = str(exception)
            error_data["exception_type"] = type(exception).__name__
        self.log(f"❌ {error}", "ERROR", **error_data)
    
    async def run(self) -> None:
        """Main agent execution flow."""
        self.log(f"🚀 Starting AIdeator Agent", "INFO", config=self.config)
        
        # Log available API keys for debugging
        self.log("🔑 API Key availability check", "INFO", available_keys=self.available_api_keys)
        
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
                self.log(f"🤖 Claude CLI version: {claude_version}", "INFO", claude_version=claude_version)
            elif agent_mode == "gemini-cli":
                gemini_version = self._get_cli_version("gemini")
                self.log(f"💎 Gemini CLI version: {gemini_version}", "INFO", gemini_version=gemini_version)
        
        # Log LiteLLM Gateway configuration
        self.log("🔧 Using LiteLLM Gateway", "INFO", 
                 gateway_url=self.gateway_url,
                 model=self.config["model"],
                 note="Routing through LiteLLM Gateway for unified API access")
        
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
            self.log("✅ Generation complete", "INFO", 
                    response_length=len(response),
                    status="success")
            
        except Exception as e:
            self.log_error("Agent execution failed", e)
            raise
    
    async def _clone_repository(self) -> None:
        """Clone the repository to analyze."""
        self.log_progress("Cloning repository", self.repo_url)
        
        try:
            if self.repo_dir.exists():
                import shutil
                shutil.rmtree(self.repo_dir)
            
            # Clone with minimal depth
            git.Repo.clone_from(
                self.repo_url, 
                self.repo_dir,
                depth=1,
                single_branch=True
            )
            
            self.log_progress("Repository cloned successfully", 
                            f"Size: {self._get_directory_size(self.repo_dir)} MB")
            
        except Exception as e:
            self.log_error(f"Failed to clone repository", e)
            raise RuntimeError(f"Repository clone failed: {e}")
    
    async def _analyze_codebase(self) -> str:
        """Analyze the codebase structure and content."""
        self.log_progress("Analyzing codebase structure")
        
        analysis = {
            "files": [],
            "total_files": 0,
            "total_size_mb": 0,
            "languages": {},
            "key_files": []
        }
        
        try:
            # Walk through repository
            for root, dirs, files in os.walk(self.repo_dir):
                # Skip hidden and vendor directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'vendor', '__pycache__']]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                        
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.repo_dir)
                    
                    # Track file extension
                    ext = file_path.suffix.lower()
                    if ext:
                        analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                    
                    analysis["total_files"] += 1
                    
                    # Add file info
                    file_info = {
                        "path": str(relative_path),
                        "size": file_path.stat().st_size
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
            for key_file in analysis["key_files"][:10]:  # Limit to top 10 files
                file_path = self.repo_dir / key_file
                if file_path.exists() and file_path.stat().st_size < 50000:  # Skip large files
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = await f.read()
                            summary_parts.extend([
                                f"\n--- {key_file} ---",
                                content[:2000],  # First 2000 chars
                                "..." if len(content) > 2000 else "",
                                ""
                            ])
                    except Exception as e:
                        self.file_logger.warning(f"Failed to read {key_file}: {e}")
            
            summary = "\n".join(summary_parts)
            
            self.log_progress("Codebase analysis complete", 
                            f"Files: {analysis['total_files']}, Size: {analysis['total_size_mb']}MB")
            
            return summary
            
        except Exception as e:
            self.log_error("Codebase analysis failed", e)
            raise RuntimeError(f"Failed to analyze codebase: {e}")
    
    def _identify_key_files(self) -> list:
        """Identify important files in the repository."""
        key_patterns = [
            "README*", "readme*",
            "package.json", "requirements.txt", "setup.py", "Cargo.toml", "go.mod",
            "Dockerfile", "docker-compose*",
            ".github/workflows/*",
            "main.*", "app.*", "index.*",
            "config.*", "settings.*"
        ]
        
        key_files = []
        for pattern in key_patterns:
            if '*' in pattern:
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
        total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return round(total_size / (1024 * 1024), 2)
    
    def _get_cli_version(self, command: str) -> str:
        """Get version of a CLI tool."""
        try:
            result = subprocess.run(
                [command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except FileNotFoundError:
            return "Error: Command not found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_llm_response(self, codebase_summary: str) -> str:
        """Generate LLM response based on codebase analysis."""
        agent_mode = os.getenv("AGENT_MODE", "litellm")
        
        if agent_mode == "claude-cli":
            return await self._generate_claude_cli_response()
        elif agent_mode == "gemini-cli":
            return await self._generate_gemini_cli_response()
        else:
            return await self._generate_litellm_response(codebase_summary)
    
    async def _generate_claude_cli_response(self) -> str:
        """Generate response using Claude CLI."""
        self.log_progress("Generating response using Claude CLI", 
                         "Executing claude command with JSON output")
        
        try:
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.repo_dir)
            
            # Execute Claude CLI
            self.log_progress("Executing Claude CLI", f"Working directory: {self.repo_dir}")
            
            result = await asyncio.create_subprocess_exec(
                "claude",
                "-p",
                self.prompt,
                "--output-format",
                "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ  # Includes ANTHROPIC_API_KEY
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                result.terminate()
                await result.wait()
                raise RuntimeError("Claude CLI execution timed out after 30 seconds")
            
            # Change back to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                # Parse JSON output
                try:
                    response_data = json.loads(stdout.decode())
                    # Extract content from JSON structure
                    # The exact structure may vary, so we'll handle different possibilities
                    if isinstance(response_data, dict):
                        content = response_data.get("content", response_data.get("text", str(response_data)))
                    else:
                        content = str(response_data)
                    
                    self.log_progress("Claude CLI completed successfully", 
                                    f"Response length: {len(content)} characters")
                    return content
                    
                except json.JSONDecodeError as e:
                    self.log_error(f"Failed to parse Claude CLI JSON output", e)
                    # Fall back to raw output if JSON parsing fails
                    return stdout.decode()
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Claude CLI failed with exit code {result.returncode}: {error_msg}")
                
        except Exception as e:
            self.log_error(f"Claude CLI execution failed", e)
            raise RuntimeError(f"Failed to generate Claude CLI response: {e}")
    
    async def _generate_gemini_cli_response(self) -> str:
        """Generate response using Gemini CLI."""
        self.log_progress("Generating response using Gemini CLI", 
                         "Executing gemini command")
        
        try:
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.repo_dir)
            
            # Execute Gemini CLI
            self.log_progress("Executing Gemini CLI", f"Working directory: {self.repo_dir}")
            
            result = await asyncio.create_subprocess_exec(
                "gemini",
                "prompt",
                self.prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ  # Includes GEMINI_API_KEY
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                result.terminate()
                await result.wait()
                raise RuntimeError("Gemini CLI execution timed out after 30 seconds")
            
            # Change back to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                # Gemini CLI returns plain text output
                response = stdout.decode().strip()
                self.log("Gemini CLI response received", "INFO", 
                        response_length=len(response))
                
                # Stream the response line by line
                for line in response.split('\n'):
                    if line.strip():
                        print(f"🔸 {line}", flush=True)
                
                return response
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Gemini CLI failed with exit code {result.returncode}: {error_msg}")
                
        except Exception as e:
            self.log_error(f"Gemini CLI execution failed", e)
            raise RuntimeError(f"Failed to generate Gemini CLI response: {e}")
    
    async def _generate_litellm_response(self, codebase_summary: Optional[str]) -> str:
        """Generate response using LiteLLM (original implementation)."""
        self.log("Generating LLM response", "INFO", 
                step="llm_start", 
                model=self.config['model'], 
                temperature=self.config['temperature'])
        
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
            
            # Call THROUGH the LiteLLM Gateway
            # The gateway will handle routing to the actual provider
            try:
                response = await acompletion(
                    model=self.config['model'],  # Use model name directly, Gateway handles routing
                    max_tokens=self.config["max_tokens"],
                    temperature=self.config["temperature"],
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ],
                    stream=True,  # Enable streaming
                    api_base=self.gateway_url,  # Point to LiteLLM Gateway service
                    api_key=self.gateway_key,  # Use Gateway master key
                    # The gateway will use its own configured API keys to call providers
                )
            except Exception as api_error:
                # Handle specific API errors with user-friendly messages
                error_str = str(api_error).lower()
                
                if "authentication" in error_str or "api key" in error_str or "unauthorized" in error_str:
                    provider = self._get_model_provider(self.config['model'])
                    error_message = f"""
🔑 **Authentication Error**

The {provider.title()} API rejected the request due to authentication issues.

**Possible causes:**
- API key is invalid or expired
- API key lacks necessary permissions
- Model '{self.config['model']}' requires a different tier of access

**Next steps:**
1. Verify your {provider.title()} API key is valid
2. Check if your API key has access to model '{self.config['model']}'
3. Try using a different model from the same provider

Original error: {str(api_error)}
"""
                    print(error_message, flush=True)
                    raise RuntimeError(f"Authentication failed for {provider}: {api_error}")
                    
                elif "rate limit" in error_str or "quota" in error_str:
                    provider = self._get_model_provider(self.config['model'])
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

Original error: {str(api_error)}
"""
                    print(error_message, flush=True)
                    raise RuntimeError(f"Rate limit exceeded for {provider}: {api_error}")
                    
                elif "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
                    error_message = f"""
🤖 **Model Not Available**

The model '{self.config['model']}' is not available or does not exist.

**Possible causes:**
- Model name is misspelled
- Model is not available in your region
- Model requires special access

**Next steps:**
1. Check the model name spelling
2. Try a different model like 'gpt-4o-mini' or 'claude-3-haiku'
3. Verify the model is available through your API provider

Original error: {str(api_error)}
"""
                    print(error_message, flush=True)
                    raise RuntimeError(f"Model not available: {api_error}")
                    
                else:
                    # Generic error
                    error_message = f"""
⚠️ **API Request Failed**

An error occurred while calling the model API.

**Error details:**
{str(api_error)}

**Next steps:**
1. Check if the API service is available
2. Verify your internet connection
3. Try again in a few moments

If the problem persists, contact support with the error details above.
"""
                    print(error_message, flush=True)
                    raise RuntimeError(f"API request failed: {api_error}")
            
            async for chunk in response:
                # Extract text from chunk
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    response_text += chunk_text
                    chunk_count += 1
                    
                    # Add to buffer
                    buffer += chunk_text
                    
                    # Stream output more frequently for smoother experience
                    # Output smaller chunks (10-20 chars) instead of waiting for lines
                    while len(buffer) >= 15:
                        # Take a chunk, preferring to break at word boundaries
                        chunk_size = 15
                        output_chunk = buffer[:chunk_size]
                        
                        # Adjust chunk to end at word boundary if possible
                        space_pos = output_chunk.rfind(' ')
                        if space_pos > 8:  # Only adjust if we have a reasonable word
                            output_chunk = buffer[:space_pos + 1]
                        
                        # Output the chunk directly without emoji prefix for cleaner parsing
                        print(output_chunk, end='', flush=True)
                        buffer = buffer[len(output_chunk):]
                    
                    # Also check for newlines to maintain structure
                    if '\n' in buffer:
                        lines = buffer.split('\n')
                        for line in lines[:-1]:  # All complete lines
                            print(line, flush=True)
                        buffer = lines[-1]  # Keep the incomplete line
            
            # Output any remaining buffer
            if buffer.strip():
                print(buffer, end='', flush=True)
            
            self.log("Streaming LLM response complete", "INFO", 
                    step="streaming_complete",
                    chunks_received=chunk_count,
                    total_length=len(response_text))
            
            return response_text
            
        except Exception as e:
            self.log_error("LLM generation failed", e)
            raise RuntimeError(f"Failed to generate LLM response: {e}")


async def main():
    """Main entry point."""
    agent = AIdeatorAgent()
    try:
        await agent.run()
        # Log completion and exit immediately
        agent.log("✅ Agent completed successfully", "INFO", status="completed")
        agent.log("🏁 Exiting agent container", "INFO")
        sys.exit(0)
    except Exception as e:
        # Ensure error is visible in logs
        agent.log(f"💥 Fatal error: {str(e)}", "ERROR", 
                 exception_type=type(e).__name__)
        # Log failure and exit immediately
        agent.log("❌ Agent failed", "INFO", status="failed")
        agent.log("🏁 Exiting agent container", "INFO")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
