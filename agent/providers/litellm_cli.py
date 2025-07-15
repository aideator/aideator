"""
LiteLLM CLI provider implementation.

Handles LiteLLM CLI execution with subprocess pattern for consistency with other providers.
"""

import asyncio
import json
import os
from typing import Optional

from agent.providers.base import BaseProvider
from agent.utils.errors import ProviderError


class LiteLLMCLIProvider(BaseProvider):
    """LiteLLM CLI provider using subprocess pattern."""
    
    def __init__(self, config, output_writer):
        """Initialize LiteLLM CLI provider."""
        super().__init__(config, output_writer)
        self.chunk_read_size = 1024
        self.timeout_seconds = 300.0  # 5 minutes for LLM calls
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "litellm-cli"
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using LiteLLM CLI with streaming.
        
        Args:
            prompt: User prompt
            context: Optional codebase analysis context
            
        Returns:
            Generated response text
        """
        await self.write_job_data(f"🤖 Starting LiteLLM CLI generation with model: {self.config.model}")
        
        try:
            # Prepare the full prompt based on context
            if context is not None:
                # Code mode: Include codebase analysis
                full_prompt = f"""
You are an expert software engineer analyzing a codebase. Here's the codebase analysis:

{context}

User Request: {prompt}

Please provide a comprehensive analysis and recommendations. Focus on:
1. Understanding the codebase structure and purpose
2. Addressing the specific user request
3. Providing actionable recommendations
4. Identifying potential improvements or issues

Be thorough but concise in your response.
"""
            else:
                # Chat mode: Direct prompt without codebase context
                full_prompt = prompt

            # Build LiteLLM wrapper script command
            wrapper_script = os.path.join(os.path.dirname(__file__), "..", "scripts", "litellm_wrapper.py")
            args = [
                "python", wrapper_script,
                self.config.model,
                full_prompt,
                str(self.config.temperature),
                str(self.config.max_tokens),
                self.config.gateway_url,
                self.config.gateway_key
            ]

            await self.write_job_data(f"🔧 Executing: python litellm_wrapper.py --model {self.config.model}")

            process = await asyncio.create_subprocess_exec(
                args[0],
                *args[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=os.environ,
            )

            # Close stdin immediately since we're using --prompt flag
            process.stdin.close()

            # Stream processing variables
            collected_output = []
            buffer = ""
            data_chunks = 0
            total_bytes = 0

            await self.write_job_data(f"🚀 LiteLLM CLI process started (PID: {process.pid})")

            try:
                # Read stdout in real-time chunks with timeout
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            process.stdout.read(self.chunk_read_size),
                            timeout=self.timeout_seconds
                        )
                        if not chunk:
                            break
                    except asyncio.TimeoutError:
                        process.terminate()
                        await process.wait()
                        error_msg = f"❌ LiteLLM CLI timed out after {self.timeout_seconds} seconds"
                        await self.write_error(error_msg)
                        raise ProviderError(f"LiteLLM CLI execution timed out after {self.timeout_seconds} seconds")

                    data_chunks += 1
                    total_bytes += len(chunk)

                    chunk_text = chunk.decode("utf-8", errors="ignore")
                    await self.write_job_data(
                        f"📡 Chunk #{data_chunks} ({len(chunk)} bytes): {chunk_text[:100]}{'...' if len(chunk_text) > 100 else ''}"
                    )

                    # Process the chunk immediately (streaming approach)
                    buffer += chunk_text
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # Keep incomplete line in buffer

                    for line in lines:
                        if line.strip():
                            try:
                                # Try to parse as JSON first (wrapper script format)
                                json_data = json.loads(line)
                                await self.write_job_data(f"📋 JSON message type: {json_data.get('type', 'unknown')}")

                                # Extract content from JSON message (similar to Claude CLI format)
                                if json_data.get("type") == "assistant" and json_data.get("message", {}).get("content"):
                                    for content_item in json_data["message"]["content"]:
                                        if content_item.get("type") == "text" and content_item.get("text"):
                                            text_content = content_item["text"]
                                            # Output immediately for streaming
                                            print(text_content, end="", flush=True)
                                            await self.write_job_data(text_content)
                                            collected_output.append(text_content)
                                elif json_data.get("type") == "error":
                                    error_msg = json_data.get("error", "Unknown error")
                                    await self.write_error(f"❌ LiteLLM wrapper error: {error_msg}")
                                    raise ProviderError(f"LiteLLM wrapper error: {error_msg}")

                            except json.JSONDecodeError:
                                # If not JSON, treat as plain text output
                                await self.write_job_data(f"📝 Plain text: {line[:50]}{'...' if len(line) > 50 else ''}")
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
                    
                    full_error = f"❌ LiteLLM CLI failed (exit code: {process.returncode}): {error_msg}"
                    await self.write_error(full_error)

                    # Still return collected output if we got some
                    if collected_output:
                        await self.write_job_data(f"⚠️ Returning partial output despite error. Collected {len(collected_output)} chunks")
                        return "".join(collected_output)
                    
                    raise ProviderError(f"LiteLLM CLI failed with exit code {process.returncode}: {error_msg}")

                # Success case
                response = "".join(collected_output)
                await self.write_job_data(
                    f"✅ LiteLLM CLI completed successfully. Chunks: {data_chunks}, Bytes: {total_bytes}, Response: {len(response)} chars"
                )

                return response if response else "No output received from LiteLLM CLI"

            except Exception as stream_error:
                # Clean up process if still running
                if process.returncode is None:
                    process.terminate()
                    await process.wait()
                raise stream_error

        except Exception as e:
            error_msg = f"❌ LiteLLM CLI execution failed: {e}"
            await self.write_error(error_msg)
            raise ProviderError(f"Failed to generate LiteLLM CLI response: {e}") from e