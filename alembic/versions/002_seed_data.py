"""Seed data for development

Revision ID: 002
Revises: 001
Create Date: 2025-07-10 01:41:00.000000

"""
import secrets
from collections.abc import Sequence
from datetime import datetime

import bcrypt
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def upgrade() -> None:
    """Add seed data."""
    # Define table structures for data insertion
    users_table = table("users",
        column("id", String),
        column("email", String),
        column("hashed_password", String),
        column("is_active", Boolean),
        column("is_superuser", Boolean),
        column("created_at", DateTime),
        column("updated_at", DateTime),
        column("full_name", String),
        column("company", String),
        column("max_runs_per_day", Integer),
        column("max_variations_per_run", Integer),
    )

    api_keys_table = table("api_keys",
        column("id", String),
        column("user_id", String),
        column("key_hash", String),
        column("name", String),
        column("description", String),
        column("scopes", JSON),
        column("is_active", Boolean),
        column("created_at", DateTime),
        column("updated_at", DateTime),
        column("last_used_at", DateTime),
        column("expires_at", DateTime),
    )

    model_definitions_table = table("model_definitions",
        column("id", String),
        column("provider", String),
        column("display_name", String),
        column("description", Text),
        column("context_window", Integer),
        column("max_output_tokens", Integer),
        column("input_price_per_1m_tokens", Float),
        column("output_price_per_1m_tokens", Float),
        column("capabilities", JSON),
        column("requires_api_key", Boolean),
        column("requires_region", Boolean),
        column("requires_project_id", Boolean),
        column("default_parameters", JSON),
        column("is_active", Boolean),
        column("created_at", DateTime),
        column("updated_at", DateTime),
    )

    # Current timestamp
    now = datetime.utcnow()

    # Create test user
    test_user_id = f"user_test_{secrets.token_urlsafe(12)}"
    test_password_hash = hash_password("testpass123")

    op.bulk_insert(users_table, [
        {
            "id": test_user_id,
            "email": "test@aideator.local",
            "hashed_password": test_password_hash,
            "is_active": True,
            "is_superuser": False,
            "created_at": now,
            "updated_at": now,
            "full_name": "Test User",
            "company": "AIdeator Development",
            "max_runs_per_day": 100,
            "max_variations_per_run": 5,
        }
    ])

    # Create API key for test user
    api_key_value = f"aid_sk_test_{secrets.token_urlsafe(32)}"
    api_key_hash = hash_password(api_key_value)

    op.bulk_insert(api_keys_table, [
        {
            "id": f"key_test_{secrets.token_urlsafe(12)}",
            "user_id": test_user_id,
            "key_hash": api_key_hash,
            "name": "Development Test Key",
            "description": "API key for development testing",
            "scopes": ["read", "write"],
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_used_at": None,
            "expires_at": None,
        }
    ])

    # Add basic model definitions
    models_data = [
        {
            "id": "gpt-4o-mini",
            "provider": "openai",
            "display_name": "GPT-4o Mini",
            "description": "OpenAI GPT-4o Mini - Fast and efficient model for most tasks",
            "context_window": 128000,
            "max_output_tokens": 16384,
            "input_price_per_1m_tokens": 0.15,
            "output_price_per_1m_tokens": 0.60,
            "capabilities": ["text_generation", "code_generation", "analysis"],
            "requires_api_key": True,
            "requires_region": False,
            "requires_project_id": False,
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "gpt-4o",
            "provider": "openai",
            "display_name": "GPT-4o",
            "description": "OpenAI GPT-4o - Most capable multimodal model",
            "context_window": 128000,
            "max_output_tokens": 16384,
            "input_price_per_1m_tokens": 2.50,
            "output_price_per_1m_tokens": 10.00,
            "capabilities": ["text_generation", "code_generation", "analysis", "vision"],
            "requires_api_key": True,
            "requires_region": False,
            "requires_project_id": False,
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "display_name": "Claude 3.5 Sonnet",
            "description": "Anthropic Claude 3.5 Sonnet - Excellent for coding and analysis",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "input_price_per_1m_tokens": 3.00,
            "output_price_per_1m_tokens": 15.00,
            "capabilities": ["text_generation", "code_generation", "analysis", "reasoning"],
            "requires_api_key": True,
            "requires_region": False,
            "requires_project_id": False,
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0
            },
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "provider": "anthropic",
            "display_name": "Claude 3.5 Haiku",
            "description": "Anthropic Claude 3.5 Haiku - Fast and efficient for simple tasks",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "input_price_per_1m_tokens": 0.25,
            "output_price_per_1m_tokens": 1.25,
            "capabilities": ["text_generation", "code_generation", "analysis"],
            "requires_api_key": True,
            "requires_region": False,
            "requires_project_id": False,
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0
            },
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "gemini-1.5-pro",
            "provider": "google",
            "display_name": "Gemini 1.5 Pro",
            "description": "Google Gemini 1.5 Pro - Large context window multimodal model",
            "context_window": 2000000,
            "max_output_tokens": 8192,
            "input_price_per_1m_tokens": 1.25,
            "output_price_per_1m_tokens": 5.00,
            "capabilities": ["text_generation", "code_generation", "analysis", "vision"],
            "requires_api_key": True,
            "requires_region": False,
            "requires_project_id": True,
            "default_parameters": {
                "temperature": 0.7,
                "max_output_tokens": 4096,
                "top_p": 1.0
            },
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "gemini-1.5-flash",
            "provider": "google",
            "display_name": "Gemini 1.5 Flash",
            "description": "Google Gemini 1.5 Flash - Fast and efficient multimodal model",
            "context_window": 1000000,
            "max_output_tokens": 8192,
            "input_price_per_1m_tokens": 0.075,
            "output_price_per_1m_tokens": 0.30,
            "capabilities": ["text_generation", "code_generation", "analysis", "vision"],
            "requires_api_key": True,
            "requires_region": False,
            "requires_project_id": True,
            "default_parameters": {
                "temperature": 0.7,
                "max_output_tokens": 4096,
                "top_p": 1.0
            },
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    ]

    op.bulk_insert(model_definitions_table, models_data)

    # Print the API key for development use
    print("\\n=== DEVELOPMENT CREDENTIALS ===")
    print("Test User Email: test@aideator.local")
    print("Test User Password: testpass123")
    print(f"Test API Key: {api_key_value}")
    print("================================\\n")


def downgrade() -> None:
    """Remove seed data."""
    # Remove test user and related data (cascading deletes will handle the rest)
    op.execute("DELETE FROM users WHERE email = 'test@aideator.local'")

    # Remove model definitions
    op.execute("DELETE FROM model_definitions WHERE provider IN ('openai', 'anthropic', 'google')")
