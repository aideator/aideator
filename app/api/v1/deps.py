"""
Common dependencies for API endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.models.user import User
from app.services.auth_service import auth_service

settings = get_settings()
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def get_current_user(api_key: str = Depends(api_key_header)) -> User:
    """Get current user from API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )

    user = await auth_service.validate_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin privileges."""
    # For now, we'll check if the user is a specific admin user
    # In production, you'd have a proper role system
    if user.email not in ["admin@aideator.com", "support@aideator.com"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return user
