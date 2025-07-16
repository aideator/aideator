"""
Claude CLI provider implementation.

Handles Claude CLI execution with streaming and standardized output.
"""

import asyncio
import contextlib
import json
import os
import builtins
from typing import Optional

from agent.providers.base import BaseProvider
from agent.utils.errors import ProviderError


class ClaudeCLIProvider(BaseProvider):
    """Claude CLI provider for direct Claude access."""
    
    def __init__(self, config, output_writer):
        """Initialize Claude CLI provider."""
        super().__init__(config, output_writer)
        self.chunk_read_size = 1024
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "claude-cli"
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Claude CLI with streaming.
        
        Args:
            prompt: User prompt
            context: Optional codebase analysis context (ignored for CLI)
            
        Returns:
            Generated response text
        """
        await self.output_writer.write_system_status("Starting Claude CLI generation")
        
        # Log API key for debugging (first 10 chars only)
        api_key = os.getenv("ANTHROPIC_API_KEY", "NOT_SET")
        masked_key = api_key[:10] + "..." if len(api_key) > 10 else api_key
        await self.output_writer.write_debug_info(f"Anthropic API key: {masked_key}")
        
        try:
            # Change to repository directory for context
            original_dir = os.getcwd()
            os.chdir(self.config.repo_dir)

            await self.output_writer.write_debug_info(f"Working directory: {self.config.repo_dir}")

            # Execute Claude CLI with streaming arguments
            args = [
                "claude",
                "--verbose",
                "--output-format",
                "stream-json",
                "--dangerously-skip-permissions",
                "-p",
                prompt,
            ]

            await self.output_writer.write_debug_info(f"Executing: {' '.join(args)}")

            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=os.environ,  # Includes ANTHROPIC_API_KEY
            )

            # Close stdin immediately since we're using -p flag
            process.stdin.close()

            # Stream processing variables
            collected_output = []
            buffer = ""
            data_chunks = 0
            total_bytes = 0

            await self.output_writer.write_system_status(f"Claude CLI process started (PID: {process.pid})")

            try:
                # Read stdout in real-time chunks
                while True:
                    chunk = await process.stdout.read(self.chunk_read_size)
                    if not chunk:
                        break

                    data_chunks += 1
                    total_bytes += len(chunk)

                    chunk_text = chunk.decode("utf-8", errors="ignore")
                    await self.output_writer.write_debug_info(
                        f"Chunk #{data_chunks} ({len(chunk)} bytes): {chunk_text[:100]}{'...' if len(chunk_text) > 100 else ''}"
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
                                await self.output_writer.write_debug_info(f"JSON message type: {json_data.get('type', 'unknown')}")

                                # Extract content from JSON message
                                if json_data.get("type") == "assistant" and json_data.get("message", {}).get("content"):
                                    for content_item in json_data["message"]["content"]:
                                        if content_item.get("type") == "text" and content_item.get("text"):
                                            text_content = content_item["text"]
                                            # Write clean assistant response to database
                                            await self.output_writer.write_assistant_response(text_content)
                                            collected_output.append(text_content)
                                        elif content_item.get("type") == "tool_use":
                                            tool_info = f"Using tool: {content_item.get('name', 'unknown')}"
                                            await self.output_writer.write_system_status(tool_info)
                                            collected_output.append(tool_info + "\n")

                            except json.JSONDecodeError:
                                # If not JSON, treat as plain text output
                                await self.output_writer.write_debug_info(f"Plain text: {line[:50]}{'...' if len(line) > 50 else ''}")
                                await self.output_writer.write_assistant_response(line + "\n")
                                collected_output.append(line + "\n")

                # Handle any remaining buffer content
                if buffer.strip():
                    await self.output_writer.write_debug_info(f"Final buffer: {buffer[:50]}{'...' if len(buffer) > 50 else ''}")
                    await self.output_writer.write_assistant_response(buffer)
                    collected_output.append(buffer)

                # Wait for process to complete
                await process.wait()

                # Change back to original directory
                os.chdir(original_dir)

                # Handle stderr if there were errors
                if process.returncode != 0:
                    stderr_output = await process.stderr.read()
                    error_msg = stderr_output.decode() if stderr_output else "Unknown error"
                    
                    error_message = f"❌ Claude CLI failed (exit code: {process.returncode}): {error_msg}"
                    await self.write_error(error_message)

                    # Still return collected output if we got some
                    if collected_output:
                        await self.output_writer.write_system_status(f"Returning partial output despite error. Collected {len(collected_output)} chunks")
                        return "".join(collected_output)
                    
                    raise ProviderError(f"Claude CLI failed with exit code {process.returncode}: {error_msg}")

                # Success case
                response = "".join(collected_output)
                await self.output_writer.write_system_status(
                    f"Claude CLI completed successfully. Chunks: {data_chunks}, Bytes: {total_bytes}, Response: {len(response)} chars"
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

            error_msg = f"❌ Claude CLI execution failed: {e}"
            await self.write_error(error_msg)
            raise ProviderError(f"Failed to generate Claude CLI response: {e}") from e