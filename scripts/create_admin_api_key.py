#!/usr/bin/env python3
"""Create an admin API key for testing the dashboard."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_async_session
from app.models.user import User, ApiKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import hashlib


async def create_admin_api_key():
    """Create an admin API key."""
    async for db in get_async_session():
        try:
            # Check if admin user exists
            result = await db.execute(
                select(User).where(User.email == "admin@aideator.dev")
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                # Create admin user
                admin_user = User(
                    email="admin@aideator.dev",
                    name="Admin User",
                    is_active=True
                )
                db.add(admin_user)
                await db.flush()
                print(f"Created admin user: {admin_user.email}")
            
            # Generate API key
            api_key = f"aideator_admin_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Create API key record
            api_key_record = ApiKey(
                user_id=admin_user.id,
                name="Admin Dashboard",
                key_hash=key_hash,
                is_active=True
            )
            db.add(api_key_record)
            await db.commit()
            
            print("\n" + "="*60)
            print("🔑 Admin API Key Created Successfully!")
            print("="*60)
            print(f"API Key: {api_key}")
            print(f"User: {admin_user.email}")
            print(f"Key ID: {api_key_record.id}")
            print("="*60)
            print("\n💡 Copy this API key and paste it in the admin dashboard")
            print("   when prompted. This key will not be shown again!")
            print("\n🚀 Now refresh your admin dashboard to use it.")
            
            return api_key
            
        except Exception as e:
            print(f"❌ Error creating API key: {e}")
            await db.rollback()
            return None


if __name__ == "__main__":
    asyncio.run(create_admin_api_key())