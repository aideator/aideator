"""
Subprocess-based provider base class.

Provides common subprocess execution and streaming logic for all CLI-based providers.
"""

import asyncio
import json
from abc import abstractmethod
from typing import Any

from agent.providers.base import BaseProvider
from agent.utils.errors import ProviderError


class SubprocessProvider(BaseProvider):
    """Base class for subprocess-based providers."""

    def __init__(self, config, output_writer):
        """Initialize subprocess provider."""
        super().__init__(config, output_writer)
        self.chunk_read_size = 1024
        self.default_timeout = 300.0  # 5 minutes

    @abstractmethod
    def build_command_args(self, prompt: str, context: str | None = None) -> list[str]:
        """Build command arguments for the subprocess.
        
        Args:
            prompt: User prompt
            context: Optional codebase analysis context
            
        Returns:
            List of command arguments
        """

    @abstractmethod
    def parse_output_line(self, line: str, collected_output: list[str]) -> bool:
        """Parse a single output line from the subprocess.
        
        Args:
            line: Output line to parse
            collected_output: List to append parsed content to
            
        Returns:
            True if line was parsed successfully, False otherwise
        """

    async def execute_subprocess_with_streaming(
        self,
        args: list[str],
        timeout: float | None = None
    ) -> str:
        """Execute subprocess with real-time streaming.
        
        Args:
            args: Command arguments
            timeout: Optional timeout in seconds
            
        Returns:
            Complete output from subprocess
            
        Raises:
            ProviderError: If subprocess execution fails
        """
        timeout = timeout or self.default_timeout

        await self.write_job_data(f"🔧 Executing: {args[0]} {' '.join(args[1:3])}")  # Show first few args

        try:
            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )

            # Close stdin immediately
            if process.stdin:
                process.stdin.close()

            # Stream processing variables
            collected_output = []
            buffer = ""
            data_chunks = 0
            total_bytes = 0

            await self.write_job_data(f"🚀 Process started (PID: {process.pid})")

            try:
                # Read stdout in real-time chunks with timeout
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            process.stdout.read(self.chunk_read_size),
                            timeout=timeout
                        )
                        if not chunk:
                            break
                    except TimeoutError:
                        process.terminate()
                        await process.wait()
                        error_msg = f"❌ Process timed out after {timeout} seconds"
                        await self.write_error(error_msg)
                        raise ProviderError(f"Subprocess execution timed out after {timeout} seconds")

                    data_chunks += 1
                    total_bytes += len(chunk)

                    chunk_text = chunk.decode("utf-8", errors="ignore")

                    # Process the chunk immediately (streaming approach)
                    buffer += chunk_text
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # Keep incomplete line in buffer

                    for line in lines:
                        if line.strip():
                            parsed = await self.parse_output_line(line, collected_output)
                            if not parsed:
                                # If not parsed by specific provider, treat as plain text
                                print(line, flush=True)
                                await self.write_job_data(line + "\n")
                                collected_output.append(line + "\n")

                # Handle any remaining buffer content
                if buffer.strip():
                    await self.write_job_data(f"📝 Final buffer: {buffer[:50]}{'...' if len(buffer) > 50 else ''}")
                    print(buffer, flush=True)
                    await self.write_job_data(buffer)
                    collected_output.append(buffer)

                # Wait for process to complete
                await process.wait()

                # Handle stderr if there were errors
                if process.returncode != 0:
                    stderr_output = await process.stderr.read()
                    error_msg = stderr_output.decode() if stderr_output else "Unknown error"

                    full_error = f"❌ {self.get_provider_name()} failed (exit code: {process.returncode}): {error_msg}"
                    await self.write_error(full_error)

                    # Still return collected output if we got some
                    if collected_output:
                        await self.write_job_data(f"⚠️ Returning partial output despite error. Collected {len(collected_output)} chunks")
                        return "".join(collected_output)

                    raise ProviderError(f"{self.get_provider_name()} failed with exit code {process.returncode}: {error_msg}")

                # Success case
                response = "".join(collected_output)
                await self.write_job_data(
                    f"✅ {self.get_provider_name()} completed successfully. Chunks: {data_chunks}, Bytes: {total_bytes}, Response: {len(response)} chars"
                )

                return response if response else f"No output received from {self.get_provider_name()}"

            except Exception as stream_error:
                # Clean up process if still running
                if process.returncode is None:
                    process.terminate()
                    await process.wait()
                raise stream_error

        except Exception as e:
            error_msg = f"❌ {self.get_provider_name()} execution failed: {e}"
            await self.write_error(error_msg)
            raise ProviderError(f"Failed to generate {self.get_provider_name()} response: {e}") from e

    async def parse_output_line(self, line: str, collected_output: list[str]) -> bool:
        """Default output line parsing - can be overridden by subclasses.
        
        Args:
            line: Output line to parse
            collected_output: List to append parsed content to
            
        Returns:
            True if line was parsed, False if should be treated as plain text
        """
        try:
            # Try to parse as JSON first
            json_data = json.loads(line)
            return await self._parse_json_output(json_data, collected_output)
        except json.JSONDecodeError:
            # Not JSON, let subclass handle or treat as plain text
            return False

    async def _parse_json_output(self, json_data: dict[str, Any], collected_output: list[str]) -> bool:
        """Parse JSON output - can be overridden by subclasses.
        
        Args:
            json_data: Parsed JSON data
            collected_output: List to append parsed content to
            
        Returns:
            True if JSON was parsed successfully
        """
        # Default JSON parsing for common formats
        await self.write_job_data(f"📋 JSON message type: {json_data.get('type', 'unknown')}")

        # Handle common JSON formats
        if json_data.get("type") == "assistant" and json_data.get("message", {}).get("content"):
            for content_item in json_data["message"]["content"]:
                if content_item.get("type") == "text" and content_item.get("text"):
                    text_content = content_item["text"]
                    print(text_content, end="", flush=True)
                    await self.write_job_data(text_content)
                    collected_output.append(text_content)
            return True
        if json_data.get("type") == "error":
            error_msg = json_data.get("error", "Unknown error")
            await self.write_error(f"❌ {self.get_provider_name()} error: {error_msg}")
            raise ProviderError(f"{self.get_provider_name()} error: {error_msg}")

        return False

    async def generate_response(self, prompt: str, context: str | None = None) -> str:
        """Generate response using subprocess execution.
        
        Args:
            prompt: User prompt
            context: Optional codebase analysis context
            
        Returns:
            Generated response text
        """
        await self.write_job_data(f"🤖 Starting {self.get_provider_name()} generation")

        # Build command arguments
        args = self.build_command_args(prompt, context)

        # Execute subprocess with streaming
        return await self.execute_subprocess_with_streaming(args)
