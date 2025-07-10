"""
Integration tests for provider key service with real database.
"""

from datetime import datetime

import pytest
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.provider_key import ProviderAPIKeyAuditLog, ProviderAPIKeyDB
from app.models.user import User
from app.services.encryption_service import EncryptionService
from app.services.provider_key_service import ProviderKeyService


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with get_session() as session:
        yield session


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user in the database."""
    user = User(
        id="user_integration_test",
        email="integration@test.com",
        hashed_password="test_hash",
        is_active=True,
        full_name="Integration Test User",
        created_at=datetime.utcnow()
    )

    # Check if user already exists
    existing = db_session.exec(select(User).where(User.id == user.id)).first()
    if existing:
        return existing

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def encryption_service():
    """Create encryption service with test key."""
    return EncryptionService(master_key="test-master-key-32-characters-long")


@pytest.fixture
def provider_key_service(encryption_service):
    """Create provider key service with test encryption."""
    service = ProviderKeyService()
    service.encryption = encryption_service
    return service


class TestProviderKeyIntegration:
    """Integration tests for provider key service."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_provider_key(self, db_session, test_user, provider_key_service):
        """Test creating and retrieving a provider key."""
        # Create provider key
        provider_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-integration-1234567890abcdef",
            name="Integration Test Key"
        )

        # Verify key was created
        assert provider_key.id.startswith("provkey_")
        assert provider_key.provider == "openai"
        assert provider_key.name == "Integration Test Key"
        assert provider_key.key_hint == "...cdef"
        assert provider_key.is_active == True

        # Verify key exists in database
        db_key = db_session.get(ProviderAPIKeyDB, provider_key.id)
        assert db_key is not None
        assert db_key.user_id == test_user.id
        assert db_key.encrypted_key != "sk-test-integration-1234567890abcdef"  # Should be encrypted

        # Verify audit log was created
        audit_logs = db_session.exec(
            select(ProviderAPIKeyAuditLog).where(
                ProviderAPIKeyAuditLog.provider_key_id == provider_key.id
            )
        ).all()
        assert len(audit_logs) == 1
        assert audit_logs[0].action == "created"

    @pytest.mark.asyncio
    async def test_list_user_keys(self, db_session, test_user, provider_key_service):
        """Test listing user's provider keys."""
        # Create multiple keys
        key1 = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-key1-1234567890",
            name="OpenAI Key 1"
        )

        key2 = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="anthropic",
            api_key="sk-ant-test-key2-1234567890",
            name="Anthropic Key"
        )

        # List all keys
        keys = await provider_key_service.list_user_keys(
            session=db_session,
            user=test_user
        )

        assert len(keys) >= 2
        key_ids = [k.id for k in keys]
        assert key1.id in key_ids
        assert key2.id in key_ids

        # Test provider filter
        openai_keys = await provider_key_service.list_user_keys(
            session=db_session,
            user=test_user,
            provider="openai"
        )

        assert len(openai_keys) >= 1
        assert all(k.provider == "openai" for k in openai_keys)

    @pytest.mark.asyncio
    async def test_get_key_for_model_fallback(self, db_session, test_user, provider_key_service):
        """Test getting key for model with provider fallback."""
        # Create provider-level key
        await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-provider-level-key",
            name="Provider Level Key"
        )

        # Create model-specific key
        await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-model-specific-key",
            name="Model Specific Key",
            model_name="gpt-4"
        )

        # Test model-specific key is returned for gpt-4
        gpt4_key = await provider_key_service.get_key_for_model(
            session=db_session,
            user=test_user,
            provider="openai",
            model_name="gpt-4"
        )
        assert gpt4_key == "sk-test-model-specific-key"

        # Test fallback to provider key for gpt-3.5
        gpt35_key = await provider_key_service.get_key_for_model(
            session=db_session,
            user=test_user,
            provider="openai",
            model_name="gpt-3.5-turbo"
        )
        assert gpt35_key == "sk-test-provider-level-key"

        # Test no key for different provider
        claude_key = await provider_key_service.get_key_for_model(
            session=db_session,
            user=test_user,
            provider="anthropic",
            model_name="claude-3-opus"
        )
        assert claude_key is None

    @pytest.mark.asyncio
    async def test_update_provider_key(self, db_session, test_user, provider_key_service):
        """Test updating a provider key."""
        # Create initial key
        original_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-original-key",
            name="Original Name"
        )

        # Update the key
        updated_key = await provider_key_service.update_provider_key(
            session=db_session,
            user=test_user,
            key_id=original_key.id,
            api_key="sk-test-updated-key",
            name="Updated Name",
            is_active=False
        )

        # Verify updates
        assert updated_key.name == "Updated Name"
        assert updated_key.is_active == False
        assert updated_key.key_hint == "...dkey"  # Should show new key hint

        # Verify in database
        db_key = db_session.get(ProviderAPIKeyDB, original_key.id)
        assert db_key.name == "Updated Name"
        assert db_key.is_active == False

        # Verify audit log
        audit_logs = db_session.exec(
            select(ProviderAPIKeyAuditLog).where(
                ProviderAPIKeyAuditLog.provider_key_id == original_key.id,
                ProviderAPIKeyAuditLog.action == "updated"
            )
        ).all()
        assert len(audit_logs) >= 1

    @pytest.mark.asyncio
    async def test_delete_provider_key(self, db_session, test_user, provider_key_service):
        """Test deleting (deactivating) a provider key."""
        # Create key
        provider_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-delete-key",
            name="Key to Delete"
        )

        # Delete key
        success = await provider_key_service.delete_provider_key(
            session=db_session,
            user=test_user,
            key_id=provider_key.id
        )

        assert success == True

        # Verify key is deactivated
        db_key = db_session.get(ProviderAPIKeyDB, provider_key.id)
        assert db_key.is_active == False

        # Verify audit log
        audit_logs = db_session.exec(
            select(ProviderAPIKeyAuditLog).where(
                ProviderAPIKeyAuditLog.provider_key_id == provider_key.id,
                ProviderAPIKeyAuditLog.action == "deleted"
            )
        ).all()
        assert len(audit_logs) == 1

    @pytest.mark.asyncio
    async def test_validate_provider_key(self, db_session, test_user, provider_key_service):
        """Test validating a provider key."""
        # Create key
        provider_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-validate-key-long-enough",
            name="Key to Validate"
        )

        # Validate key
        is_valid = await provider_key_service.validate_provider_key(
            session=db_session,
            user=test_user,
            key_id=provider_key.id
        )

        assert is_valid == True

        # Verify validation status in database
        db_key = db_session.get(ProviderAPIKeyDB, provider_key.id)
        assert db_key.is_valid == True
        assert db_key.last_validated_at is not None
        assert db_key.last_error is None

        # Verify audit log
        audit_logs = db_session.exec(
            select(ProviderAPIKeyAuditLog).where(
                ProviderAPIKeyAuditLog.provider_key_id == provider_key.id,
                ProviderAPIKeyAuditLog.action == "validated"
            )
        ).all()
        assert len(audit_logs) == 1

    @pytest.mark.asyncio
    async def test_usage_tracking(self, db_session, test_user, provider_key_service):
        """Test usage tracking when retrieving keys."""
        # Create key
        provider_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="openai",
            api_key="sk-test-usage-tracking",
            name="Usage Test Key"
        )

        # Get key multiple times
        for i in range(3):
            key = await provider_key_service.get_key_for_model(
                session=db_session,
                user=test_user,
                provider="openai",
                model_name="gpt-4"
            )
            assert key == "sk-test-usage-tracking"

        # Verify usage was tracked
        db_key = db_session.get(ProviderAPIKeyDB, provider_key.id)
        assert db_key.total_requests == 3
        assert db_key.last_used_at is not None

    @pytest.mark.asyncio
    async def test_unique_constraint_enforcement(self, db_session, test_user, provider_key_service):
        """Test that unique constraint is enforced for active keys."""
        # Create first key
        key1 = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="google",
            api_key="first-google-key",
            name="First Google Key"
        )

        # Create second key for same provider (should deactivate first)
        key2 = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="google",
            api_key="second-google-key",
            name="Second Google Key"
        )

        # Verify first key was deactivated
        db_key1 = db_session.get(ProviderAPIKeyDB, key1.id)
        assert db_key1.is_active == False

        # Verify second key is active
        db_key2 = db_session.get(ProviderAPIKeyDB, key2.id)
        assert db_key2.is_active == True

    @pytest.mark.asyncio
    async def test_encryption_decryption_flow(self, db_session, test_user, provider_key_service):
        """Test that encryption/decryption works properly."""
        original_api_key = "sk-test-encryption-flow-1234567890"

        # Create key
        provider_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=test_user,
            provider="cohere",
            api_key=original_api_key,
            name="Encryption Test Key"
        )

        # Verify key is encrypted in database
        db_key = db_session.get(ProviderAPIKeyDB, provider_key.id)
        assert db_key.encrypted_key != original_api_key
        assert len(db_key.encrypted_key) > len(original_api_key)  # Encrypted should be longer

        # Verify we can retrieve the original key
        retrieved_key = await provider_key_service.get_key_for_model(
            session=db_session,
            user=test_user,
            provider="cohere",
            model_name="command"
        )
        assert retrieved_key == original_api_key

    @pytest.mark.asyncio
    async def test_cross_user_isolation(self, db_session, provider_key_service):
        """Test that users can't access each other's keys."""
        # Create two test users
        user1 = User(
            id="user_isolation_test_1",
            email="user1@test.com",
            hashed_password="hash1",
            is_active=True,
            full_name="User 1",
            created_at=datetime.utcnow()
        )

        user2 = User(
            id="user_isolation_test_2",
            email="user2@test.com",
            hashed_password="hash2",
            is_active=True,
            full_name="User 2",
            created_at=datetime.utcnow()
        )

        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        # User 1 creates a key
        user1_key = await provider_key_service.create_provider_key(
            session=db_session,
            user=user1,
            provider="openai",
            api_key="user1-secret-key",
            name="User 1 Key"
        )

        # User 2 should not see User 1's key
        user2_keys = await provider_key_service.list_user_keys(
            session=db_session,
            user=user2
        )

        user2_key_ids = [k.id for k in user2_keys]
        assert user1_key.id not in user2_key_ids

        # User 2 should not be able to get User 1's key for a model
        user2_retrieved_key = await provider_key_service.get_key_for_model(
            session=db_session,
            user=user2,
            provider="openai",
            model_name="gpt-4"
        )
        assert user2_retrieved_key is None
