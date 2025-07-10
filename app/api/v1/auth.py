import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_password_hash, verify_password
from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import CurrentUser
from app.core.logging import get_logger
from app.models.user import APIKey, User
from app.schemas.auth import (
    APIKeyResponse,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    from jose import jwt

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def generate_api_key() -> str:
    """Generate a secure API key."""
    prefix = "aid_sk_"
    key = secrets.token_urlsafe(32)
    return f"{prefix}{key}"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Register a new user."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        id=f"user_{secrets.token_urlsafe(12)}",
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        company=user_data.company,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_registered", user_id=user.id, email=user.email)

    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_session),
) -> Token:
    """Login and receive access token."""
    # Find user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Create token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    logger.info("user_login", user_id=user.id)

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    """Get current user information."""
    return current_user


@router.post("/api-keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: CurrentUser,
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
        key_info=key_record,
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
) -> list[APIKey]:
    """List user's API keys."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return keys


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_session),
) -> None:
    """Delete an API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
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
) -> dict:
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
            is_superuser=False
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
            APIKey.user_id == user.id,
            APIKey.name == "Development Test Key"
        )
    )
    old_keys = await db.execute(
        select(APIKey).where(
            APIKey.user_id == user.id,
            APIKey.name == "Development Test Key"
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
