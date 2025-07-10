"""
Authentication service for validating API keys and managing user sessions.
"""


from sqlalchemy import select

from app.core.auth import get_user_from_api_key
from app.core.database import async_session_maker
from app.models.user import User


class AuthService:
    """Service for authentication operations."""

    async def validate_api_key(self, api_key: str) -> User | None:
        """Validate API key and return associated user."""
        async with async_session_maker() as session:
            return await get_user_from_api_key(api_key, session)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        async with async_session_maker() as session:
            return await session.get(User, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()


# Global instance
auth_service = AuthService()
