from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthError, authenticate_user
from app.core.config import get_settings
from app.core.database import async_session_maker, get_session
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Get current user - authenticated GitHub user or general dev user."""
    
    # If credentials provided, try to authenticate with GitHub
    if credentials:
        try:
            return await authenticate_user(credentials, db)
        except AuthError:
            # If GitHub auth fails, fall back to dev user
            pass
    
    # No credentials or GitHub auth failed - use dev user
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


# API key authentication removed - using GitHub OAuth only


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




# Services
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.kubernetes_service import KubernetesService

# Initialize services
kubernetes_service = KubernetesService()
agent_orchestrator = AgentOrchestrator(kubernetes_service)

def get_orchestrator() -> AgentOrchestrator:
    """Get agent orchestrator instance."""
    return agent_orchestrator

# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]
