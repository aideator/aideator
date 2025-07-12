"""LiteLLM provider implementation."""

from typing import AsyncGenerator, Dict, Any
from litellm import acompletion
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import LLMProvider


class LiteLLMProvider(LLMProvider):
    """LiteLLM-based provider for OpenAI and other models."""
    
    def __init__(self):
        self.name = "litellm"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using LiteLLM."""
        model = config.get("model", "gpt-4o-mini")
        
        # Prepare the full prompt
        full_prompt = f"""
You are an expert software engineer analyzing a codebase. Here's the codebase analysis:

{prompt}

Please provide a comprehensive analysis and recommendations. Focus on:
1. Understanding the codebase structure and purpose
2. Addressing the specific user request
3. Providing actionable recommendations
4. Identifying potential improvements or issues

Be thorough but concise in your response.
"""
        
        # Stream response
        async for chunk in await acompletion(
            model=f"openai/{model}",
            max_tokens=config.get("max_tokens", 4000),
            temperature=config.get("temperature", 0.7),
            messages=[
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            stream=True
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def get_name(self) -> str:
        """Get provider name."""
        return self.name