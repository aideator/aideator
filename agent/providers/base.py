"""
Base provider interface for LLM providers.

All providers implement this interface and output job_data type.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, config, output_writer):
        """Initialize provider with configuration and output writer.
        
        Args:
            config: AgentConfig instance
            output_writer: OutputWriter instance for database writes
        """
        self.config = config
        self.output_writer = output_writer
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response from the LLM.
        
        Args:
            prompt: The user prompt
            context: Optional codebase analysis context
            
        Returns:
            Generated response text (job_data type)
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass
    
    async def write_job_data(self, content: str) -> None:
        """Write job data output to database.
        
        Args:
            content: Output content to write as job_data type
        """
        await self.output_writer.write_output(
            content=content,
            output_type="job_data"
        )
    
    async def write_error(self, error_message: str) -> None:
        """Write error output to database.
        
        Args:
            error_message: Error message to write as error type
        """
        await self.output_writer.write_output(
            content=error_message,
            output_type="error"
        )