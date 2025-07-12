"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Generate response from LLM.
        
        Args:
            prompt: The input prompt
            config: Provider-specific configuration
            
        Yields:
            Text chunks as they are generated
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name for logging."""
        pass