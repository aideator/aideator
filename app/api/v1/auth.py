import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.auth import (
    get_user_from_github_token,
    verify_github_token,
)
from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.auth import (
    UserResponse,
)
from app.utils.dev_user import get_or_create_dev_user

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer()


# API key generation removed - using GitHub OAuth only


# =============================================================================
# GitHub OAuth Routes
# =============================================================================

@router.get("/github/login")
async def github_login(request: Request) -> RedirectResponse:
    """Redirect to GitHub for OAuth login."""
    # Build GitHub OAuth URL
    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=user:email"
        f"&state=github_oauth"
    )
    
    return RedirectResponse(url=github_oauth_url, status_code=302)


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str | None = None,
    request: Request = None,
    db: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Handle GitHub OAuth callback and redirect to frontend."""
    try:
        # Exchange code for access token
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Get access token from GitHub
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            
            if token_response.status_code != 200:
                return RedirectResponse(url="http://localhost:3000/?error=token_exchange_failed", status_code=302)
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return RedirectResponse(url="http://localhost:3000/?error=no_access_token", status_code=302)
        
        # Get or create user from GitHub token
        user = await get_user_from_github_token(access_token, db)
        if not user:
            return RedirectResponse(url="http://localhost:3000/?error=user_creation_failed", status_code=302)
        
        # Store user data in session or use a simpler approach
        # Let's try a simpler redirect with just essential data
        redirect_url = (
            f"http://localhost:3000/auth/callback"
            f"?token={access_token}"
            f"&user_id={user.id}"
            f"&email={urllib.parse.quote(user.email)}"
            f"&name={urllib.parse.quote(user.name or '')}"
            f"&github_username={user.github_username or ''}"
        )
        
        logger.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url="http://localhost:3000/?error=oauth_callback_failed", status_code=302)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    name: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Update current user information."""
    # Update user fields (simplified for GitHub OAuth)
    if name is not None:
        current_user.name = name

    current_user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[UserResponse]:
    """List all users (admin only)."""
    # Simple admin check - in production, you'd have proper role management
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(User).order_by(desc(col(User.created_at)))
    result = await db.execute(query)
    users = result.scalars().all()

    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Get user by ID (admin only)."""
    # Simple admin check - in production, you'd have proper role management
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(User).where(col(User.id) == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete user (admin only)."""
    # Simple admin check - in production, you'd have proper role management
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = select(User).where(col(User.id) == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, str]:
    """Logout user (GitHub OAuth tokens are handled client-side)."""
    # GitHub OAuth tokens are handled client-side
    # No server-side token invalidation needed
    return {"message": "Logged out successfully"}


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get detailed user profile."""
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "github_username": current_user.github_username,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
            "created_at": current_user.created_at,
            "updated_at": current_user.updated_at,
        },
        "preferences": {
            "timezone": "UTC",  # Default for now
            "language": "en",  # Default for now
        },
        "statistics": {
            "total_sessions": 0,  # Would come from database
            "total_requests": 0,  # Would come from database
            "total_cost": 0.0,  # Would come from database
        },
    }


# API key management endpoints removed - using GitHub OAuth only


@router.get("/dev/test-login", include_in_schema=False)
async def dev_test_login(
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """
    Development endpoint for automatic test user login.
    WARNING: This endpoint is only available in development mode.
    """
    # Only allow in development mode
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    # Find or create test user using standardized utility
    user = await get_or_create_dev_user(db)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "company": user.company,
        },
        "access_token": "fake_github_token_for_dev",
        "token_type": "github",
        "message": "Development test user login successful",
    }