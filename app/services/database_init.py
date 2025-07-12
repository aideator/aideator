"""
Database initialization service for populating model catalog.
"""

import logging
import secrets

from sqlmodel import Session, select

from app.core.auth import get_password_hash
from app.core.config import get_settings
from app.core.database import get_session
from app.models.provider import ModelDefinition
from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import APIKey, User
from app.services.model_catalog import model_catalog

logger = logging.getLogger(__name__)


class DatabaseInitService:
    """Service for initializing database with model catalog."""

    def __init__(self, db: Session):
        self.db = db

    def initialize_test_user(self) -> dict:
        """Initialize a test user for development."""
        try:
            logger.info("Initializing test user for development...")

            # Check if test user already exists
            existing_user = self.db.exec(
                select(User).where(User.email == "test@aideator.local")
            ).first()

            if existing_user:
                logger.info("Test user already exists")
                # Get existing API key
                existing_key = self.db.exec(
                    select(APIKey).where(
                        APIKey.user_id == existing_user.id,
                        APIKey.name == "Development Test Key",
                    )
                ).first()

                if existing_key:
                    # Make sure provider key exists too
                    self._create_provider_key_for_user(existing_user.id)

                    return {
                        "user_id": existing_user.id,
                        "email": existing_user.email,
                        "message": "Test user already exists",
                        "api_key_exists": True,
                    }
                # Create API key for existing user
                api_key = f"aid_sk_test_{secrets.token_urlsafe(32)}"
                key_hash = get_password_hash(api_key)

                key_record = APIKey(
                    id=f"key_test_{secrets.token_urlsafe(12)}",
                    user_id=existing_user.id,
                    key_hash=key_hash,
                    name="Development Test Key",
                    scopes=["read", "write"],
                )

                self.db.add(key_record)
                self.db.commit()

                # Also create provider key for existing user if needed
                self._create_provider_key_for_user(existing_user.id)

                logger.info(f"Created API key for test user: {api_key}")
                return {
                    "user_id": existing_user.id,
                    "email": existing_user.email,
                    "message": "Created API key for existing test user",
                    "api_key": api_key,
                }

            # Create test user
            test_user = User(
                id=f"user_test_{secrets.token_urlsafe(12)}",
                email="test@aideator.local",
                hashed_password=get_password_hash("testpass123"),
                full_name="Test User",
                company="AIdeator Development",
                is_active=True,
                is_superuser=False,
            )

            self.db.add(test_user)
            self.db.commit()
            self.db.refresh(test_user)

            # Create API key for test user
            api_key = f"aid_sk_test_{secrets.token_urlsafe(32)}"
            key_hash = get_password_hash(api_key)

            key_record = APIKey(
                id=f"key_test_{secrets.token_urlsafe(12)}",
                user_id=test_user.id,
                key_hash=key_hash,
                name="Development Test Key",
                scopes=["read", "write"],
            )

            self.db.add(key_record)
            self.db.commit()

            # Create provider key for OpenAI if available in settings
            self._create_provider_key_for_user(test_user.id)

            logger.info(f"Test user created: {test_user.email}")
            logger.info(f"Test API key: {api_key}")

            return {
                "user_id": test_user.id,
                "email": test_user.email,
                "password": "testpass123",
                "api_key": api_key,
                "message": "Test user created successfully",
            }

        except Exception as e:
            logger.error(f"Error initializing test user: {e}")
            self.db.rollback()
            raise

    def initialize_model_catalog(self) -> None:
        """Initialize the model catalog in the database."""
        try:
            logger.info("Initializing model catalog...")

            # Get all models from the catalog service
            catalog_models = model_catalog.to_model_definitions()

            # Get existing models from database
            existing_models = self.db.exec(select(ModelDefinition)).all()
            existing_model_map = {model.id: model for model in existing_models}

            # Track changes
            added_count = 0
            updated_count = 0

            for catalog_model in catalog_models:
                existing_model = existing_model_map.get(catalog_model.id)

                if existing_model:
                    # Update existing model
                    existing_model.display_name = catalog_model.display_name
                    existing_model.description = catalog_model.description
                    existing_model.context_window = catalog_model.context_window
                    existing_model.max_output_tokens = catalog_model.max_output_tokens
                    existing_model.input_price_per_1m_tokens = (
                        catalog_model.input_price_per_1m_tokens
                    )
                    existing_model.output_price_per_1m_tokens = (
                        catalog_model.output_price_per_1m_tokens
                    )
                    existing_model.capabilities = catalog_model.capabilities
                    existing_model.requires_api_key = catalog_model.requires_api_key
                    existing_model.requires_region = catalog_model.requires_region
                    existing_model.requires_project_id = (
                        catalog_model.requires_project_id
                    )
                    existing_model.default_parameters = catalog_model.default_parameters
                    existing_model.is_active = catalog_model.is_active

                    updated_count += 1
                else:
                    # Add new model
                    self.db.add(catalog_model)
                    added_count += 1

            # Mark models not in catalog as inactive
            catalog_ids = {model.id for model in catalog_models}
            for existing_model in existing_models:
                if existing_model.id not in catalog_ids:
                    existing_model.is_active = False
                    updated_count += 1

            # Commit changes
            self.db.commit()

            logger.info(
                f"Model catalog initialized: {added_count} added, {updated_count} updated"
            )

        except Exception as e:
            logger.error(f"Error initializing model catalog: {e}")
            self.db.rollback()
            raise

    def get_model_statistics(self) -> dict:
        """Get statistics about the model catalog."""
        try:
            total_models = self.db.exec(select(ModelDefinition)).all()
            active_models = self.db.exec(
                select(ModelDefinition).where(ModelDefinition.is_active)
            ).all()

            # Group by provider
            provider_stats = {}
            for model in active_models:
                provider = model.provider.value
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        "count": 0,
                        "requires_api_key": 0,
                        "free_models": 0,
                        "avg_price": 0,
                        "prices": [],
                    }

                provider_stats[provider]["count"] += 1

                if model.requires_api_key:
                    provider_stats[provider]["requires_api_key"] += 1
                else:
                    provider_stats[provider]["free_models"] += 1

                if model.input_price_per_1m_tokens:
                    provider_stats[provider]["prices"].append(
                        model.input_price_per_1m_tokens
                    )

            # Calculate average prices
            for provider, stats in provider_stats.items():
                if stats["prices"]:
                    stats["avg_price"] = sum(stats["prices"]) / len(stats["prices"])
                    stats["min_price"] = min(stats["prices"])
                    stats["max_price"] = max(stats["prices"])
                del stats["prices"]  # Remove raw prices from output

            return {
                "total_models": len(total_models),
                "active_models": len(active_models),
                "inactive_models": len(total_models) - len(active_models),
                "provider_stats": provider_stats,
            }

        except Exception as e:
            logger.error(f"Error getting model statistics: {e}")
            return {}

    def _create_provider_key_for_user(self, user_id: str) -> None:
        """Create provider key for OpenAI if available in settings."""
        settings = get_settings()
        if not settings.openai_api_key:
            return

        try:
            # Check if OpenAI provider key already exists
            existing_provider_key = self.db.exec(
                select(ProviderAPIKeyDB).where(
                    ProviderAPIKeyDB.user_id == user_id,
                    ProviderAPIKeyDB.provider == "openai",
                    ProviderAPIKeyDB.is_active,
                )
            ).first()

            if not existing_provider_key:
                # Create the provider key manually since we can't use async here
                from app.services.encryption_service import get_encryption_service

                encryption_service = get_encryption_service()
                encrypted_key, key_hint = encryption_service.encrypt_api_key(
                    settings.openai_api_key
                )

                key_id = f"provkey_{secrets.token_urlsafe(12)}"

                provider_key = ProviderAPIKeyDB(
                    id=key_id,
                    user_id=user_id,
                    provider="openai",
                    model_name=None,
                    encrypted_key=encrypted_key,
                    key_hint=key_hint,
                    name="Development OpenAI Key",
                    extra_metadata={
                        "description": "Auto-created from .env for development"
                    },
                )

                self.db.add(provider_key)
                # Note: commit will be called by the parent method

                logger.info(
                    f"Created OpenAI provider key for user {user_id}: {key_hint}"
                )
            else:
                logger.info(f"OpenAI provider key already exists for user {user_id}")

        except Exception as e:
            logger.warning(
                f"Failed to create OpenAI provider key for user {user_id}: {e}"
            )
            # Don't fail the entire test user creation if provider key fails


def initialize_database(create_test_user: bool = False):
    """Initialize the database with default data."""
    logger.info("Starting database initialization...")

    try:
        # Get database session
        db = next(get_session())

        # Initialize services
        init_service = DatabaseInitService(db)

        # Initialize model catalog
        init_service.initialize_model_catalog()

        # Initialize test user for development
        if create_test_user:
            test_user_info = init_service.initialize_test_user()
            logger.info(f"Test user initialization: {test_user_info}")

        # Get and log statistics
        stats = init_service.get_model_statistics()
        logger.info(f"Database initialized successfully: {stats}")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Run initialization
    initialize_database()
