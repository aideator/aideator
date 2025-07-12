import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.auth import (
    get_password_hash,
    verify_password,
)
from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.models.user import APIKey, User
from app.schemas.auth import (
    APIKeyResponse,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def generate_api_key() -> str:
    """Generate a secure API key."""
    prefix = "aid_sk_"
    key = secrets.token_urlsafe(32)
    return f"{prefix}{key}"


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Register a new user."""
    # Check if user already exists
    query = select(User).where(col(User.email) == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    # Create new user
    user = User(
        id=str(uuid4()),
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        created_at=datetime.utcnow(),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate user and return access token."""
    # Create a temporary HTTPAuthorizationCredentials object with the email as the token
    # This is a temporary fix - we should create a proper authenticate_user function
    # that takes email and password directly

    # For now, let's authenticate manually
    query = select(User).where(col(User.email) == user_credentials.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        user = None

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Create access token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Update current user information."""
    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.email is not None:
        # Check if email is already taken
        query = select(User).where(
            and_(
                col(User.email) == user_update.email,
                col(User.id) != current_user.id,
            )
        )
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already taken")

        current_user.email = user_update.email

    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)

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


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Change user password."""
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, str]:
    """Logout user (invalidate token)."""
    # In a real implementation, you would add the token to a blacklist
    # For now, we just return success
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
            "full_name": current_user.full_name,
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


@router.post(
    "/api-keys",
    response_model=CreateAPIKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> CreateAPIKeyResponse:
    """Create a new API key."""
    # Generate key
    api_key = generate_api_key()
    key_hash = get_password_hash(api_key)

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    # Create API key record
    key_record = APIKey(
        id=f"key_{secrets.token_urlsafe(12)}",
        user_id=current_user.id,
        key_hash=key_hash,
        name=request.name,
        scopes=request.scopes,
        expires_at=expires_at,
    )

    db.add(key_record)
    await db.commit()
    await db.refresh(key_record)

    logger.info("api_key_created", user_id=current_user.id, key_id=key_record.id)

    return CreateAPIKeyResponse(
        api_key=api_key,
        key_info=APIKeyResponse.model_validate(key_record),
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[APIKey]:
    """List user's API keys."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(desc(APIKey.created_at))
    )
    return list(result.scalars().all())


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    """Delete an API key."""
    result = await db.execute(
        select(APIKey).where(
            (APIKey.id == key_id) & (APIKey.user_id == current_user.id)
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    await db.delete(key)
    await db.commit()

    logger.info("api_key_deleted", user_id=current_user.id, key_id=key_id)


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

    # Find or create test user
    result = await db.execute(select(User).where(User.email == "test@aideator.local"))
    user = result.scalar_one_or_none()

    if not user:
        # Create test user
        user = User(
            id=f"user_test_{secrets.token_urlsafe(12)}",
            email="test@aideator.local",
            hashed_password=get_password_hash("testpass123"),
            full_name="Test User",
            company="AIdeator Development",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Create access token
    access_token_expires = timedelta(days=30)  # Long-lived for development
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    # Always create a fresh API key for development
    api_key = f"aid_sk_test_{secrets.token_urlsafe(32)}"
    key_hash = get_password_hash(api_key)

    # Remove old development key if exists
    await db.execute(
        select(APIKey).where(
            (APIKey.user_id == user.id) & (APIKey.name == "Development Test Key")
        )
    )
    old_keys = await db.execute(
        select(APIKey).where(
            (APIKey.user_id == user.id) & (APIKey.name == "Development Test Key")
        )
    )
    for old_key in old_keys.scalars().all():
        await db.delete(old_key)

    # Create new API key
    api_key_record = APIKey(
        id=f"key_test_{secrets.token_urlsafe(12)}",
        user_id=user.id,
        key_hash=key_hash,
        name="Development Test Key",
        scopes=["runs:create", "runs:read"],
    )

    db.add(api_key_record)
    await db.commit()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "company": user.company,
        },
        "access_token": access_token,
        "token_type": "bearer",
        "api_key": api_key,  # Always returns fresh API key in development
        "message": "Development test user login successful",
    }
