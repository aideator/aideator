from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthError, authenticate_user
from app.core.config import get_settings
from app.core.database import get_session, async_session_maker
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token or API key."""
    settings = get_settings()
    
    # In development modes, bypass authentication completely
    if settings.simple_dev_mode or not settings.require_api_keys_for_agents:
        from app.middleware.development import get_dev_user_from_request
        
        # Try to get dev user from request state first
        dev_user = await get_dev_user_from_request(request)
        if dev_user:
            return dev_user
        
        # If no dev user in request state, create one directly
        from app.middleware.development import DevelopmentAuthMiddleware
        middleware = DevelopmentAuthMiddleware(app=None)
        async with async_session_maker() as dev_db:
            test_user = await middleware._get_or_create_test_user(dev_db)
            return test_user
    
    # Production mode - require credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
    request: Request,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    api_key: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get current user from API key header or query parameter."""
    settings = get_settings()
    
    # In development modes, bypass authentication completely
    if settings.simple_dev_mode or not settings.require_api_keys_for_agents:
        from app.middleware.development import get_dev_user_from_request
        
        # Try to get dev user from request state first
        dev_user = await get_dev_user_from_request(request)
        if dev_user:
            return dev_user
        
        # If no dev user in request state, create one directly
        # This handles cases where middleware hasn't run or dependency injection order issues
        from app.middleware.development import DevelopmentAuthMiddleware
        middleware = DevelopmentAuthMiddleware(app=None)  # app not needed for user creation
        async with async_session_maker() as dev_db:
            test_user = await middleware._get_or_create_test_user(dev_db)
            return test_user
    
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
