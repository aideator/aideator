"""
Unit Tests for Core Services and Utilities

This test suite covers the core services, utilities, and business logic
components to increase overall test coverage.

Components Covered:
- Configuration management (app/core/config.py)
- Authentication utilities (app/core/auth.py)
- Database utilities (app/core/database.py)
- Dependency injection (app/core/dependencies.py, app/core/deps.py)
- Middleware components
- Schema validation
- Service layer components
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os

from fastapi import HTTPException
from pydantic import ValidationError
from jose import JWTError

# Core imports
from app.core.config import Settings, get_settings, KubernetesEnvironment
from app.core.auth import (
    verify_password, get_password_hash
)
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.logging import setup_logging
from app.schemas.auth import UserCreate, UserLogin, APIKeyCreate
from app.schemas.runs import RunCreate, RunResponse
from app.schemas.session import SessionCreate, PreferenceCreate
from app.schemas.common import PaginationParams
from app.models.user import User, APIKey


class TestConfigurationManagement:
    """Test configuration and settings management."""
    
    def test_settings_creation(self):
        """Test creating settings with default values."""
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            openai_api_key="sk-test-openai-key",
            anthropic_api_key="sk-ant-test-key",
            gemini_api_key="AIza-test-key"
        )
        
        assert settings.project_name == "AIdeator"
        assert settings.version == "1.0.0"
        assert settings.api_v1_prefix == "/api/v1"
        assert settings.debug is False
        assert settings.kubernetes_namespace == "aideator"
        assert settings.max_variations == 5
    
    def test_settings_validation_secret_key(self):
        """Test secret key validation."""
        # Test short secret key
        with pytest.raises(ValueError):
            Settings(secret_key="short")
        
        # Test valid secret key
        settings = Settings(secret_key="this-is-a-valid-secret-key-32-chars")
        assert len(settings.secret_key) >= 32
    
    def test_settings_validation_api_keys(self):
        """Test API key format validation."""
        # Test invalid OpenAI key
        with pytest.raises(ValueError):
            Settings(
                secret_key="test-secret-key-32-characters-long",
                openai_api_key="invalid-key"
            )
        
        # Test invalid Anthropic key
        with pytest.raises(ValueError):
            Settings(
                secret_key="test-secret-key-32-characters-long",
                anthropic_api_key="invalid-key"
            )
        
        # Test invalid Gemini key
        with pytest.raises(ValueError):
            Settings(
                secret_key="test-secret-key-32-characters-long",
                gemini_api_key="invalid-key"
            )
        
        # Test valid keys
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            openai_api_key="sk-test-key",
            anthropic_api_key="sk-ant-test-key",
            gemini_api_key="AIza-test-key"
        )
        assert settings.openai_api_key.startswith("sk-")
        assert settings.anthropic_api_key.startswith("sk-ant-")
        assert settings.gemini_api_key.startswith("AIza")
    
    def test_database_url_async_property(self):
        """Test database URL async property."""
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            database_url="postgresql://user:pass@localhost:5432/db"
        )
        
        async_url = settings.database_url_async
        assert "postgresql+asyncpg://" in async_url
    
    def test_kubernetes_secrets(self):
        """Test Kubernetes secrets generation."""
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            openai_api_key="sk-test-key",
            anthropic_api_key="sk-ant-test-key",
            gemini_api_key="AIza-test-key"
        )
        
        secrets = settings.get_kubernetes_secrets()
        assert "openai-api-key" in secrets
        assert "anthropic-api-key" in secrets
        assert "gemini-api-key" in secrets
        assert secrets["openai-api-key"] == "sk-test-key"
    
    def test_kubernetes_environment(self):
        """Test Kubernetes environment utilities."""
        agent_env = KubernetesEnvironment.get_agent_env(variation_id=1)
        assert agent_env["PYTHONUNBUFFERED"] == "1"
        assert agent_env["AGENT_VARIATION_ID"] == "1"
        assert agent_env["LOG_LEVEL"] == "INFO"
        
        build_args = KubernetesEnvironment.get_build_args()
        assert "PYTHON_VERSION" in build_args
        assert "WORKDIR" in build_args
    
    @patch.dict(os.environ, {"SECRET_KEY": "env-secret-key-32-characters-long"})
    def test_settings_from_environment(self):
        """Test loading settings from environment variables."""
        settings = Settings()
        assert settings.secret_key == "env-secret-key-32-characters-long"
    
    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Should be same instance due to lru_cache


class TestAuthenticationUtilities:
    """Test authentication utility functions."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_auth_functions_exist(self):
        """Test that core auth functions exist and can be called."""
        # Test password hashing functions work
        password = "test_password"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestSchemaValidation:
    """Test Pydantic schema validation."""
    
    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
        # Valid user data
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "company": "Test Company"
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        
        # Invalid email
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="password",
                full_name="Test User"
            )
    
    def test_run_create_schema(self):
        """Test RunCreate schema validation."""
        # Valid run data
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt",
            "variations": 3,
            "agent_config": {
                "model": "gpt-4",
                "temperature": 0.7
            }
        }
        run = RunCreate(**run_data)
        assert run.github_url == "https://github.com/test/repo"
        assert run.variations == 3
        
        # Invalid variations count
        with pytest.raises(ValidationError):
            RunCreate(
                github_url="https://github.com/test/repo",
                prompt="Test prompt",
                variations=0  # Should be >= 1
            )
        
        # Invalid URL
        with pytest.raises(ValidationError):
            RunCreate(
                github_url="not-a-url",
                prompt="Test prompt",
                variations=1
            )
    
    def test_session_create_schema(self):
        """Test SessionCreate schema validation."""
        session_data = {
            "title": "Test Session",
            "description": "Test description",
            "models_used": ["gpt-4", "claude-3-sonnet"]
        }
        session = SessionCreate(**session_data)
        assert session.title == "Test Session"
        assert len(session.models_used) == 2
        
        # Test title length validation
        with pytest.raises(ValidationError):
            SessionCreate(
                title="A" * 201,  # Too long
                models_used=["gpt-4"]
            )
    
    def test_preference_create_schema(self):
        """Test PreferenceCreate schema validation."""
        preference_data = {
            "preferred_model": "claude-3-sonnet",
            "preferred_response_id": "response_123",
            "compared_models": ["gpt-4", "claude-3-sonnet"],
            "response_quality_scores": {
                "gpt-4": 4,
                "claude-3-sonnet": 5
            },
            "confidence_score": 4
        }
        preference = PreferenceCreate(**preference_data)
        assert preference.preferred_model == "claude-3-sonnet"
        assert preference.confidence_score == 4
        
        # Test invalid quality scores
        with pytest.raises(ValidationError):
            PreferenceCreate(
                preferred_model="gpt-4",
                preferred_response_id="response_123",
                compared_models=["gpt-4", "claude-3-sonnet"],
                response_quality_scores={
                    "gpt-4": 6,  # Invalid score > 5
                    "claude-3-sonnet": 5
                }
            )
        
        # Test insufficient compared models
        with pytest.raises(ValidationError):
            PreferenceCreate(
                preferred_model="gpt-4",
                preferred_response_id="response_123",
                compared_models=["gpt-4"],  # Need at least 2
                response_quality_scores={"gpt-4": 5}
            )
    
    def test_api_key_create_schema(self):
        """Test APIKeyCreate schema validation."""
        api_key_data = {
            "name": "Test API Key",
            "description": "For testing purposes",
            "scopes": ["runs:create", "runs:read"],
            "expires_in_days": 90
        }
        api_key = APIKeyCreate(**api_key_data)
        assert api_key.name == "Test API Key"
        assert len(api_key.scopes) == 2
        assert api_key.expires_in_days == 90
    
    def test_pagination_params_schema(self):
        """Test PaginationParams schema validation."""
        # Default values
        pagination = PaginationParams()
        assert pagination.limit == 20
        assert pagination.offset == 0
        
        # Custom values
        pagination = PaginationParams(limit=50, offset=100)
        assert pagination.limit == 50
        assert pagination.offset == 100
        
        # Invalid values
        with pytest.raises(ValidationError):
            PaginationParams(limit=-1)  # Negative limit
        
        with pytest.raises(ValidationError):
            PaginationParams(offset=-1)  # Negative offset


class TestDependencyInjection:
    """Test dependency injection functions."""
    
    def test_dependency_functions_exist(self):
        """Test that dependency functions exist and are callable."""
        # Test that the functions exist
        assert callable(get_current_user)
        assert callable(get_current_active_user)
        
        # These are FastAPI dependency functions, so we just test they exist
        # Full testing would require FastAPI test client with proper setup


class TestLoggingUtilities:
    """Test logging setup and utilities."""
    
    def test_setup_logging(self):
        """Test logging setup function."""
        logger = setup_logging()
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')


class TestMiddlewareComponents:
    """Test middleware components."""
    
    def test_logging_middleware_import(self):
        """Test that logging middleware can be imported."""
        from app.middleware.logging import LoggingMiddleware
        assert LoggingMiddleware is not None
    
    def test_rate_limit_middleware_import(self):
        """Test that rate limit middleware can be imported."""
        from app.middleware.rate_limit import RateLimitMiddleware
        assert RateLimitMiddleware is not None


class TestUtilityFunctions:
    """Test utility functions and helpers."""
    
    def test_openapi_utilities_import(self):
        """Test that OpenAPI utilities can be imported."""
        from app.utils.openapi import custom_openapi
        assert custom_openapi is not None
    
    @patch('app.utils.openapi.get_settings')
    def test_custom_openapi_function(self, mock_get_settings):
        """Test custom OpenAPI function."""
        from app.utils.openapi import custom_openapi
        from app.main import app
        
        mock_settings = MagicMock()
        mock_settings.project_name = "AIdeator"
        mock_settings.version = "1.0.0"
        mock_get_settings.return_value = mock_settings
        
        openapi_func = custom_openapi(app)
        assert callable(openapi_func)


class TestModelClasses:
    """Test model class definitions and relationships."""
    
    def test_user_model(self):
        """Test User model creation and properties."""
        user = User(
            id="user_123",
            email="test@example.com",
            full_name="Test User",
            company="Test Company",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert user.id == "user_123"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
    
    def test_api_key_model(self):
        """Test APIKey model creation and properties."""
        api_key = APIKey(
            id="key_123",
            user_id="user_123",
            key_hash="hashed_key",
            name="Test API Key",
            description="Test description",
            scopes=["runs:create", "runs:read"],
            is_active=True,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
        
        assert api_key.id == "key_123"
        assert api_key.user_id == "user_123"
        assert len(api_key.scopes) == 2
        assert api_key.is_active is True
    
    def test_run_model(self):
        """Test Run model creation and properties."""
        from app.models.run import Run
        
        run = Run(
            id="run_123",
            user_id="user_123",
            github_url="https://github.com/test/repo",
            prompt="Test prompt",
            variations=3,
            status="pending",
            created_at=datetime.utcnow(),
            results={},
            error_message=None
        )
        
        assert run.id == "run_123"
        assert run.user_id == "user_123"
        assert run.variations == 3
        assert run.status == "pending"
    
    def test_session_model(self):
        """Test Session model creation and properties."""
        from app.models.session import Session
        
        session = Session(
            id="session_123",
            user_id="user_123",
            title="Test Session",
            description="Test description",
            is_active=True,
            is_archived=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            models_used=["gpt-4", "claude-3-sonnet"],
            total_turns=0,
            total_cost=0.0
        )
        
        assert session.id == "session_123"
        assert session.title == "Test Session"
        assert session.is_active is True
        assert len(session.models_used) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])