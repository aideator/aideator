"""
LiteLLM provider implementation.

Handles LiteLLM API calls with streaming and standardized output.
"""


from litellm import acompletion
from tenacity import retry, stop_after_attempt, wait_exponential

from agent.providers.base import BaseProvider
from agent.utils.errors import ProviderError, format_api_error


class LiteLLMProvider(BaseProvider):
    """LiteLLM provider for unified LLM access."""

    def __init__(self, config, output_writer):
        """Initialize LiteLLM provider."""
        super().__init__(config, output_writer)
        self.max_retry_attempts = 3
        self.retry_min_wait = 4
        self.retry_max_wait = 10

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "litellm"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def generate_response(self, prompt: str, context: str | None = None) -> str:
        """Generate response using LiteLLM with streaming.
        
        Args:
            prompt: User prompt
            context: Optional codebase analysis context
            
        Returns:
            Generated response text
        """
        await self.write_job_data(f"🤖 Starting LiteLLM generation with model: {self.config.model}")

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

            await self.write_job_data("🔄 Calling LiteLLM API...")

            response_text = ""
            chunk_count = 0
            buffer = ""

            # Call THROUGH the LiteLLM Gateway
            try:
                response = await acompletion(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[{"role": "user", "content": full_prompt}],
                    stream=True,
                    api_base=self.config.gateway_url,
                    api_key=self.config.gateway_key,
                )
            except Exception as api_error:
                # Format user-friendly error message
                provider = self._get_model_provider(self.config.model)
                error_message = format_api_error(api_error, provider)
                await self.write_error(error_message)
                raise ProviderError(f"LiteLLM API failed: {api_error}")

            await self.write_job_data("📡 Streaming response...")

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    response_text += chunk_text
                    chunk_count += 1

                    # Add to buffer for real-time output
                    buffer += chunk_text

                    # Stream output in chunks for smooth experience
                    while len(buffer) >= 15:
                        chunk_size = 15
                        output_chunk = buffer[:chunk_size]

                        # Adjust chunk to end at word boundary if possible
                        space_pos = output_chunk.rfind(" ")
                        if space_pos > 8:
                            output_chunk = buffer[: space_pos + 1]

                        # Output the chunk to console for streaming
                        print(output_chunk, end="", flush=True)
                        await self.write_job_data(output_chunk)
                        buffer = buffer[len(output_chunk) :]

                    # Also check for newlines to maintain structure
                    if "\n" in buffer:
                        lines = buffer.split("\n")
                        for line in lines[:-1]:
                            print(line, flush=True)
                            await self.write_job_data(line + "\n")
                        buffer = lines[-1]

            # Output any remaining buffer
            if buffer.strip():
                print(buffer, end="", flush=True)
                await self.write_job_data(buffer)

            await self.write_job_data(
                f"\n\n✅ LiteLLM streaming complete. Chunks: {chunk_count}, Length: {len(response_text)} chars"
            )

            return response_text

        except Exception as e:
            error_msg = f"❌ LiteLLM generation failed: {e}"
            await self.write_error(error_msg)
            raise ProviderError(f"Failed to generate LiteLLM response: {e}") from e

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
