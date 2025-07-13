"""
Centralized error handling and user-friendly error messages.

Provides consistent error formatting across all providers and services.
"""

from typing import Optional


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class ConfigurationError(AgentError):
    """Configuration-related errors."""
    pass


class ProviderError(AgentError):
    """Provider-related errors."""
    pass


class RepositoryError(AgentError):
    """Repository analysis errors."""
    pass


class DatabaseError(AgentError):
    """Database connection errors."""
    pass


def format_api_error(error: Exception, provider: str) -> str:
    """Format API errors with user-friendly messages."""
    error_str = str(error).lower()
    
    if "authentication" in error_str or "api key" in error_str or "unauthorized" in error_str:
        return f"""
🔑 **Authentication Error**

The {provider.title()} API rejected the request due to authentication issues.

**Possible causes:**
- API key is invalid or expired
- API key lacks necessary permissions
- Model requires a different tier of access

**Next steps:**
1. Verify your {provider.title()} API key is valid
2. Check if your API key has access to the requested model
3. Try using a different model from the same provider

Original error: {error}
"""
    
    if "rate limit" in error_str or "quota" in error_str:
        return f"""
⏱️ **Rate Limit Exceeded**

The {provider.title()} API rate limit has been exceeded.

**What this means:**
- Too many requests have been made to the API
- Your account may have reached its usage quota

**Next steps:**
1. Wait a few minutes and try again
2. Check your {provider.title()} account usage limits
3. Consider upgrading your API plan if needed

Original error: {error}
"""
    
    if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
        return f"""
🤖 **Model Not Available**

The requested model is not available or does not exist.

**Possible causes:**
- Model name is misspelled
- Model is not available in your region
- Model requires special access

**Next steps:**
1. Check the model name spelling
2. Try a different model like 'gpt-4o-mini' or 'claude-3-haiku'
3. Verify the model is available through your API provider

Original error: {error}
"""
    
    # Generic error
    return f"""
⚠️ **API Request Failed**

An error occurred while calling the model API.

**Error details:**
{error}

**Next steps:**
1. Check if the API service is available
2. Verify your internet connection
3. Try again in a few moments

If the problem persists, contact support with the error details above.
"""


def format_repository_error(error: Exception, repo_url: str) -> str:
    """Format repository cloning/analysis errors."""
    return f"""
📁 **Repository Error**

Failed to process repository: {repo_url}

**Error details:**
{error}

**Possible causes:**
- Repository is private or doesn't exist
- Network connectivity issues
- Invalid repository URL format

**Next steps:**
1. Verify the repository URL is correct
2. Check if the repository is publicly accessible
3. Ensure network connectivity

Original error: {error}
"""


def format_database_error(error: Exception) -> str:
    """Format database connection errors."""
    return f"""
🗄️ **Database Connection Error**

Failed to connect to the database.

**Error details:**
{error}

**Possible causes:**
- Database service is unavailable
- Connection string is incorrect
- Network connectivity issues

**Next steps:**
1. Check if the database service is running
2. Verify DATABASE_URL environment variable
3. Check network connectivity to database

Original error: {error}
"""


def format_configuration_error(missing_config: str, description: Optional[str] = None) -> str:
    """Format configuration errors."""
    msg = f"""
⚙️ **Configuration Error**

Missing required configuration: {missing_config}

"""
    
    if description:
        msg += f"**Details:**\n{description}\n\n"
    
    msg += f"""**Next steps:**
1. Set the required environment variable: {missing_config}
2. Restart the agent with proper configuration
3. Check the deployment documentation for required variables
"""
    
    return msg