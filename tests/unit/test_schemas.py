import pytest
from pydantic import ValidationError

from app.schemas.auth import CreateAPIKeyRequest, UserCreate
from app.schemas.runs import AgentConfig, CreateRunRequest


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_user_create_valid(self):
        """Test valid user creation."""
        user = UserCreate(
            email="user@example.com",
            password="SecurePass123",
            full_name="John Doe",
        )
        assert user.email == "user@example.com"
        assert user.password == "SecurePass123"

    def test_user_create_invalid_email(self):
        """Test invalid email validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="invalid-email", password="SecurePass123")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("email",)
        assert "valid email" in errors[0]["msg"].lower()

    def test_user_create_weak_password(self):
        """Test password complexity validation."""
        # No uppercase
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="user@example.com", password="password123")
        assert "uppercase" in str(exc_info.value)

        # No lowercase
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="user@example.com", password="PASSWORD123")
        assert "lowercase" in str(exc_info.value)

        # No digit
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(email="user@example.com", password="SecurePass")
        assert "digit" in str(exc_info.value)

    def test_api_key_request_defaults(self):
        """Test API key request with defaults."""
        request = CreateAPIKeyRequest(name="Test Key")
        assert request.name == "Test Key"
        assert request.scopes == ["runs:create", "runs:read"]
        assert request.expires_in_days is None


class TestRunSchemas:
    """Test run-related schemas."""

    def test_create_run_request_valid(self):
        """Test valid run creation request."""
        request = CreateRunRequest(
            github_url="https://github.com/user/repo",
            prompt="Refactor the main function",
            variations=3,
        )
        assert str(request.github_url) == "https://github.com/user/repo"
        assert request.prompt == "Refactor the main function"
        assert request.variations == 3

    def test_create_run_request_invalid_url(self):
        """Test GitHub URL validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateRunRequest(
                github_url="https://gitlab.com/user/repo",
                prompt="Test prompt",
            )
        assert "allowed hosts" in str(exc_info.value)

    def test_create_run_request_short_prompt(self):
        """Test prompt length validation."""
        with pytest.raises(ValidationError) as exc_info:
            CreateRunRequest(
                github_url="https://github.com/user/repo",
                prompt="Short",
            )
        
        errors = exc_info.value.errors()
        assert any("at least 10 characters" in str(e) for e in errors)

    def test_create_run_request_variations_bounds(self):
        """Test variations bounds."""
        # Valid
        request = CreateRunRequest(
            github_url="https://github.com/user/repo",
            prompt="Valid prompt for testing",
            variations=5,
        )
        assert request.variations == 5

        # Too many
        with pytest.raises(ValidationError):
            CreateRunRequest(
                github_url="https://github.com/user/repo",
                prompt="Valid prompt for testing",
                variations=11,
            )

    def test_agent_config_defaults(self):
        """Test agent configuration defaults."""
        config = AgentConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.system_prompt is None

    def test_agent_config_temperature_bounds(self):
        """Test temperature validation."""
        # Valid
        config = AgentConfig(temperature=0.5)
        assert config.temperature == 0.5

        # Too high
        with pytest.raises(ValidationError):
            AgentConfig(temperature=1.5)

        # Too low
        with pytest.raises(ValidationError):
            AgentConfig(temperature=-0.1)