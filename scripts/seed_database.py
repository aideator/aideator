#!/usr/bin/env python3
"""
Database seeding script for development.
Creates a test user and API key for development.
"""

import asyncio
import logging
import secrets
import sys
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

from app.core.auth import get_password_hash
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.models.user import APIKey, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def create_test_user():
    """Create a test user and API key for development."""
    async with async_session_maker() as session:
        try:
            # Check if test user already exists
            result = await session.execute(
                select(User).where(User.email == "test@aideator.local")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info("Test user already exists")

                # Check for existing API key
                result = await session.execute(
                    select(APIKey).where(
                        APIKey.user_id == existing_user.id,
                        APIKey.name == "Development Test Key"
                    )
                )
                existing_key = result.scalar_one_or_none()

                if existing_key:
                    logger.info("Test API key already exists")
                    return {
                        "user_id": existing_user.id,
                        "email": existing_user.email,
                        "message": "Test user and API key already exist"
                    }
                # Create new API key for existing user
                api_key_value = f"aid_sk_test_{secrets.token_urlsafe(32)}"
                api_key_hash = get_password_hash(api_key_value)

                new_key = APIKey(
                    id=f"key_test_{secrets.token_urlsafe(12)}",
                    user_id=existing_user.id,
                    key_hash=api_key_hash,
                    name="Development Test Key",
                    scopes=["read", "write"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    total_requests=0,
                    total_runs=0
                )

                session.add(new_key)
                await session.commit()

                logger.info("Created new API key for existing test user")
                print_credentials(existing_user.email, "testpass123", api_key_value)

                return {
                    "user_id": existing_user.id,
                    "email": existing_user.email,
                    "api_key": api_key_value,
                    "message": "Created new API key for existing test user"
                }

            # Create new test user
            test_user = User(
                id=f"user_test_{secrets.token_urlsafe(12)}",
                email="test@aideator.local",
                hashed_password=get_password_hash("testpass123"),
                full_name="Test User",
                company="AIdeator Development",
                is_active=True,
                is_superuser=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                max_runs_per_day=100,
                max_variations_per_run=5
            )

            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)

            # Create API key for test user
            api_key_value = f"aid_sk_test_{secrets.token_urlsafe(32)}"
            api_key_hash = get_password_hash(api_key_value)

            api_key = APIKey(
                id=f"key_test_{secrets.token_urlsafe(12)}",
                user_id=test_user.id,
                key_hash=api_key_hash,
                name="Development Test Key",
                scopes=["read", "write"],
                is_active=True,
                created_at=datetime.utcnow(),
                total_requests=0,
                total_runs=0
            )

            session.add(api_key)
            await session.commit()

            logger.info(f"Test user created successfully: {test_user.email}")
            print_credentials(test_user.email, "testpass123", api_key_value)

            return {
                "user_id": test_user.id,
                "email": test_user.email,
                "password": "testpass123",
                "api_key": api_key_value,
                "message": "Test user and API key created successfully"
            }

        except Exception as e:
            logger.error(f"Error creating test user: {e}")
            await session.rollback()
            raise


def print_credentials(email: str, password: str, api_key: str):
    """Print the credentials in a nice format."""
    print()
    print("=" * 50)
    print("🚀 DEVELOPMENT CREDENTIALS")
    print("=" * 50)
    print(f"📧 Email:    {email}")
    print(f"🔑 Password: {password}")
    print(f"🎫 API Key:  {api_key}")
    print("=" * 50)
    print()
    print("💡 You can now:")
    print("   • Log in to the frontend with email/password")
    print("   • Use the API key for backend requests")
    print("   • Test the development auto-login feature")
    print()


async def main():
    """Main entry point."""
    try:
        logger.info("Starting database seeding...")

        settings = get_settings()
        logger.info(f"Database URL: {settings.database_url}")

        result = await create_test_user()
        logger.info(f"Seeding completed: {result['message']}")

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
