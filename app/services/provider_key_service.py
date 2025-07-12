"""
Service for managing provider API keys.
"""

import secrets
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select

from app.core.logging import get_logger
from app.models.provider_key import ProviderAPIKeyAuditLog, ProviderAPIKeyDB
from app.models.user import User
from app.services.encryption_service import get_encryption_service

logger = get_logger(__name__)


class ProviderKeyService:
    """Service for managing encrypted provider API keys."""

    def __init__(self, db: Session | AsyncSession | None = None) -> None:
        self.encryption = get_encryption_service()
        self.db = db

    async def create_provider_key_internal(
        self,
        session: Session | AsyncSession,
        user: User,
        provider: str,
        api_key: str,
        name: str | None = None,
        model_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderAPIKeyDB:
        """Create a new provider API key.

        Args:
            session: Database session
            user: User creating the key
            provider: Provider name (openai, anthropic, etc)
            api_key: The plaintext API key to store
            name: Optional user-friendly name
            model_name: Optional specific model override
            metadata: Optional additional metadata

        Returns:
            Created ProviderAPIKeyDB instance (without decrypted key)
        """
        # Check if user already has an active key for this provider/model combo
        existing = await self._get_active_key(session, user.id, provider, model_name)
        if existing:
            # Deactivate the old key
            existing.is_active = False
            existing.updated_at = datetime.utcnow()
            session.add(existing)

        # Encrypt the API key
        encrypted_key, key_hint = self.encryption.encrypt_api_key(api_key)

        # Generate unique ID
        key_id = f"provkey_{secrets.token_urlsafe(12)}"

        # Create the key record
        provider_key = ProviderAPIKeyDB(
            id=key_id,
            user_id=user.id,
            provider=provider,
            model_name=model_name,
            encrypted_key=encrypted_key,
            key_hint=key_hint,
            name=name or f"{provider.title()} API Key",
            extra_metadata=metadata or {},
        )

        session.add(provider_key)
        
        # Flush to ensure provider_key is inserted first
        if isinstance(session, AsyncSession):
            await session.flush()
        else:
            session.flush()

        # Create audit log entry after provider key is flushed
        audit_log = ProviderAPIKeyAuditLog(
            id=f"audit_{secrets.token_urlsafe(12)}",
            user_id=user.id,
            provider_key_id=key_id,
            action="created",
            details={
                "provider": provider,
                "model_name": model_name,
                "name": name,
            },
        )
        session.add(audit_log)

        # Don't commit here - let the session manager handle it
        # The key is already populated with all necessary fields

        logger.info(f"Created provider API key {key_id} for user {user.id}")
        return provider_key

    async def list_user_keys(
        self,
        session: Session | AsyncSession,
        user: User,
        provider: str | None = None,
        include_inactive: bool = False,
    ) -> list[ProviderAPIKeyDB]:
        """List all provider keys for a user.

        Args:
            session: Database session
            user: User to list keys for
            provider: Optional filter by provider
            include_inactive: Whether to include inactive keys

        Returns:
            List of ProviderAPIKeyDB instances (without decrypted keys)
        """
        query = select(ProviderAPIKeyDB).where(ProviderAPIKeyDB.user_id == user.id)

        if provider:
            query = query.where(ProviderAPIKeyDB.provider == provider)

        if not include_inactive:
            query = query.where(ProviderAPIKeyDB.is_active)

        query = query.order_by(desc(ProviderAPIKeyDB.created_at))  # type: ignore[arg-type]

        if isinstance(session, AsyncSession):
            results = await session.execute(query)
            return list(results.scalars().all())
        results = session.exec(query)
        return list(results)

    async def get_key_for_model(
        self,
        session: Session | AsyncSession,
        user: User,
        model: str,
    ) -> ProviderAPIKeyDB | None:
        """Get provider key for a specific model.

        This method handles the fallback logic:
        1. Infers provider from model name
        2. First looks for a model-specific key
        3. Falls back to provider-level key

        Args:
            session: Database session
            user: User requesting the key
            model: Model name

        Returns:
            Provider key or None if not found
        """
        # Infer provider from model name
        provider = self._infer_provider_from_model(model)

        # First try model-specific key
        model_key = await self._get_active_key(session, user.id, provider, model)
        if model_key:
            # Update usage tracking
            model_key.last_used_at = datetime.utcnow()
            model_key.total_requests += 1
            session.add(model_key)
            # Let session manager handle commit

            # Audit log
            await self._create_audit_log(
                session, user.id, model_key.id, "used", {"model_name": model}
            )

            return model_key

        # Fall back to provider-level key
        provider_key = await self._get_active_key(session, user.id, provider, None)
        if provider_key:
            # Update usage tracking
            provider_key.last_used_at = datetime.utcnow()
            provider_key.total_requests += 1
            session.add(provider_key)
            # Let session manager handle commit

            # Audit log
            await self._create_audit_log(
                session,
                user.id,
                provider_key.id,
                "used",
                {"model_name": model, "fallback": True},
            )

            return provider_key

        return None

    async def update_provider_key_internal(
        self,
        session: Session | AsyncSession,
        user: User,
        key_id: str,
        api_key: str | None = None,
        name: str | None = None,
        is_active: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderAPIKeyDB:
        """Update an existing provider key.

        Args:
            session: Database session
            user: User updating the key
            key_id: ID of the key to update
            api_key: Optional new API key
            name: Optional new name
            is_active: Optional active status
            metadata: Optional new metadata

        Returns:
            Updated ProviderAPIKeyDB instance
        """
        # Get the key
        if isinstance(session, AsyncSession):
            key = await session.get(ProviderAPIKeyDB, key_id)
        else:
            key = session.get(ProviderAPIKeyDB, key_id)
        if not key or key.user_id != user.id:
            raise HTTPException(status_code=404, detail="Provider key not found")

        update_details = {}

        # Update API key if provided
        if api_key is not None:
            encrypted_key, key_hint = self.encryption.encrypt_api_key(api_key)
            key.encrypted_key = encrypted_key
            key.key_hint = key_hint
            update_details["key_updated"] = True

        # Update other fields
        if name is not None:
            key.name = name
            update_details["name_updated"] = True

        if is_active is not None:
            key.is_active = bool(is_active)
            update_details["is_active_updated"] = True

        if metadata is not None:
            key.extra_metadata = metadata
            update_details["metadata_updated"] = True

        key.updated_at = datetime.utcnow()
        session.add(key)

        # Audit log
        await self._create_audit_log(
            session, user.id, key_id, "updated", update_details
        )

        # Let session manager handle commit
        # Just refresh to get updated values
        if isinstance(session, AsyncSession):
            await session.refresh(key)
        else:
            session.refresh(key)

        return key

    async def delete_provider_key_internal(
        self,
        session: Session | AsyncSession,
        user: User,
        key_id: str,
    ) -> bool:
        """Delete a provider key (soft delete by deactivating).

        Args:
            session: Database session
            user: User deleting the key
            key_id: ID of the key to delete

        Returns:
            True if deleted successfully
        """
        if isinstance(session, AsyncSession):
            key = await session.get(ProviderAPIKeyDB, key_id)
        else:
            key = session.get(ProviderAPIKeyDB, key_id)
        if not key or key.user_id != user.id:
            raise HTTPException(status_code=404, detail="Provider key not found")

        # Soft delete by deactivating
        key.is_active = False
        key.updated_at = datetime.utcnow()
        session.add(key)

        # Audit log
        await self._create_audit_log(
            session,
            user.id,
            key_id,
            "deleted",
            {"provider": key.provider, "model_name": key.model_name},
        )

        # Let session manager handle commit

        logger.info(f"Deleted provider key {key_id} for user {user.id}")
        return True

    async def validate_provider_key(
        self,
        session: Session | AsyncSession,
        user: User,
        key_id: str,
    ) -> bool:
        """Validate a provider key by checking if it can be decrypted.

        Args:
            session: Database session
            user: User validating the key
            key_id: ID of the key to validate

        Returns:
            True if valid, False otherwise
        """
        if isinstance(session, AsyncSession):
            key = await session.get(ProviderAPIKeyDB, key_id)
        else:
            key = session.get(ProviderAPIKeyDB, key_id)
        if not key or key.user_id != user.id:
            raise HTTPException(status_code=404, detail="Provider key not found")

        try:
            # Decrypt the key to verify it's valid
            decrypted = self.encryption.decrypt_api_key(key.encrypted_key)

            # Basic validation: check if key has reasonable format
            is_valid = len(decrypted) > 10  # Most API keys are longer than 10 chars

            # Update validation status
            key.is_valid = is_valid
            key.last_validated_at = datetime.utcnow()
            key.last_error = None if is_valid else "Key appears to be too short"
            session.add(key)

            # Audit log
            await self._create_audit_log(
                session, user.id, key_id, "validated", {"is_valid": is_valid}
            )

            # Let session manager handle commit

            return is_valid

        except Exception as e:
            key.is_valid = False
            key.last_validated_at = datetime.utcnow()
            key.last_error = str(e)
            session.add(key)
            # Let session manager handle commit

            logger.error(f"Failed to validate key {key_id}: {e}")
            return False

    async def _get_active_key(
        self,
        session: Session | AsyncSession,
        user_id: str,
        provider: str,
        model_name: str | None,
    ) -> ProviderAPIKeyDB | None:
        """Get active key for provider/model combo."""
        query = select(ProviderAPIKeyDB).where(
            ProviderAPIKeyDB.user_id == user_id,
            ProviderAPIKeyDB.provider == provider,
            ProviderAPIKeyDB.is_active,
        )

        if model_name is None:
            query = query.where(ProviderAPIKeyDB.model_name.is_(None))  # type: ignore[union-attr]
        else:
            query = query.where(ProviderAPIKeyDB.model_name == model_name)

        if isinstance(session, AsyncSession):
            result = await session.execute(query)
            return result.scalar_one_or_none()
        return session.exec(query).first()

    async def _create_audit_log(
        self,
        session: Session | AsyncSession,
        user_id: str,
        provider_key_id: str,
        action: str,
        details: dict[str, Any],
    ) -> None:
        """Create audit log entry."""
        audit_log = ProviderAPIKeyAuditLog(
            id=f"audit_{secrets.token_urlsafe(12)}",
            user_id=user_id,
            provider_key_id=provider_key_id,
            action=action,
            details=details,
        )
        session.add(audit_log)

    # API compatibility methods
    async def create_provider_key(
        self,
        user_id: str,
        provider_type: str,
        name: str,
        api_key: str,
        model_name: str | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderAPIKeyDB:
        """Create a new provider API key (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        from app.models.user import User

        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add IP address to metadata if provided
        if ip_address:
            metadata = metadata or {}
            metadata["ip_address"] = ip_address

        return await self.create_provider_key_internal(
            session=self.db,
            user=user,
            provider=provider_type,
            api_key=api_key,
            name=name,
            model_name=model_name,
            metadata=metadata,
        )

    async def get_user_provider_keys(self, user_id: str) -> list[ProviderAPIKeyDB]:
        """Get all provider keys for a user (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        from app.models.user import User

        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return await self.list_user_keys(self.db, user)

    async def get_provider_key(self, key_id: str) -> ProviderAPIKeyDB | None:
        """Get a specific provider key by ID (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        return self.db.get(ProviderAPIKeyDB, key_id)

    async def update_provider_key(
        self,
        credential_id: str,
        name: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderAPIKeyDB:
        """Update a provider key (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        key = self.db.get(ProviderAPIKeyDB, credential_id)
        if not key:
            raise HTTPException(status_code=404, detail="Provider key not found")

        from app.models.user import User

        user = self.db.get(User, key.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return await self.update_provider_key_internal(
            session=self.db,
            user=user,
            key_id=credential_id,
            api_key=api_key,
            name=name,
            metadata=metadata,
        )

    async def test_provider_key(self, key_id: str) -> dict[str, Any]:
        """Test a provider key (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        key = self.db.get(ProviderAPIKeyDB, key_id)
        if not key:
            raise HTTPException(status_code=404, detail="Provider key not found")

        from app.models.user import User

        user = self.db.get(User, key.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        is_valid = await self.validate_provider_key(self.db, user, key_id)

        return {
            "key_id": key_id,
            "is_valid": is_valid,
            "provider": key.provider,
            "model_name": key.model_name,
            "test_timestamp": datetime.utcnow().isoformat(),
        }

    async def get_provider_key_usage(self, key_id: str) -> dict[str, Any]:
        """Get usage statistics for a provider key (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        key = self.db.get(ProviderAPIKeyDB, key_id)
        if not key:
            raise HTTPException(status_code=404, detail="Provider key not found")

        return {
            "key_id": key_id,
            "total_requests": key.total_requests,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "created_at": key.created_at.isoformat(),
            "updated_at": key.updated_at.isoformat(),
            "is_active": key.is_active,
            "total_tokens": key.total_tokens,
            "total_cost": key.total_cost,
        }

    async def delete_provider_key(self, key_id: str) -> bool:
        """Delete a provider key (API compatibility method)."""
        if not self.db:
            raise ValueError("Database session not provided")

        key = self.db.get(ProviderAPIKeyDB, key_id)
        if not key:
            raise HTTPException(status_code=404, detail="Provider key not found")

        from app.models.user import User

        user = self.db.get(User, key.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return await self.delete_provider_key_internal(
            session=self.db,
            user=user,
            key_id=key_id,
        )

    async def track_usage(
        self,
        session: Session | AsyncSession,
        provider_key_id: str,
        tokens_used: int,
        cost_usd: float,
    ) -> None:
        """Track usage for a provider key."""
        if isinstance(session, AsyncSession):
            key = await session.get(ProviderAPIKeyDB, provider_key_id)
        else:
            key = session.get(ProviderAPIKeyDB, provider_key_id)
        if not key:
            return

        key.total_tokens += tokens_used
        key.total_cost += cost_usd
        key.total_requests += 1
        key.last_used_at = datetime.utcnow()

        session.add(key)
        # Let session manager handle commit

    async def decrypt_api_key(
        self,
        session: Session | AsyncSession,
        user: User,
        provider_key_id: str,
    ) -> str:
        """Decrypt an API key."""
        if isinstance(session, AsyncSession):
            key = await session.get(ProviderAPIKeyDB, provider_key_id)
        else:
            key = session.get(ProviderAPIKeyDB, provider_key_id)
        if not key or key.user_id != user.id:
            raise HTTPException(status_code=404, detail="Provider key not found")

        return self.encryption.decrypt_api_key(key.encrypted_key)

    async def get_provider_key_for_user(
        self,
        session: Session | AsyncSession,
        user: User,
        provider_key_id: str,
    ) -> ProviderAPIKeyDB | None:
        """Get a provider key by ID for a specific user."""
        if isinstance(session, AsyncSession):
            key = await session.get(ProviderAPIKeyDB, provider_key_id)
        else:
            key = session.get(ProviderAPIKeyDB, provider_key_id)
        if not key or key.user_id != user.id:
            return None
        return key

    def _infer_provider_from_model(self, model_name: str) -> str:
        """Infer provider from model name.

        Args:
            model_name: The name of the model

        Returns:
            The provider name
        """
        model_lower = model_name.lower()

        # OpenAI models
        if any(
            prefix in model_lower
            for prefix in [
                "gpt",
                "text-davinci",
                "text-curie",
                "text-babbage",
                "text-ada",
                "dall-e",
                "whisper",
                "tts",
            ]
        ):
            return "openai"

        # Anthropic models
        if any(
            prefix in model_lower
            for prefix in ["claude", "claude-3", "claude-2", "claude-instant"]
        ):
            return "anthropic"

        # Google models
        if any(
            prefix in model_lower
            for prefix in ["gemini", "palm", "bard", "text-bison", "chat-bison"]
        ):
            return "google"

        # Vertex AI models
        if any(prefix in model_lower for prefix in ["vertex", "vertex_ai"]):
            return "vertex_ai"

        # Cohere models
        if any(
            prefix in model_lower
            for prefix in ["cohere", "command", "embed-english", "embed-multilingual"]
        ):
            return "cohere"

        # Groq models
        if any(
            prefix in model_lower
            for prefix in ["groq", "llama2-70b", "mixtral-8x7b", "gemma-7b"]
        ):
            return "groq"

        # Mistral models
        if any(prefix in model_lower for prefix in ["mistral", "mixtral", "codestral"]):
            return "mistral"

        # Perplexity models
        if any(prefix in model_lower for prefix in ["perplexity", "pplx"]):
            return "perplexity"

        # DeepSeek models
        if any(
            prefix in model_lower
            for prefix in ["deepseek", "deepseek-chat", "deepseek-coder"]
        ):
            return "deepseek"

        # XAI models
        if any(prefix in model_lower for prefix in ["xai", "grok"]):
            return "xai"

        # Fireworks models
        if any(
            prefix in model_lower
            for prefix in ["fireworks", "llama-v2", "llama-v3", "starcoder"]
        ):
            return "fireworks"

        # Together AI models
        if any(
            prefix in model_lower
            for prefix in ["together", "llama-2", "llama-3", "qwen", "meta-llama"]
        ):
            return "together"

        # Bedrock models
        if any(
            prefix in model_lower for prefix in ["bedrock", "amazon", "ai21", "titan"]
        ):
            return "bedrock"

        # Azure models
        if any(prefix in model_lower for prefix in ["azure"]):
            return "azure"

        # Ollama models
        if any(prefix in model_lower for prefix in ["ollama"]):
            return "ollama"

        # Hugging Face models
        if any(prefix in model_lower for prefix in ["huggingface", "hf"]):
            return "huggingface"

        # Default to OpenAI for unknown models
        return "openai"
