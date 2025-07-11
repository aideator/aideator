"""
API endpoints for credential management.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.models import (
    ProviderCredentialCreate,
    ProviderCredentialResponse,
    ProviderCredentialUpdate,
)
from app.services.provider_key_service import ProviderKeyService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=list[ProviderCredentialResponse])
async def get_credentials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[ProviderCredentialResponse]:
    """Get all credentials for the current user."""
    service = ProviderKeyService(db)
    return await service.get_user_provider_keys(current_user.id)


@router.post("/", response_model=ProviderCredentialResponse)
async def create_credential(
    credential: ProviderCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ProviderCredentialResponse:
    """Create a new credential for the current user."""
    service = ProviderKeyService(db)

    # IP address tracking disabled for now
    ip_address = None

    # Extract api_key from credentials dict
    api_key = credential.credentials.get("api_key")
    if not api_key:
        raise HTTPException(
            status_code=400, detail="api_key is required in credentials"
        )

    return await service.create_provider_key(
        user_id=current_user.id,
        provider_type=credential.provider,
        name=credential.name,
        api_key=api_key,
        model_name=credential.credentials.get("model_name"),
        ip_address=ip_address,
        metadata=credential.credentials,
    )


@router.get("/{credential_id}", response_model=ProviderCredentialResponse)
async def get_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ProviderCredentialResponse:
    """Get a specific credential by ID."""
    service = ProviderKeyService(db)

    # Get the credential
    credential = await service.get_provider_key_for_user(
        session=db, user=current_user, provider_key_id=credential_id
    )

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    return credential


@router.put("/{credential_id}", response_model=ProviderCredentialResponse)
async def update_credential(
    credential_id: str,
    credential_update: ProviderCredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> ProviderCredentialResponse:
    """Update a credential."""
    service = ProviderKeyService(db)

    # Get the existing credential
    existing_credential = await service.get_provider_key_for_user(
        session=db, user=current_user, provider_key_id=credential_id
    )

    if not existing_credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Update the credential
    api_key = None
    model_name = None
    metadata = {}

    if credential_update.credentials:
        api_key = credential_update.credentials.get("api_key")
        model_name = credential_update.credentials.get("model_name")
        metadata = credential_update.credentials

    return await service.update_provider_key(
        credential_id=credential_id,
        name=credential_update.name,
        api_key=api_key,
        model_name=model_name,
        metadata=metadata,
    )


@router.delete("/{credential_id}")
async def delete_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete a credential."""
    service = ProviderKeyService(db)

    # Get the credential
    credential = await service.get_provider_key_for_user(
        session=db, user=current_user, provider_key_id=credential_id
    )

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Delete the credential
    await service.delete_provider_key(credential_id)

    return {"message": "Credential deleted successfully"}


@router.post("/{credential_id}/test")
async def validate_credential(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Test a credential to see if it's working."""
    service = ProviderKeyService(db)

    # Get the credential
    credential = await service.get_provider_key_for_user(
        session=db, user=current_user, provider_key_id=credential_id
    )

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Test the credential
    return await service.test_provider_key(credential_id)


@router.get("/{credential_id}/usage")
async def get_credential_usage(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get usage statistics for a credential."""
    service = ProviderKeyService(db)

    # Get the credential
    credential = await service.get_provider_key_for_user(
        session=db, user=current_user, provider_key_id=credential_id
    )

    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    # Get usage statistics
    return await service.get_provider_key_usage(credential_id)


# Provider type definitions with proper values
PROVIDER_CONFIGS = {
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI API keys for GPT models",
        "example_models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "anthropic": {
        "name": "Anthropic",
        "description": "Anthropic API keys for Claude models",
        "example_models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Google API keys for Gemini models",
        "example_models": ["gemini-pro", "gemini-pro-vision"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "mistral": {
        "name": "Mistral AI",
        "description": "Mistral API keys for Mistral models",
        "example_models": ["mistral-small", "mistral-medium", "mistral-large"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "cohere": {
        "name": "Cohere",
        "description": "Cohere API keys for language models",
        "example_models": ["command", "command-light", "command-nightly"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "azure": {
        "name": "Azure OpenAI",
        "description": "Azure OpenAI API keys and endpoints",
        "example_models": ["gpt-35-turbo", "gpt-4"],
        "required_fields": ["api_key", "endpoint"],
        "optional_fields": ["model_name", "api_version"],
    },
    "bedrock": {
        "name": "AWS Bedrock",
        "description": "AWS Bedrock access keys",
        "example_models": ["anthropic.claude-v2", "amazon.titan-text-express-v1"],
        "required_fields": ["aws_access_key_id", "aws_secret_access_key"],
        "optional_fields": ["aws_region", "model_name"],
    },
    "vertex": {
        "name": "Google Vertex AI",
        "description": "Google Cloud Vertex AI credentials",
        "example_models": ["text-bison", "chat-bison", "gemini-pro"],
        "required_fields": ["project_id", "location"],
        "optional_fields": ["service_account_key", "model_name"],
    },
    "huggingface": {
        "name": "Hugging Face",
        "description": "Hugging Face API tokens",
        "example_models": [
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
        ],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "groq": {
        "name": "Groq",
        "description": "Groq API keys for fast inference",
        "example_models": ["llama2-70b-4096", "mixtral-8x7b-32768"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "perplexity": {
        "name": "Perplexity",
        "description": "Perplexity API keys",
        "example_models": ["pplx-7b-online", "pplx-70b-online"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "description": "DeepSeek API keys",
        "example_models": ["deepseek-chat", "deepseek-coder"],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "together": {
        "name": "Together AI",
        "description": "Together AI API keys",
        "example_models": [
            "togethercomputer/llama-2-7b-chat",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
        ],
        "required_fields": ["api_key"],
        "optional_fields": ["model_name"],
    },
    "ollama": {
        "name": "Ollama",
        "description": "Ollama local server",
        "example_models": ["llama2", "codellama", "mistral"],
        "required_fields": ["endpoint"],
        "optional_fields": ["model_name"],
    },
}


@router.get("/providers")
async def get_provider_configs() -> dict[str, Any]:
    """Get available provider configurations."""
    return {
        "providers": PROVIDER_CONFIGS,
        "total_providers": len(PROVIDER_CONFIGS),
    }
