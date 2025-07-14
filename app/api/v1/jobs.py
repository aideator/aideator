"""
Job-related API endpoints for secure key retrieval.
"""

# Secure API key retrieval system for agent jobs
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.logging import get_logger
from app.models.user import User
from app.services.provider_key_service import ProviderKeyService

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


class JobKeyResponse(BaseModel):
    """Response for job key retrieval."""

    success: bool = True
    keys: dict[str, str]
    expires_at: str


class JobKeyRequest(BaseModel):
    """Request for job key retrieval."""

    job_token: str


@router.post("/keys", response_model=JobKeyResponse)
async def get_job_keys(
    request: JobKeyRequest,
    db: AsyncSession = Depends(get_session),
) -> JobKeyResponse:
    """
    Retrieve API keys for a specific job using a JWT token.

    This endpoint validates the job token and returns the user's API keys
    needed for the agent to communicate with LLM providers.

    Args:
        job_token: JWT token containing run_id, user_id, and expiration

    Returns:
        Dictionary of provider API keys and token expiration time

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    try:
        # Decode and validate JWT token
        payload = jwt.decode(
            request.job_token, settings.secret_key, algorithms=["HS256"]
        )

        # Extract token data
        user_id = payload.get("user_id")
        run_id = payload.get("run_id")
        variation_id = payload.get("variation_id")

        if not user_id or not run_id or not variation_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required fields",
            )

        logger.info(
            f"🔑 Job key request for run {run_id}, variation {variation_id}, user {user_id}"
        )

        # Get user from database
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Get user's API keys
        provider_service = ProviderKeyService(db)
        user_keys = await provider_service.get_user_provider_keys(user_id)

        # Decrypt and organize keys by provider
        decrypted_keys = {}
        for key in user_keys:
            if key.is_active:
                try:
                    decrypted_key = await provider_service.decrypt_api_key(
                        db, user, key.id
                    )
                    provider_name = key.provider.upper()
                    decrypted_keys[f"{provider_name}_API_KEY"] = decrypted_key
                    logger.info(
                        f"✅ Retrieved {provider_name} API key for job {run_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"❌ Failed to decrypt {key.provider} key for user {user_id}: {e}"
                    )

        # Add model-specific keys if configured
        model_name = payload.get("model_name")
        if model_name:
            model_key = await provider_service.get_key_for_model(db, user, model_name)
            if model_key and model_key.is_active:
                try:
                    decrypted_key = await provider_service.decrypt_api_key(
                        db, user, model_key.id
                    )
                    provider_name = model_key.provider.upper()
                    decrypted_keys[f"{provider_name}_API_KEY"] = decrypted_key
                    logger.info(
                        f"✅ Retrieved model-specific {provider_name} key for {model_name}"
                    )
                except Exception as e:
                    logger.warning(f"❌ Failed to decrypt model-specific key: {e}")

        expires_at = datetime.fromtimestamp(payload.get("exp", 0), tz=UTC).isoformat()

        logger.info(
            f"🎯 Successfully retrieved {len(decrypted_keys)} API keys for job {run_id}"
        )

        return JobKeyResponse(keys=decrypted_keys, expires_at=expires_at)

    except jwt.ExpiredSignatureError:
        logger.warning("❌ Expired job token used")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"❌ Invalid job token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"❌ Error retrieving job keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys",
        )


def generate_job_token(
    user_id: str,
    run_id: str,
    variation_id: int,
    model_name: str | None = None,
    expires_minutes: int = 60,
) -> str:
    """
    Generate a JWT token for job authentication.

    Args:
        user_id: User ID owning the API keys
        run_id: Run ID for the job
        variation_id: Variation ID for the job
        model_name: Optional model name for model-specific keys
        expires_minutes: Token expiration time in minutes

    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_id,
        "run_id": run_id,
        "variation_id": str(variation_id),
        "model_name": model_name,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "iat": datetime.utcnow(),
        "type": "job_token",
    }

    return jwt.encode(payload, settings.secret_key, algorithm="HS256")
