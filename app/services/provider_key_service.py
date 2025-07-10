"""
Service for managing provider API keys.
"""

import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.provider_key import ProviderAPIKeyDB, ProviderAPIKeyAuditLog
from app.models.user import User
from app.services.encryption_service import get_encryption_service
from app.core.config import logger


class ProviderKeyService:
    """Service for managing encrypted provider API keys."""
    
    def __init__(self):
        self.encryption = get_encryption_service()
        
    async def create_provider_key(
        self,
        session: Session,
        user: User,
        provider: str,
        api_key: str,
        name: Optional[str] = None,
        model_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
        
        # Create audit log entry
        audit_log = ProviderAPIKeyAuditLog(
            id=f"audit_{secrets.token_urlsafe(12)}",
            user_id=user.id,
            provider_key_id=key_id,
            action="created",
            details={
                "provider": provider,
                "model_name": model_name,
                "name": name,
            }
        )
        session.add(audit_log)
        
        session.commit()
        session.refresh(provider_key)
        
        logger.info(f"Created provider API key {key_id} for user {user.id}")
        return provider_key
    
    async def list_user_keys(
        self,
        session: Session,
        user: User,
        provider: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[ProviderAPIKeyDB]:
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
            query = query.where(ProviderAPIKeyDB.is_active == True)
        
        query = query.order_by(ProviderAPIKeyDB.created_at.desc())
        
        results = session.exec(query)
        return list(results)
    
    async def get_key_for_model(
        self,
        session: Session,
        user: User,
        provider: str,
        model_name: str,
    ) -> Optional[str]:
        """Get decrypted API key for a specific model.
        
        This method handles the fallback logic:
        1. First looks for a model-specific key
        2. Falls back to provider-level key
        
        Args:
            session: Database session
            user: User requesting the key
            provider: Provider name
            model_name: Model name
            
        Returns:
            Decrypted API key or None if not found
        """
        # First try model-specific key
        model_key = await self._get_active_key(session, user.id, provider, model_name)
        if model_key:
            try:
                decrypted = self.encryption.decrypt_api_key(model_key.encrypted_key)
                
                # Update usage tracking
                model_key.last_used_at = datetime.utcnow()
                model_key.total_requests += 1
                session.add(model_key)
                session.commit()
                
                # Audit log
                await self._create_audit_log(
                    session, user.id, model_key.id, "used",
                    {"model_name": model_name}
                )
                
                return decrypted
            except Exception as e:
                logger.error(f"Failed to decrypt model key {model_key.id}: {e}")
        
        # Fall back to provider-level key
        provider_key = await self._get_active_key(session, user.id, provider, None)
        if provider_key:
            try:
                decrypted = self.encryption.decrypt_api_key(provider_key.encrypted_key)
                
                # Update usage tracking
                provider_key.last_used_at = datetime.utcnow()
                provider_key.total_requests += 1
                session.add(provider_key)
                session.commit()
                
                # Audit log
                await self._create_audit_log(
                    session, user.id, provider_key.id, "used",
                    {"model_name": model_name, "fallback": True}
                )
                
                return decrypted
            except Exception as e:
                logger.error(f"Failed to decrypt provider key {provider_key.id}: {e}")
        
        return None
    
    async def update_provider_key(
        self,
        session: Session,
        user: User,
        key_id: str,
        api_key: Optional[str] = None,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
            update_details["name"] = name
        
        if is_active is not None:
            key.is_active = is_active
            update_details["is_active"] = is_active
        
        if metadata is not None:
            key.extra_metadata = metadata
            update_details["metadata_updated"] = True
        
        key.updated_at = datetime.utcnow()
        session.add(key)
        
        # Audit log
        await self._create_audit_log(
            session, user.id, key_id, "updated", update_details
        )
        
        session.commit()
        session.refresh(key)
        
        return key
    
    async def delete_provider_key(
        self,
        session: Session,
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
        key = session.get(ProviderAPIKeyDB, key_id)
        if not key or key.user_id != user.id:
            raise HTTPException(status_code=404, detail="Provider key not found")
        
        # Soft delete by deactivating
        key.is_active = False
        key.updated_at = datetime.utcnow()
        session.add(key)
        
        # Audit log
        await self._create_audit_log(
            session, user.id, key_id, "deleted",
            {"provider": key.provider, "model_name": key.model_name}
        )
        
        session.commit()
        
        logger.info(f"Deleted provider key {key_id} for user {user.id}")
        return True
    
    async def validate_provider_key(
        self,
        session: Session,
        user: User,
        key_id: str,
    ) -> bool:
        """Validate a provider key by making a test API call.
        
        Args:
            session: Database session
            user: User validating the key
            key_id: ID of the key to validate
            
        Returns:
            True if valid, False otherwise
        """
        key = session.get(ProviderAPIKeyDB, key_id)
        if not key or key.user_id != user.id:
            raise HTTPException(status_code=404, detail="Provider key not found")
        
        try:
            # Decrypt the key
            decrypted = self.encryption.decrypt_api_key(key.encrypted_key)
            
            # TODO: Make actual validation call to provider
            # For now, just check if decryption works
            is_valid = len(decrypted) > 0
            
            # Update validation status
            key.is_valid = is_valid
            key.last_validated_at = datetime.utcnow()
            key.last_error = None if is_valid else "Invalid key format"
            session.add(key)
            
            # Audit log
            await self._create_audit_log(
                session, user.id, key_id, "validated",
                {"is_valid": is_valid}
            )
            
            session.commit()
            
            return is_valid
            
        except Exception as e:
            key.is_valid = False
            key.last_validated_at = datetime.utcnow()
            key.last_error = str(e)
            session.add(key)
            session.commit()
            
            logger.error(f"Failed to validate key {key_id}: {e}")
            return False
    
    async def _get_active_key(
        self,
        session: Session,
        user_id: str,
        provider: str,
        model_name: Optional[str],
    ) -> Optional[ProviderAPIKeyDB]:
        """Get active key for provider/model combo."""
        query = select(ProviderAPIKeyDB).where(
            ProviderAPIKeyDB.user_id == user_id,
            ProviderAPIKeyDB.provider == provider,
            ProviderAPIKeyDB.is_active == True,
        )
        
        if model_name is None:
            query = query.where(ProviderAPIKeyDB.model_name.is_(None))
        else:
            query = query.where(ProviderAPIKeyDB.model_name == model_name)
        
        result = session.exec(query).first()
        return result
    
    async def _create_audit_log(
        self,
        session: Session,
        user_id: str,
        provider_key_id: str,
        action: str,
        details: Dict[str, Any],
    ):
        """Create audit log entry."""
        audit_log = ProviderAPIKeyAuditLog(
            id=f"audit_{secrets.token_urlsafe(12)}",
            user_id=user_id,
            provider_key_id=provider_key_id,
            action=action,
            details=details,
        )
        session.add(audit_log)