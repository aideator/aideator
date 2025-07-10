"""
API endpoints for provider credentials management.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.provider import ProviderCredential, ProviderType
from app.models.user import User
from app.schemas.models import (
    ProviderCredentialCreate,
    ProviderCredentialResponse,
    ProviderCredentialUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def encrypt_credentials(credentials: dict) -> dict:
    """
    Encrypt credentials before storing.
    For now, this is a placeholder - in production, use proper encryption.
    """
    # TODO: Implement proper encryption using app.core.security
    return credentials


def decrypt_credentials(encrypted_credentials: dict) -> dict:
    """
    Decrypt credentials after retrieving.
    For now, this is a placeholder - in production, use proper decryption.
    """
    # TODO: Implement proper decryption using app.core.security
    return encrypted_credentials


@router.post("/", response_model=ProviderCredentialResponse)
async def create_provider_credential(
    credential: ProviderCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Create a new provider credential.
    """
    try:
        # Check if user already has credentials for this provider
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == current_user.id,
                ProviderCredential.provider == credential.provider,
                ProviderCredential.is_active == True
            )
        )
        existing = result.first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Active credentials for {credential.provider.value} already exist"
            )

        # Validate required credential fields based on provider
        required_fields = _get_required_credential_fields(credential.provider)
        missing_fields = [field for field in required_fields if field not in credential.credentials]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields for {credential.provider.value}: {', '.join(missing_fields)}"
            )

        # Encrypt credentials
        encrypted_creds = encrypt_credentials(credential.credentials)

        # Create new credential
        new_credential = ProviderCredential(
            id=f"cred_{credential.provider.value}_{current_user.id}_{int(datetime.utcnow().timestamp())}",
            user_id=current_user.id,
            provider=credential.provider,
            name=credential.name,
            encrypted_credentials=encrypted_creds,
        )

        db.add(new_credential)
        await db.commit()
        await db.refresh(new_credential)

        return ProviderCredentialResponse(
            id=new_credential.id,
            provider=new_credential.provider,
            name=new_credential.name,
            is_active=new_credential.is_active,
            created_at=new_credential.created_at,
            updated_at=new_credential.updated_at,
            last_used_at=new_credential.last_used_at,
            total_requests=new_credential.total_requests,
            total_cost_usd=new_credential.total_cost_usd,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating provider credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to create provider credential")


@router.get("/", response_model=list[ProviderCredentialResponse])
async def get_provider_credentials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get all provider credentials for the current user.
    """
    try:
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.user_id == current_user.id
            )
        )
        credentials = result.all()

        return [
            ProviderCredentialResponse(
                id=cred.id,
                provider=cred.provider,
                name=cred.name,
                is_active=cred.is_active,
                created_at=cred.created_at,
                updated_at=cred.updated_at,
                last_used_at=cred.last_used_at,
                total_requests=cred.total_requests,
                total_cost_usd=cred.total_cost_usd,
            )
            for cred in credentials
        ]

    except Exception as e:
        logger.error(f"Error getting provider credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider credentials")


@router.get("/{credential_id}", response_model=ProviderCredentialResponse)
async def get_provider_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get a specific provider credential.
    """
    try:
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.id == credential_id,
                ProviderCredential.user_id == current_user.id
            )
        )
        credential = result.first()

        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")

        return ProviderCredentialResponse(
            id=credential.id,
            provider=credential.provider,
            name=credential.name,
            is_active=credential.is_active,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            last_used_at=credential.last_used_at,
            total_requests=credential.total_requests,
            total_cost_usd=credential.total_cost_usd,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider credential")


@router.put("/{credential_id}", response_model=ProviderCredentialResponse)
async def update_provider_credential(
    credential_id: str,
    update: ProviderCredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Update a provider credential.
    """
    try:
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.id == credential_id,
                ProviderCredential.user_id == current_user.id
            )
        )
        credential = result.first()

        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")

        # Update fields
        if update.name is not None:
            credential.name = update.name

        if update.is_active is not None:
            credential.is_active = update.is_active

        if update.credentials is not None:
            # Validate required fields
            required_fields = _get_required_credential_fields(credential.provider)
            missing_fields = [field for field in required_fields if field not in update.credentials]

            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields for {credential.provider.value}: {', '.join(missing_fields)}"
                )

            # Encrypt new credentials
            credential.encrypted_credentials = encrypt_credentials(update.credentials)

        credential.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(credential)

        return ProviderCredentialResponse(
            id=credential.id,
            provider=credential.provider,
            name=credential.name,
            is_active=credential.is_active,
            created_at=credential.created_at,
            updated_at=credential.updated_at,
            last_used_at=credential.last_used_at,
            total_requests=credential.total_requests,
            total_cost_usd=credential.total_cost_usd,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to update provider credential")


@router.delete("/{credential_id}")
async def delete_provider_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a provider credential.
    """
    try:
        result = await db.exec(
            select(ProviderCredential).where(
                ProviderCredential.id == credential_id,
                ProviderCredential.user_id == current_user.id
            )
        )
        credential = result.first()

        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")

        db.delete(credential)
        await db.commit()

        return {"message": "Credential deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting provider credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete provider credential")


def _get_required_credential_fields(provider: ProviderType) -> list[str]:
    """
    Get required credential fields for a provider.
    """
    field_map = {
        ProviderType.OPENAI: ["api_key"],
        ProviderType.ANTHROPIC: ["api_key"],
        ProviderType.GEMINI: ["api_key"],
        ProviderType.VERTEX_AI: ["project_id", "service_account_key"],
        ProviderType.MISTRAL: ["api_key"],
        ProviderType.COHERE: ["api_key"],
        ProviderType.BEDROCK: ["aws_access_key_id", "aws_secret_access_key", "region"],
        ProviderType.AZURE: ["api_key", "api_base", "api_version"],
        ProviderType.HUGGINGFACE: [],  # Some models don't require keys
        ProviderType.GROQ: ["api_key"],
        ProviderType.PERPLEXITY: ["api_key"],
        ProviderType.DEEPSEEK: ["api_key"],
        ProviderType.TOGETHER: ["api_key"],
        ProviderType.OLLAMA: [],  # Local models
        ProviderType.NVIDIA_NIM: ["api_key"],
        ProviderType.DEEPINFRA: ["api_key"],
        ProviderType.FIREWORKS: ["api_key"],
        ProviderType.XAI: ["api_key"],
        ProviderType.VOYAGE: ["api_key"],
        ProviderType.ANYSCALE: ["api_key"],
        ProviderType.OPENROUTER: ["api_key"],
        ProviderType.SAMBANOVA: ["api_key"],
        ProviderType.NEBIUS: ["api_key"],
        ProviderType.PREDIBASE: ["api_key"],
        ProviderType.VLLM: [],  # Local models
        ProviderType.GALADRIEL: ["api_key"],
        ProviderType.AI21: ["api_key"],
    }

    return field_map.get(provider, ["api_key"])  # Default to api_key
