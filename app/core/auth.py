from datetime import datetime
from typing import cast

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import APIKey, User

settings = get_settings()
logger = get_logger(__name__)
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
        logger.info(f"🔍 Validating JWT token: {token[:20]}...")
        
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        logger.info(f"✅ JWT payload decoded: {payload}")
        
        # Try to get user_id first (if present in payload)
        user_id: str | None = payload.get("user_id")
        if user_id:
            logger.info(f"🔍 Looking up user by user_id: {user_id}")
            user = await db.get(User, user_id)
            if user and user.is_active:
                logger.info(f"✅ Found user by user_id: {user.email}")
                return user
            else:
                logger.warning(f"❌ User not found or inactive by user_id: {user_id}")
        
        # Fallback to using 'sub' field (which might be email or user_id)
        sub: str | None = payload.get("sub")
        if sub is None:
            logger.warning("❌ No 'sub' field in JWT payload")
            return None
            
        logger.info(f"🔍 Looking up user by sub field: {sub}")
        
        # Try as user ID first
        user = await db.get(User, sub)
        if user and user.is_active:
            logger.info(f"✅ Found user by sub as ID: {user.email}")
            return user
            
        # If not found by ID, try as email
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == sub))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            logger.info(f"✅ Found user by sub as email: {user.email}")
            return user
        
        logger.warning(f"❌ User not found by sub: {sub}")
        return None

    except JWTError as e:
        logger.error(f"❌ JWT validation failed: {e}")
        return None


async def get_user_from_api_key(api_key: str, db: AsyncSession) -> User | None:
    """Get user from API key."""
    logger.info(f"�� Validating API key: {api_key[:10]}...")
    
    if not api_key.startswith("aid_sk_"):
        logger.warning("❌ API key doesn't start with 'aid_sk_'")
        return None

    # Hash the provided key to match stored hash
    pwd_context.hash(api_key)

    # Find the API key by trying to verify against stored hashes
    result = await db.execute(select(APIKey).where(APIKey.is_active == True))  # type: ignore[arg-type] # noqa: E712
    api_keys = result.scalars().all()
    
    logger.info(f"🔍 Found {len(api_keys)} active API keys in database")

    for stored_key in api_keys:
        if pwd_context.verify(api_key, stored_key.key_hash):
            logger.info(f"✅ API key verified for user: {stored_key.user_id}")
            # Found matching key, check if it's expired
            if stored_key.expires_at and stored_key.expires_at < datetime.utcnow():
                logger.warning("❌ API key is expired")
                continue

            # Update usage stats
            stored_key.total_requests += 1
            stored_key.last_used_at = datetime.utcnow()
            await db.commit()

            # Get the user
            user = await db.get(User, stored_key.user_id)
            if user and user.is_active:
                logger.info(f"✅ Found active user: {user.email}")
                return user
            else:
                logger.warning(f"❌ User not found or inactive: {stored_key.user_id}")

    logger.warning("❌ No matching API key found")
    return None


async def authenticate_user(
    credentials: HTTPAuthorizationCredentials, db: AsyncSession
) -> User:
    """Authenticate user from JWT token or API key."""
    token = credentials.credentials
    logger.info(f"🔍 Authenticating with token: {token[:20]}...")

    # Try JWT token first
    logger.info("🔍 Trying JWT token authentication...")
    user = await get_user_from_token(token, db)
    if user:
        logger.info(f"✅ JWT authentication successful: {user.email}")
        return user

    # Try API key
    logger.info("🔍 Trying API key authentication...")
    user = await get_user_from_api_key(token, db)
    if user:
        logger.info(f"✅ API key authentication successful: {user.email}")
        return user

    logger.warning("❌ Both JWT and API key authentication failed")
    raise AuthError("Invalid credentials")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return cast("bool", pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """Hash password."""
    return cast("str", pwd_context.hash(password))
