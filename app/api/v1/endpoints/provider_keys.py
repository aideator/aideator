"""
API endpoints for provider API key management.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import CurrentUser
from app.models.provider_key import ProviderAPIKeyDB
from app.services.provider_key_service import ProviderKeyService

router = APIRouter(tags=["provider-keys"])
provider_key_service = ProviderKeyService()


# Request/Response Models
class CreateProviderKeyRequest(BaseModel):
    """Request to create a new provider API key."""

    model_config = {"protected_namespaces": ()}

    provider: str = Field(..., description="Provider name: openai, anthropic, etc")
    api_key: str = Field(..., min_length=1, description="The API key to store")
    name: str | None = Field(None, description="User-friendly name for the key")
    model_name: str | None = Field(
        None, description="Optional: specific model override"
    )

    @validator("provider")
    def validate_provider(cls, v: str) -> str:
        valid_providers = [
            "openai",
            "anthropic",
            "google",
            "cohere",
            "together",
            "replicate",
            "huggingface",
            "azure",
            "bedrock",
            "vertex_ai",
        ]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {', '.join(valid_providers)}")
        return v.lower()


class UpdateProviderKeyRequest(BaseModel):
    """Request to update a provider API key."""

    api_key: str | None = Field(None, description="New API key (if changing)")
    name: str | None = Field(None, description="New name")
    is_active: bool | None = Field(None, description="Active status")


class ProviderKeyResponse(BaseModel):
    """Response containing provider key info (without the actual key)."""

    model_config = {"protected_namespaces": ()}

    id: str
    provider: str
    model_name: str | None
    name: str | None
    key_hint: str
    is_active: bool
    is_valid: bool | None
    last_validated_at: str | None
    last_used_at: str | None
    total_requests: int
    created_at: str

    @classmethod
    def from_db(cls, db_key: ProviderAPIKeyDB) -> "ProviderKeyResponse":
        return cls(
            id=db_key.id,
            provider=db_key.provider,
            model_name=db_key.model_name,
            name=db_key.name,
            key_hint=db_key.key_hint,
            is_active=db_key.is_active,
            is_valid=db_key.is_valid,
            last_validated_at=db_key.last_validated_at.isoformat()
            if db_key.last_validated_at
            else None,
            last_used_at=db_key.last_used_at.isoformat()
            if db_key.last_used_at
            else None,
            total_requests=db_key.total_requests,
            created_at=db_key.created_at.isoformat(),
        )


@router.post("/", response_model=ProviderKeyResponse)
async def create_provider_key(
    request: CreateProviderKeyRequest,
    current_user: CurrentUser,
    session: Session = Depends(get_session),
) -> ProviderKeyResponse:
    """Create a new provider API key."""
    db_key = await provider_key_service.create_provider_key_internal(
        session=session,
        user=current_user,
        provider=request.provider,
        api_key=request.api_key,
        name=request.name,
        model_name=request.model_name,
    )

    return ProviderKeyResponse.from_db(db_key)


@router.get("/", response_model=list[ProviderKeyResponse])
async def list_provider_keys(
    current_user: CurrentUser,
    session: Session = Depends(get_session),
    provider: str | None = Query(None, description="Filter by provider"),
    include_inactive: bool = Query(False, description="Include inactive keys"),
) -> list[ProviderKeyResponse]:
    """List all provider keys for the current user."""
    keys = await provider_key_service.list_user_keys(
        session=session,
        user=current_user,
        provider=provider,
        include_inactive=include_inactive,
    )

    return [ProviderKeyResponse.from_db(key) for key in keys]


@router.get("/{key_id}", response_model=ProviderKeyResponse)
async def get_provider_key(
    key_id: str,
    current_user: CurrentUser,
    session: Session = Depends(get_session),
) -> ProviderKeyResponse:
    """Get details of a specific provider key."""
    keys = await provider_key_service.list_user_keys(
        session=session,
        user=current_user,
        include_inactive=True,
    )

    for key in keys:
        if key.id == key_id:
            return ProviderKeyResponse.from_db(key)

    raise HTTPException(status_code=404, detail="Provider key not found")


@router.put("/{key_id}", response_model=ProviderKeyResponse)
async def update_provider_key(
    key_id: str,
    request: UpdateProviderKeyRequest,
    current_user: CurrentUser,
    session: Session = Depends(get_session),
) -> ProviderKeyResponse:
    """Update a provider API key."""
    db_key = await provider_key_service.update_provider_key_internal(
        session=session,
        user=current_user,
        key_id=key_id,
        api_key=request.api_key,
        name=request.name,
        is_active=request.is_active,
    )

    return ProviderKeyResponse.from_db(db_key)


@router.delete("/{key_id}")
async def delete_provider_key(
    key_id: str,
    current_user: CurrentUser,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete (deactivate) a provider API key."""
    success = await provider_key_service.delete_provider_key_internal(
        session=session,
        user=current_user,
        key_id=key_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Provider key not found")

    return {"status": "success", "message": "Provider key deleted"}


@router.post("/{key_id}/validate")
async def validate_provider_key(
    key_id: str,
    current_user: CurrentUser,
    session: Session = Depends(get_session),
) -> dict[str, str | bool]:
    """Validate a provider API key by making a test call."""
    is_valid = await provider_key_service.validate_provider_key(
        session=session,
        user=current_user,
        key_id=key_id,
    )

    return {
        "status": "success",
        "is_valid": is_valid,
        "message": "Key is valid" if is_valid else "Key validation failed",
    }


@router.get("/providers/list")
async def list_supported_providers() -> dict[str, Any]:
    """Get list of supported providers and their configuration."""
    return {
        "providers": [
            {
                "name": "openai",
                "display_name": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "requires_api_key": True,
                "key_format": "sk-...",
                "documentation_url": "https://platform.openai.com/api-keys",
            },
            {
                "name": "anthropic",
                "display_name": "Anthropic",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "requires_api_key": True,
                "key_format": "sk-ant-...",
                "documentation_url": "https://console.anthropic.com/settings/keys",
            },
            {
                "name": "google",
                "display_name": "Google AI",
                "models": ["gemini-pro", "gemini-pro-vision"],
                "requires_api_key": True,
                "key_format": "AI...",
                "documentation_url": "https://makersuite.google.com/app/apikey",
            },
            {
                "name": "cohere",
                "display_name": "Cohere",
                "models": ["command", "command-light"],
                "requires_api_key": True,
                "key_format": "...",
                "documentation_url": "https://dashboard.cohere.com/api-keys",
            },
            {
                "name": "together",
                "display_name": "Together AI",
                "models": ["mixtral-8x7b", "llama-2-70b"],
                "requires_api_key": True,
                "key_format": "...",
                "documentation_url": "https://api.together.xyz/settings/api-keys",
            },
        ]
    }
