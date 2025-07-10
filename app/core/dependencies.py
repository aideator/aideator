from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthError, authenticate_user
from app.core.database import get_session
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token or API key."""
    return await authenticate_user(credentials, db)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_user_from_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    api_key: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get current user from API key header or query parameter."""
    from app.core.auth import get_user_from_api_key

    # Try header first, then query parameter
    key = x_api_key or api_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "API-Key"},
        )

    user = await get_user_from_api_key(key, db)
    if not user:
        raise AuthError("Invalid API key")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User | None:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None

    try:
        return await authenticate_user(credentials, db)
    except AuthError:
        return None


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentUserAPIKey = Annotated[User, Depends(get_current_user_from_api_key)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]
