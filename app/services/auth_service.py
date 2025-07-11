"""
Authentication service for validating API keys and managing user sessions.
"""

from app.core.auth import get_user_from_api_key
from app.core.database import async_session_maker
from app.models.user import User


class AuthService:
    """Service for authentication operations."""

    async def validate_api_key(self, api_key: str) -> User | None:
        """Validate API key and return associated user."""
        async with async_session_maker() as session:
            return await get_user_from_api_key(api_key, session)


# Global instance
auth_service = AuthService()
