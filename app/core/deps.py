from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.logging import get_logger
from app.models.user import APIKey, User
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.kubernetes_service import KubernetesService

settings = get_settings()
logger = get_logger(__name__)

# Security
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Initialize services
kubernetes_service = KubernetesService()
agent_orchestrator = AgentOrchestrator(kubernetes_service)

def get_orchestrator() -> AgentOrchestrator:
    """Get agent orchestrator instance."""
    return agent_orchestrator


async def get_current_user_from_api_key(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """Get current user from API key if provided."""
    # Check for API key in header
    api_key = request.headers.get(settings.api_key_header)
    if not api_key:
        return None
    
    # Validate API key format
    if not api_key.startswith("aid_sk_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )
    
    # Find API key in database
    result = await db.execute(
        select(APIKey).where(APIKey.is_active == True)
    )
    api_keys = result.scalars().all()
    
    # Check each key (we can't query by hash)
    valid_key = None
    for key in api_keys:
        if pwd_context.verify(api_key, key.key_hash):
            valid_key = key
            break
    
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Check expiration
    if valid_key.expires_at and valid_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired",
        )
    
    # Update last used
    valid_key.last_used_at = datetime.utcnow()
    valid_key.total_requests += 1
    await db.commit()
    
    # Get user
    user = await db.get(User, valid_key.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user


async def require_user(
    current_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    """Require authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_superuser(
    current_user: User = Depends(require_user),
) -> User:
    """Require superuser privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return current_user


# Import datetime at the top of the file
from datetime import datetime