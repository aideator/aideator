"""
Comprehensive Unit Tests for Backend Coverage

This test suite is designed to maximize code coverage by testing
models, schemas, configurations, and utility functions that can
be tested without complex dependencies.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch
import json
import os

from pydantic import ValidationError

# Schema imports - using actual class names
from app.schemas.auth import UserCreate, UserLogin, CreateAPIKeyRequest
from app.schemas.runs import CreateRunRequest, AgentConfig
from app.schemas.models import ModelVariantCreate
from app.schemas.session import SessionCreate, PreferenceCreate
from app.schemas.common import PaginationParams

# Model imports
from app.models.user import User, APIKey
from app.models.run import Run
from app.models.session import Session, Turn, Preference
from app.models.provider import ProviderType, ModelCapability, ProviderCredential

# Core imports
from app.core.config import Settings, get_settings, KubernetesEnvironment
from app.core.auth import verify_password, get_password_hash
from app.core.logging import setup_logging


class TestAllSchemas:
    """Test all schema validation to increase coverage."""
    
    def test_user_create_schema(self):
        """Test UserCreate schema with all validation paths."""
        # Valid user data
        user_data = {
            "email": "test@example.com",
            "password": "SecurePassword123",
            "full_name": "Test User",
            "company": "Test Company"
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        
        # Test all password validation rules
        with pytest.raises(ValidationError, match="uppercase"):
            UserCreate(email="test@example.com", password="lowercase123")
        
        with pytest.raises(ValidationError, match="lowercase"):
            UserCreate(email="test@example.com", password="UPPERCASE123")
        
        with pytest.raises(ValidationError, match="digit"):
            UserCreate(email="test@example.com", password="NoDigitPassword")
        
        # Test email validation
        with pytest.raises(ValidationError):
            UserCreate(email="invalid-email", password="SecurePassword123")
    
    def test_run_create_schema(self):
        """Test CreateRunRequest schema."""
        # Valid run data with model_variants
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for run creation",
            "model_variants": [
                {"model_definition_id": "gpt-4"},
                {"model_definition_id": "claude-3-sonnet"}
            ]
        }
        run = CreateRunRequest(**run_data)
        assert str(run.github_url) == "https://github.com/test/repo"
        assert len(run.model_variants) == 2
        
        # Test invalid prompt (too short)
        with pytest.raises(ValidationError):
            CreateRunRequest(
                github_url="https://github.com/test/repo",
                prompt="short",  # Less than 10 characters
                model_variants=[{"model_definition_id": "gpt-4"}]
            )
        
        # Test invalid URL
        with pytest.raises(ValidationError):
            CreateRunRequest(
                github_url="not-a-url",
                prompt="Test prompt for run creation",
                model_variants=[{"model_definition_id": "gpt-4"}]
            )
    
    def test_agent_config_schema(self):
        """Test AgentConfig schema."""
        config_data = {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.9
        }
        config = AgentConfig(**config_data)
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
    
    def test_session_create_schema(self):
        """Test SessionCreate schema."""
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
            SessionCreate(title="A" * 201, models_used=["gpt-4"])
    
    def test_preference_create_schema(self):
        """Test PreferenceCreate schema with all validation."""
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
        
        # Test quality score validation - invalid score
        with pytest.raises(ValidationError):
            PreferenceCreate(
                preferred_model="gpt-4",
                preferred_response_id="response_123",
                compared_models=["gpt-4", "claude-3-sonnet"],
                response_quality_scores={"gpt-4": 6, "claude-3-sonnet": 5}
            )
        
        # Test insufficient compared models
        with pytest.raises(ValidationError):
            PreferenceCreate(
                preferred_model="gpt-4",
                preferred_response_id="response_123",
                compared_models=["gpt-4"],
                response_quality_scores={"gpt-4": 5}
            )
    
    def test_api_key_create_schema(self):
        """Test CreateAPIKeyRequest schema."""
        api_key_data = {
            "name": "Test API Key",
            "description": "For testing",
            "scopes": ["runs:create", "runs:read"],
            "expires_in_days": 90
        }
        api_key = CreateAPIKeyRequest(**api_key_data)
        assert api_key.name == "Test API Key"
        assert len(api_key.scopes) == 2
    
    def test_pagination_params_schema(self):
        """Test PaginationParams schema."""
        # Default values
        pagination = PaginationParams()
        assert pagination.page == 1
        assert pagination.per_page == 20
        
        # Custom values
        pagination = PaginationParams(page=2, per_page=50)
        assert pagination.page == 2
        assert pagination.per_page == 50
        
        # Invalid values
        with pytest.raises(ValidationError):
            PaginationParams(page=0)  # Must be >= 1
        
        with pytest.raises(ValidationError):
            PaginationParams(per_page=0)  # Must be >= 1


class TestAllModels:
    """Test all model classes to increase coverage."""
    
    def test_user_model(self):
        """Test User model."""
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
    
    def test_api_key_model(self):
        """Test APIKey model."""
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
        assert len(api_key.scopes) == 2
    
    def test_run_model(self):
        """Test Run model."""
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
        assert run.variations == 3
    
    def test_session_model(self):
        """Test Session model."""
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
    
    def test_turn_model(self):
        """Test Turn model."""
        turn = Turn(
            id="turn_123",
            session_id="session_123",
            user_id="user_123",
            turn_number=1,
            prompt="Test prompt",
            context="Test context",
            model="multi-model",
            models_requested=["gpt-4", "claude-3-sonnet"],
            responses={},
            started_at=datetime.utcnow(),
            status="pending"
        )
        assert turn.id == "turn_123"
        assert turn.turn_number == 1
    
    def test_preference_model(self):
        """Test Preference model."""
        preference = Preference(
            id="pref_123",
            user_id="user_123",
            session_id="session_123",
            turn_id="turn_123",
            preferred_model="claude-3-sonnet",
            preferred_response_id="response_123",
            compared_models=["gpt-4", "claude-3-sonnet"],
            response_quality_scores={"gpt-4": 4, "claude-3-sonnet": 5},
            feedback_text="Claude was more helpful",
            confidence_score=4,
            created_at=datetime.utcnow(),
            preference_type="response"
        )
        assert preference.id == "pref_123"
        assert preference.preferred_model == "claude-3-sonnet"
    
    def test_provider_credential_model(self):
        """Test ProviderCredential model."""
        credential = ProviderCredential(
            id="cred_123",
            user_id="user_123",
            provider=ProviderType.OPENAI,
            name="OpenAI Key",
            description="My OpenAI API key",
            encrypted_api_key="encrypted_key_data",
            is_active=True,
            created_at=datetime.utcnow(),
            last_used_at=None
        )
        assert credential.id == "cred_123"
        assert credential.provider == ProviderType.OPENAI
    
    def test_provider_type_enum(self):
        """Test ProviderType enum."""
        assert ProviderType.OPENAI == "openai"
        assert ProviderType.ANTHROPIC == "anthropic"
        assert ProviderType.GEMINI == "gemini"
        assert ProviderType.AZURE == "azure"
        # Test all major providers are defined
        providers = [p.value for p in ProviderType]
        assert "openai" in providers
        assert "anthropic" in providers
        assert "gemini" in providers
    
    def test_model_capability_enum(self):
        """Test ModelCapability enum."""
        # Test that capabilities exist
        capabilities = [c.value for c in ModelCapability]
        assert len(capabilities) > 0


class TestConfiguration:
    """Test configuration management extensively."""
    
    def test_settings_creation_with_all_fields(self):
        """Test Settings with all possible configurations."""
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            openai_api_key="sk-test-openai-key",
            anthropic_api_key="sk-ant-test-key",
            gemini_api_key="AIza-test-key",
            debug=True,
            host="0.0.0.0",
            port=8000,
            workers=4,
            reload=True,
            log_level="debug",
            database_url="postgresql://user:pass@localhost/db",
            kubernetes_namespace="test-namespace",
            max_variations=10,
            max_prompt_length=5000
        )
        
        assert settings.project_name == "AIdeator"
        assert settings.debug is True
        assert settings.kubernetes_namespace == "test-namespace"
        assert settings.max_variations == 10
    
    def test_settings_validation_all_paths(self):
        """Test all validation paths in Settings."""
        # Test secret key validation
        with pytest.raises(ValueError, match="Secret key must be at least 32"):
            Settings(secret_key="short")
        
        # Test OpenAI key validation
        with pytest.raises(ValueError, match="Invalid OpenAI API key"):
            Settings(
                secret_key="test-secret-key-32-characters-long",
                openai_api_key="invalid-key"
            )
        
        # Test Anthropic key validation
        with pytest.raises(ValueError, match="Invalid Anthropic API key"):
            Settings(
                secret_key="test-secret-key-32-characters-long",
                anthropic_api_key="invalid-key"
            )
        
        # Test Gemini key validation
        with pytest.raises(ValueError, match="Invalid Gemini API key"):
            Settings(
                secret_key="test-secret-key-32-characters-long",
                gemini_api_key="invalid-key"
            )
    
    def test_settings_list_parsing(self):
        """Test list parsing from environment variables."""
        # Test with list input (normal case)
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            allowed_origins=["http://localhost:3000", "https://example.com"]
        )
        assert len(settings.allowed_origins) == 2
        assert "http://localhost:3000" in settings.allowed_origins
        
        # Test with default values
        settings = Settings(
            secret_key="test-secret-key-32-characters-long"
        )
        assert isinstance(settings.allowed_hosts, list)
        assert isinstance(settings.allowed_origins, list)
    
    def test_database_url_variations(self):
        """Test database URL handling for different formats."""
        # Test postgresql+asyncpg URL (unchanged)
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            database_url="postgresql+asyncpg://user:pass@localhost/db"
        )
        assert settings.database_url_async == "postgresql+asyncpg://user:pass@localhost/db"
        
        # Test postgresql URL (converted)
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            database_url="postgresql://user:pass@localhost/db"
        )
        assert "postgresql+asyncpg://" in settings.database_url_async
    
    def test_kubernetes_environment_utilities(self):
        """Test KubernetesEnvironment utilities."""
        # Test agent environment
        env = KubernetesEnvironment.get_agent_env(variation_id=5)
        assert env["PYTHONUNBUFFERED"] == "1"
        assert env["AGENT_VARIATION_ID"] == "5"
        assert env["LOG_LEVEL"] == "INFO"
        
        # Test build args
        with patch('app.core.config.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.kubernetes_workdir = "/custom/workdir"
            mock_get_settings.return_value = mock_settings
            
            build_args = KubernetesEnvironment.get_build_args()
            assert build_args["PYTHON_VERSION"] == "3.11"
            assert build_args["WORKDIR"] == "/custom/workdir"
    
    def test_kubernetes_secrets_generation(self):
        """Test Kubernetes secrets generation."""
        settings = Settings(
            secret_key="test-secret-key-32-characters-long",
            openai_api_key="sk-test-openai-key",
            anthropic_api_key="sk-ant-test-anthropic-key",
            gemini_api_key="AIza-test-gemini-key"
        )
        
        secrets = settings.get_kubernetes_secrets()
        assert secrets["openai-api-key"] == "sk-test-openai-key"
        assert secrets["anthropic-api-key"] == "sk-ant-test-anthropic-key"
        assert secrets["gemini-api-key"] == "AIza-test-gemini-key"


class TestAuthUtilities:
    """Test authentication utilities comprehensively."""
    
    def test_password_hashing_multiple_cases(self):
        """Test password hashing with multiple test cases."""
        test_passwords = [
            "simple123",
            "Complex!Password@123",
            "unicode_password_测试",
            "very_long_password_with_many_characters_123456789"
        ]
        
        for password in test_passwords:
            hashed = get_password_hash(password)
            assert hashed != password
            assert verify_password(password, hashed) is True
            assert verify_password("wrong", hashed) is False
            assert verify_password(password + "wrong", hashed) is False


class TestUtilitiesAndHelpers:
    """Test utility functions and helpers."""
    
    def test_logging_setup(self):
        """Test logging setup."""
        logger = setup_logging()
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
    
    def test_get_settings_caching(self):
        """Test settings caching behavior."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Same instance due to lru_cache
        
        # Test that settings have expected properties
        assert hasattr(settings1, 'project_name')
        assert hasattr(settings1, 'version')
        assert hasattr(settings1, 'api_v1_prefix')


class TestImportCoverage:
    """Test imports to ensure all modules are importable."""
    
    def test_api_router_imports(self):
        """Test that all API routers can be imported."""
        from app.api.v1.auth import router as auth_router
        from app.api.v1.runs import router as runs_router
        from app.api.v1.health import router as health_router
        from app.api.v1.models import router as models_router
        from app.api.v1.sessions import router as sessions_router
        from app.api.v1.preferences import router as preferences_router
        from app.api.v1.credentials import router as credentials_router
        from app.api.v1.streams import router as streams_router
        
        # Test that routers have expected attributes
        routers = [
            auth_router, runs_router, health_router, models_router,
            sessions_router, preferences_router, credentials_router, streams_router
        ]
        
        for router in routers:
            assert hasattr(router, 'routes')
            assert len(router.routes) > 0
    
    def test_service_imports(self):
        """Test that all service classes can be imported."""
        from app.services.agent_orchestrator import AgentOrchestrator
        from app.services.kubernetes_service import KubernetesService
        from app.services.sse_manager import SSEManager
        from app.services.model_catalog import model_catalog
        
        # Test that classes/instances exist
        assert AgentOrchestrator is not None
        assert KubernetesService is not None
        assert SSEManager is not None
        assert model_catalog is not None
    
    def test_middleware_imports(self):
        """Test that middleware can be imported."""
        from app.middleware.logging import LoggingMiddleware
        from app.middleware.rate_limit import RateLimitMiddleware
        
        assert LoggingMiddleware is not None
        assert RateLimitMiddleware is not None
    
    def test_core_imports(self):
        """Test that core modules can be imported."""
        from app.core.dependencies import get_current_user, get_current_active_user
        from app.core.database import get_session
        from app.utils.openapi import custom_openapi
        
        assert callable(get_current_user)
        assert callable(get_current_active_user)
        assert callable(get_session)
        assert callable(custom_openapi)


class TestMainApplicationSetup:
    """Test main application setup and configuration."""
    
    def test_app_import(self):
        """Test that the main app can be imported."""
        from app.main import app, create_application
        
        assert app is not None
        assert callable(create_application)
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0
    
    def test_app_has_required_routes(self):
        """Test that app has expected routes."""
        from app.main import app
        
        # Get all route paths
        route_paths = []
        for route in app.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
            elif hasattr(route, 'routes'):  # Router
                for subroute in route.routes:
                    if hasattr(subroute, 'path'):
                        route_paths.append(subroute.path)
        
        # Check for key routes
        assert "/" in route_paths
        assert "/health" in route_paths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])