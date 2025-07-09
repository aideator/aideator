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
            "model": os.getenv("MODEL", "gpt-4o-mini"),
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
        }
        
        # API key setup
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
        
        # Log agent mode
        agent_mode = os.getenv("AGENT_MODE", "litellm")
        self.log(f"🎯 Agent mode: {agent_mode}", "INFO", agent_mode=agent_mode)
        
        # Log CLI tool versions
        claude_version = self._get_cli_version("claude")
        self.log(f"🤖 Claude CLI version: {claude_version}", "INFO", claude_version=claude_version)
        
        gemini_version = self._get_cli_version("gemini")
        self.log(f"💎 Gemini CLI version: {gemini_version}", "INFO", gemini_version=gemini_version)
        
        # Log LiteLLM SDK configuration
        self.log("🔧 Using LiteLLM SDK", "INFO", 
                 provider="openai",
                 note="Direct SDK usage - no proxy needed")
        
        # Log file location to file only, not stdout
        self.log(f"Debug logs location: {self.log_file}", "INFO")
        
        try:
            # Clone repository
            await self._clone_repository()
            
            # Analyze codebase
            codebase_summary = await self._analyze_codebase()
            
            # Generate response with LLM
            response = await self._generate_llm_response(codebase_summary)
            
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
    
    async def _generate_litellm_response(self, codebase_summary: str) -> str:
        """Generate response using LiteLLM (original implementation)."""
        self.log("Generating LLM response", "INFO", 
                step="llm_start", 
                model=self.config['model'], 
                temperature=self.config['temperature'])
        
        try:
            # Prepare the full prompt
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
            
            # Make API call via LiteLLM with streaming
            self.log("Starting LLM streaming", "INFO", step="streaming_start")
            
            response_text = ""
            chunk_count = 0
            buffer = ""
            
            async for chunk in await acompletion(
                model=f"openai/{self.config['model']}",
                max_tokens=self.config["max_tokens"],
                temperature=self.config["temperature"],
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                stream=True  # Enable streaming
            ):
                # Extract text from chunk
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    response_text += chunk_text
                    chunk_count += 1
                    
                    # Add to buffer
                    buffer += chunk_text
                    
                    # Stream output line by line
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():  # Only output non-empty lines
                            print(f"🔸 {line}", flush=True)
                    
                    # Also output partial lines periodically
                    if len(buffer) > 100:
                        print(f"🔸 {buffer}", flush=True)
                        buffer = ""
            
            # Output any remaining buffer
            if buffer.strip():
                print(f"🔸 {buffer}", flush=True)
            
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
        # Sleep for 600 seconds (10 minutes) before exit on success
        agent.log("⏱️ Sleeping for 600 seconds before exit", "INFO")
        await asyncio.sleep(600)
    except Exception as e:
        # Ensure error is visible in logs
        agent.log(f"💥 Fatal error: {str(e)}", "ERROR", 
                 exception_type=type(e).__name__)
        # Sleep for 600 seconds even on error
        agent.log("⏱️ Sleeping for 600 seconds before exit (after error)", "INFO")
        await asyncio.sleep(600)
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
