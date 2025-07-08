#!/usr/bin/env python3
"""
AIdeator Agent - Containerized LLM agent for code analysis and generation.
Runs inside Kubernetes jobs and streams output via stdout.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import git
from litellm import acompletion
from tenacity import retry, stop_after_attempt, wait_exponential


class AideatorAgent:
    """Containerized agent for LLM-based code analysis."""
    
    def __init__(self):
        # Set OpenAI API key for LiteLLM to use
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
        
        if not os.environ["OPENAI_API_KEY"]:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.repo_url = os.getenv("REPO_URL")
        self.prompt = os.getenv("PROMPT")
        self.variation_id = int(os.getenv("VARIATION_ID", "0"))
        self.run_id = os.getenv("RUN_ID", "unknown")
        if not self.repo_url:
            raise ValueError("REPO_URL environment variable is required")
        if not self.prompt:
            raise ValueError("PROMPT environment variable is required")
        
        # Using LiteLLM SDK directly for true BYOK - no proxy needed
        # LiteLLM will use the OPENAI_API_KEY from environment
        self.workspace = Path("/workspace")
        self.repo_dir = self.workspace / f"repo-{self.run_id}-{self.variation_id}"
        
        # Agent configuration based on variation
        self.config = self._get_variation_config()
    
    def _get_variation_config(self) -> Dict[str, Any]:
        """Get configuration for this agent variation."""
        # Using OpenAI's GPT-4o-mini model via LiteLLM
        configs = [
            {"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 4000},
            {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 4000},
            {"model": "gpt-4o-mini", "temperature": 0.9, "max_tokens": 4000},
            {"model": "gpt-4o-mini", "temperature": 0.5, "max_tokens": 4000},
            {"model": "gpt-4o-mini", "temperature": 0.1, "max_tokens": 4000},
        ]
        return configs[self.variation_id % len(configs)]
    
    def log(self, message: str, level: str = "INFO", **kwargs) -> None:
        """Log a structured message to stdout."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "run_id": self.run_id,
            "variation_id": self.variation_id,
            "message": message,
            **kwargs
        }
        print(json.dumps(log_entry), flush=True)
    
    def log_progress(self, step: str, details: Optional[str] = None) -> None:
        """Log progress information."""
        self.log(f"🔄 {step}", "PROGRESS", step=step, details=details)
    
    def log_result(self, result: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log agent result."""
        self.log(f"✅ {result}", "RESULT", result=result, metadata=metadata or {})
    
    def log_error(self, error: str, exception: Optional[Exception] = None) -> None:
        """Log error information."""
        error_data = {"error": error}
        if exception:
            error_data["exception"] = str(exception)
            error_data["exception_type"] = type(exception).__name__
        self.log(f"❌ {error}", "ERROR", **error_data)
    
    async def run(self) -> None:
        """Main agent execution flow."""
        self.log(f"🚀 Starting AIdeator Agent", "INFO", config=self.config)
        
        # Log LiteLLM SDK configuration
        self.log("🔧 Using LiteLLM SDK", "INFO", 
                 provider="openai",
                 note="Direct SDK usage - no proxy needed")
        
        try:
            # Step 1: Clone repository
            await self._clone_repository()
            
            # Step 2: Analyze codebase
            codebase_summary = await self._analyze_codebase()
            
            # Step 3: Generate response using LLM
            response = await self._generate_llm_response(codebase_summary)
            
            # Step 4: Log final result
            self.log_result("Agent execution completed successfully", {
                "response_length": len(response),
                "model": self.config["model"],
                "temperature": self.config["temperature"]
            })
            
            # Output the actual response
            print("\n" + "="*50)
            print("AGENT RESPONSE:")
            print("="*50)
            print(response)
            print("="*50)
            
        except Exception as e:
            self.log_error("Agent execution failed", e)
            sys.exit(1)
    
    async def _clone_repository(self) -> None:
        """Clone the target repository."""
        self.log_progress("Cloning repository", self.repo_url)
        
        try:
            # Ensure workspace exists
            self.workspace.mkdir(parents=True, exist_ok=True)
            
            # Remove existing repo directory if it exists
            if self.repo_dir.exists():
                import shutil
                shutil.rmtree(self.repo_dir)
            
            # Clone repository
            repo = git.Repo.clone_from(
                self.repo_url,
                self.repo_dir,
                depth=1  # Shallow clone for efficiency
            )
            
            self.log_progress("Repository cloned successfully", f"Path: {self.repo_dir}")
            
            # Log repository statistics
            file_count = sum(1 for _ in self.repo_dir.rglob("*") if _.is_file())
            self.log("📊 Repository statistics", "INFO", 
                    file_count=file_count, 
                    repo_size_mb=self._get_directory_size(self.repo_dir))
            
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    async def _analyze_codebase(self) -> str:
        """Analyze the cloned codebase."""
        self.log_progress("Analyzing codebase structure")
        
        try:
            # Get file tree
            file_tree = self._get_file_tree()
            
            # Get key files content
            key_files = self._get_key_files()
            
            # Build codebase summary
            summary = f"""
# Codebase Analysis

## Repository: {self.repo_url}
## Files: {len(key_files)} key files analyzed

## File Structure:
{file_tree}

## Key Files Content:
"""
            
            for file_path, content in key_files.items():
                summary += f"\n### {file_path}\n```\n{content[:2000]}{'...' if len(content) > 2000 else ''}\n```\n"
            
            self.log_progress("Codebase analysis completed", 
                            f"Analyzed {len(key_files)} files")
            
            return summary
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze codebase: {e}")
    
    def _get_file_tree(self) -> str:
        """Generate a file tree representation."""
        tree_lines = []
        
        def add_to_tree(path: Path, prefix: str = ""):
            if path.is_file():
                tree_lines.append(f"{prefix}📄 {path.name}")
            elif path.is_dir() and not path.name.startswith('.'):
                tree_lines.append(f"{prefix}📁 {path.name}/")
                children = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                for i, child in enumerate(children[:10]):  # Limit depth
                    is_last = i == len(children) - 1
                    new_prefix = prefix + ("└── " if is_last else "├── ")
                    add_to_tree(child, new_prefix)
                if len(children) > 10:
                    tree_lines.append(f"{prefix}... ({len(children) - 10} more items)")
        
        add_to_tree(self.repo_dir)
        return "\n".join(tree_lines[:50])  # Limit output
    
    def _get_key_files(self) -> Dict[str, str]:
        """Extract content from key files."""
        key_patterns = [
            "*.py", "*.js", "*.ts", "*.tsx", "*.jsx",
            "*.go", "*.rs", "*.java", "*.cpp", "*.c", "*.h",
            "README*", "*.md", "*.json", "*.yaml", "*.yml",
            "Dockerfile*", "*.toml", "requirements.txt", "package.json"
        ]
        
        key_files = {}
        
        for pattern in key_patterns:
            for file_path in self.repo_dir.rglob(pattern):
                if file_path.is_file() and len(key_files) < 20:  # Limit files
                    try:
                        relative_path = file_path.relative_to(self.repo_dir)
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        key_files[str(relative_path)] = content
                    except Exception:
                        continue  # Skip files we can't read
        
        return key_files
    
    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB."""
        total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return round(total_size / (1024 * 1024), 2)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_llm_response(self, codebase_summary: str) -> str:
        """Generate LLM response based on codebase analysis."""
        self.log_progress("Generating LLM response", 
                         f"Model: {self.config['model']}, Temp: {self.config['temperature']}")
        
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
            self.log_progress("Starting LLM streaming", "Streaming response from model - UPDATED")
            
            response_text = ""
            chunk_count = 0
            
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
                    
                    # Log streaming progress every 10 chunks
                    if chunk_count % 10 == 0:
                        self.log_progress(
                            f"Streaming LLM response",
                            f"chunks_received: {chunk_count}, chars_so_far: {len(response_text)}"
                        )
                    
                    # Also print the chunk for real-time visibility
                    print(chunk_text, end='', flush=True)
            
            print()  # New line after streaming
            self.log_progress("LLM streaming completed", 
                            f"Total chunks: {chunk_count}, Length: {len(response_text)} characters")
            
            return response_text
            
        except Exception as e:
            self.log_error(f"LLM API call failed", e)
            raise RuntimeError(f"Failed to generate LLM response: {e}")


async def main():
    """Main entry point."""
    agent = AideatorAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())