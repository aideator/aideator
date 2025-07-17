"""
Development user utilities for simplified local development.

This module provides a single source of truth for creating and managing
development users across all scripts and development tools.
"""

import secrets
from datetime import datetime

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_dev_user(db: AsyncSession) -> User:
    """
    Get or create the standard development user.
    
    This function provides a consistent way to create development users
    across all scripts and development tools. The user is created with
    superuser privileges for full access during development.
    
    Args:
        db: Database session
        
    Returns:
        User: The development user object
    """
    # Look for existing development user
    result = await db.execute(select(User).where(User.email == "test@aideator.local"))
    user = result.scalar_one_or_none()
    
    if user:
        return user
    
    # Create new development user
    user = User(
        id=f"user_test_{secrets.token_urlsafe(12)}",
        email="test@aideator.local",
        name="Test User",
        company="AIdeator Development",
        is_active=True,
        is_superuser=True,  # Full access for development
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def ensure_dev_user_exists(db: AsyncSession) -> str:
    """
    Ensure development user exists and return user ID.
    
    This is a convenience function for scripts that just need the user ID.
    
    Args:
        db: Database session
        
    Returns:
        str: User ID of the development user
    """
    user = await get_or_create_dev_user(db)
    return user.id