from datetime import datetime

import httpx
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()
security = HTTPBearer()


class AuthError(HTTPException):
    """Custom authentication error."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_github_token(token: str) -> dict | None:
    """Verify GitHub token and return user info."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}"},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None


async def get_user_from_github_token(token: str, db: AsyncSession) -> User | None:
    """Get user from GitHub token."""
    github_user = await verify_github_token(token)
    if not github_user:
        return None
    
    github_id = github_user.get("id")
    github_username = github_user.get("login")
    
    if not github_id or not github_username:
        return None
    
    # Find existing user by GitHub ID
    result = await db.execute(
        select(User).where(User.github_id == str(github_id))
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update GitHub username if it changed
        if user.github_username != github_username:
            user.github_username = github_username
            await db.commit()
        return user if user.is_active else None
    
    # Create new user for GitHub OAuth
    import secrets
    new_user = User(
        id=f"user_github_{secrets.token_urlsafe(12)}",
        email=github_user.get("email") or f"{github_username}@github.local",
        name=github_user.get("name") or github_username,
        github_id=str(github_id),
        github_username=github_username,
        is_active=True,
        is_superuser=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


# API key authentication removed - using GitHub OAuth only


async def authenticate_user(
    credentials: HTTPAuthorizationCredentials, db: AsyncSession
) -> User:
    """Authenticate user from GitHub token only."""
    token = credentials.credentials

    # Try GitHub token
    user = await get_user_from_github_token(token, db)
    if user:
        return user

    raise AuthError("Invalid credentials")


# Password hashing removed - using GitHub OAuth only