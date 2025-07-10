"""
Unit Tests for Models and Schemas

This test suite covers the data models and schema validation
to increase overall test coverage.

Components Covered:
- Pydantic schema validation
- SQLModel model definitions
- Configuration management
- Basic utility functions
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.core.auth import get_password_hash, verify_password

# Core imports
from app.core.config import KubernetesEnvironment, Settings, get_settings
from app.core.logging import setup_logging
from app.models.run import Run
from app.models.session import Preference, Session, Turn

# Model imports
from app.models.user import APIKey, User

# Schema imports
from app.schemas.auth import CreateAPIKeyRequest, UserCreate, UserLogin
from app.schemas.common import PaginationParams
from app.schemas.runs import CreateRunRequest
from app.schemas.session import PreferenceCreate, SessionCreate


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


class TestAuthenticationUtilities:
    """Test authentication utility functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestSchemaValidation:
    """Test Pydantic schema validation."""

    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
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

        # Invalid email
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="SecurePassword123",
                full_name="Test User"
            )

        # Invalid password (no uppercase)
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="lowercase123",
                full_name="Test User"
            )

        # Invalid password (no digit)
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="NoDigitPassword",
                full_name="Test User"
            )

    def test_user_login_schema(self):
        """Test UserLogin schema validation."""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        login = UserLogin(**login_data)
        assert login.email == "test@example.com"
        assert login.password == "password123"

        # Invalid email
        with pytest.raises(ValidationError):
            UserLogin(
                email="not-an-email",
                password="password123"
            )

    def test_run_create_schema(self):
        """Test CreateRunRequest schema validation."""
        # Valid run data
        run_data = {
            "github_url": "https://github.com/test/repo",
            "prompt": "Test prompt for run creation",
            "model_variants": [
                {"model_definition_id": "gpt-4"}
            ]
        }
        run = CreateRunRequest(**run_data)
        assert str(run.github_url) == "https://github.com/test/repo"
        assert len(run.model_variants) == 1

        # Invalid prompt (too short)
        with pytest.raises(ValidationError):
            CreateRunRequest(
                github_url="https://github.com/test/repo",
                prompt="short",  # Less than 10 characters
                model_variants=[{"model_definition_id": "gpt-4"}]
            )

        # Invalid URL
        with pytest.raises(ValidationError):
            CreateRunRequest(
                github_url="not-a-url",
                prompt="Test prompt for run creation",
                model_variants=[{"model_definition_id": "gpt-4"}]
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
        """Test CreateAPIKeyRequest schema validation."""
        api_key_data = {
            "name": "Test API Key",
            "description": "For testing purposes",
            "scopes": ["runs:create", "runs:read"],
            "expires_in_days": 90
        }
        api_key = CreateAPIKeyRequest(**api_key_data)
        assert api_key.name == "Test API Key"
        assert len(api_key.scopes) == 2
        assert api_key.expires_in_days == 90

    def test_pagination_params_schema(self):
        """Test PaginationParams schema validation."""
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

    def test_turn_model(self):
        """Test Turn model creation and properties."""
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
        assert turn.session_id == "session_123"
        assert turn.turn_number == 1
        assert turn.prompt == "Test prompt"
        assert len(turn.models_requested) == 2

    def test_preference_model(self):
        """Test Preference model creation and properties."""
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
        assert preference.confidence_score == 4
        assert len(preference.compared_models) == 2


class TestUtilityFunctions:
    """Test utility functions and helpers."""

    def test_logging_setup(self):
        """Test logging setup function."""
        logger = setup_logging()
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Should be same instance due to lru_cache

    def test_middleware_imports(self):
        """Test that middleware components can be imported."""
        from app.middleware.logging import LoggingMiddleware
        from app.middleware.rate_limit import RateLimitMiddleware
        assert LoggingMiddleware is not None
        assert RateLimitMiddleware is not None

    def test_openapi_utilities_import(self):
        """Test that OpenAPI utilities can be imported."""
        from app.utils.openapi import custom_openapi
        assert custom_openapi is not None


class TestServiceImports:
    """Test that service modules can be imported."""

    def test_service_imports(self):
        """Test that all service modules can be imported."""
        from app.services.agent_orchestrator import AgentOrchestrator
        from app.services.kubernetes_service import KubernetesService
        from app.services.model_catalog import model_catalog
        from app.services.sse_manager import SSEManager

        assert AgentOrchestrator is not None
        assert KubernetesService is not None
        assert SSEManager is not None
        assert model_catalog is not None

    def test_api_router_imports(self):
        """Test that API routers can be imported."""
        from app.api.v1.auth import router as auth_router
        from app.api.v1.credentials import router as credentials_router
        from app.api.v1.health import router as health_router
        from app.api.v1.models import router as models_router
        from app.api.v1.preferences import router as preferences_router
        from app.api.v1.runs import router as runs_router
        from app.api.v1.sessions import router as sessions_router
        from app.api.v1.streams import router as streams_router

        assert auth_router is not None
        assert runs_router is not None
        assert health_router is not None
        assert models_router is not None
        assert sessions_router is not None
        assert preferences_router is not None
        assert credentials_router is not None
        assert streams_router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
