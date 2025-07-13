"""
Gemini CLI provider implementation.

Handles Gemini CLI execution with streaming and standardized output.
"""

import asyncio
import os
from typing import Optional

from agent.providers.base import BaseProvider
from agent.utils.errors import ProviderError


class GeminiCLIProvider(BaseProvider):
    """Gemini CLI provider for direct Gemini access."""
    
    def __init__(self, config, output_writer):
        """Initialize Gemini CLI provider."""
        super().__init__(config, output_writer)
        self.timeout_seconds = 30.0
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "gemini-cli"
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Gemini CLI.
        
        Args:
            prompt: User prompt
            context: Optional codebase analysis context (ignored for CLI)
            
        Returns:
            Generated response text
        """
        await self.write_job_data(f"💎 Starting Gemini CLI generation")
        
        try:
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.config.repo_dir)

            await self.write_job_data(f"📁 Working directory: {self.config.repo_dir}")

            # Execute Gemini CLI
            args = [
                "gemini",
                "prompt",
                prompt
            ]
            
            await self.write_job_data(f"🔧 Executing: {' '.join(args)}")

            result = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ,  # Includes GEMINI_API_KEY
            )

            await self.write_job_data(f"🚀 Gemini CLI process started (PID: {result.pid})")

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=self.timeout_seconds
                )
            except TimeoutError:
                result.terminate()
                await result.wait()
                error_msg = f"❌ Gemini CLI execution timed out after {self.timeout_seconds} seconds"
                await self.write_error(error_msg)
                raise ProviderError(f"Gemini CLI execution timed out after {self.timeout_seconds} seconds")

            # Change back to original directory
            os.chdir(original_dir)

            if result.returncode == 0:
                # Gemini CLI returns plain text output
                response = stdout.decode().strip()
                await self.write_job_data(f"📡 Gemini CLI response received ({len(response)} chars)")

                # Stream the response line by line for consistent output format
                for line in response.split("\n"):
                    if line.strip():
                        formatted_line = f"🔸 {line}"
                        print(formatted_line, flush=True)
                        await self.write_job_data(formatted_line + "\n")

                await self.write_job_data("✅ Gemini CLI completed successfully")
                return response
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                full_error = f"❌ Gemini CLI failed (exit code: {result.returncode}): {error_msg}"
                await self.write_error(full_error)
                raise ProviderError(f"Gemini CLI failed with exit code {result.returncode}: {error_msg}")

        except Exception as e:
            error_msg = f"❌ Gemini CLI execution failed: {e}"
            await self.write_error(error_msg)
            raise ProviderError(f"Failed to generate Gemini CLI response: {e}") from e