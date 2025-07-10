from datetime import datetime

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import APIKey, User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthError(HTTPException):
    """Custom authentication error."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_from_token(token: str, db: AsyncSession) -> User | None:
    """Get user from JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            # Token missing user ID - authentication failed
            return None

        user = await db.get(User, user_id)
        # Return user only if exists and is active
        return user if user and user.is_active else None

    except JWTError:
        # JWT validation failed
        return None


async def get_user_from_api_key(api_key: str, db: AsyncSession) -> User | None:
    """Get user from API key."""
    if not api_key.startswith("aid_sk_"):
        return None

    # Hash the provided key to match stored hash
    key_hash = pwd_context.hash(api_key)

    # Find the API key by trying to verify against stored hashes
    result = await db.execute(
        select(APIKey).where(APIKey.is_active == True)
    )
    api_keys = result.scalars().all()

    for stored_key in api_keys:
        if pwd_context.verify(api_key, stored_key.key_hash):
            # Found matching key, check if it's expired
            if stored_key.expires_at and stored_key.expires_at < datetime.utcnow():
                continue

            # Update usage stats
            stored_key.total_requests += 1
            stored_key.last_used_at = datetime.utcnow()
            await db.commit()

            # Get the user
            user = await db.get(User, stored_key.user_id)
            return user if user and user.is_active else None

    return None


async def authenticate_user(credentials: HTTPAuthorizationCredentials, db: AsyncSession) -> User:
    """Authenticate user from JWT token or API key."""
    token = credentials.credentials

    # Try JWT token first
    user = await get_user_from_token(token, db)
    if user:
        return user

    # Try API key
    user = await get_user_from_api_key(token, db)
    if user:
        return user

    raise AuthError("Invalid credentials")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)
