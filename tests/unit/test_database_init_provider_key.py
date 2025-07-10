"""
Test for automatic OpenAI provider key creation during test user initialization.
"""

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import APIKey, User
from app.services.database_init import DatabaseInitService


class TestDatabaseInitProviderKey:
    """Test cases for automatic provider key creation during test user initialization."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def init_service(self, mock_session):
        """Create DatabaseInitService with mocked session."""
        return DatabaseInitService(mock_session)

    @patch("app.services.database_init.get_settings")
    @patch("app.services.database_init.ProviderKeyService")
    def test_new_user_gets_openai_provider_key(self, mock_provider_service_class, mock_get_settings, init_service, mock_session):
        """Test that new test user gets OpenAI provider key from settings."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock provider key service
        mock_provider_service = Mock()
        mock_created_key = Mock()
        mock_created_key.key_hint = "sk-...7890"
        mock_provider_service.create_provider_key.return_value = mock_created_key
        mock_provider_service_class.return_value = mock_provider_service

        # Mock that test user doesn't exist
        mock_session.exec.return_value.first.return_value = None

        # Mock password hashing
        with patch("app.services.database_init.get_password_hash") as mock_hash:
            mock_hash.return_value = "hashed_password"

            # Mock secrets for ID generation
            with patch("app.services.database_init.secrets") as mock_secrets:
                mock_secrets.token_urlsafe.return_value = "test123"

                # Call the method
                result = init_service.initialize_test_user()

        # Verify that user was created
        assert result["message"] == "Test user created successfully"
        assert result["email"] == "test@aideator.local"
        assert "api_key" in result

        # Verify that provider key service was called correctly
        mock_provider_service.create_provider_key.assert_called_once()
        call_args = mock_provider_service.create_provider_key.call_args

        assert call_args[1]["user_id"] == result["user_id"]
        assert call_args[1]["provider_key_data"]["provider"] == "openai"
        assert call_args[1]["provider_key_data"]["api_key"] == "sk-test1234567890"
        assert call_args[1]["provider_key_data"]["name"] == "Development OpenAI Key"
        assert "Auto-created from .env" in call_args[1]["provider_key_data"]["description"]

    @patch("app.services.database_init.get_settings")
    def test_existing_user_gets_provider_key_if_missing(self, mock_get_settings, init_service, mock_session):
        """Test that existing test user gets provider key if they don't have one."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock existing user
        mock_user = Mock(spec=User)
        mock_user.id = "user_test_existing"
        mock_user.email = "test@aideator.local"

        # Mock no existing API key
        mock_exec_results = [mock_user, None, None]  # user exists, no API key, no provider key
        mock_session.exec.return_value.first.side_effect = mock_exec_results

        # Mock provider key service
        with patch("app.services.database_init.ProviderKeyService") as mock_provider_service_class:
            mock_provider_service = Mock()
            mock_created_key = Mock()
            mock_created_key.key_hint = "sk-...7890"
            mock_provider_service.create_provider_key.return_value = mock_created_key
            mock_provider_service_class.return_value = mock_provider_service

            # Mock password hashing and secrets
            with patch("app.services.database_init.get_password_hash") as mock_hash:
                with patch("app.services.database_init.secrets") as mock_secrets:
                    mock_hash.return_value = "hashed_password"
                    mock_secrets.token_urlsafe.return_value = "test123"

                    # Call the method
                    result = init_service.initialize_test_user()

        # Verify that provider key was created
        mock_provider_service.create_provider_key.assert_called_once()

    @patch("app.services.database_init.get_settings")
    def test_no_provider_key_created_when_no_openai_key(self, mock_get_settings, init_service, mock_session):
        """Test that no provider key is created when OpenAI API key is not available."""
        # Mock settings with no OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = None
        mock_get_settings.return_value = mock_settings

        # Mock that test user doesn't exist
        mock_session.exec.return_value.first.return_value = None

        # Mock provider key service (should not be called)
        with patch("app.services.database_init.ProviderKeyService") as mock_provider_service_class:
            mock_provider_service = Mock()
            mock_provider_service_class.return_value = mock_provider_service

            # Mock password hashing and secrets
            with patch("app.services.database_init.get_password_hash") as mock_hash:
                with patch("app.services.database_init.secrets") as mock_secrets:
                    mock_hash.return_value = "hashed_password"
                    mock_secrets.token_urlsafe.return_value = "test123"

                    # Call the method
                    result = init_service.initialize_test_user()

        # Verify that provider key service was NOT called
        mock_provider_service.create_provider_key.assert_not_called()

        # Verify user was still created successfully
        assert result["message"] == "Test user created successfully"

    @patch("app.services.database_init.get_settings")
    @patch("app.services.database_init.ProviderKeyService")
    def test_provider_key_creation_failure_doesnt_break_user_creation(self, mock_provider_service_class, mock_get_settings, init_service, mock_session):
        """Test that provider key creation failure doesn't prevent user creation."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock provider key service that raises an exception
        mock_provider_service = Mock()
        mock_provider_service.create_provider_key.side_effect = Exception("Encryption failed")
        mock_provider_service_class.return_value = mock_provider_service

        # Mock that test user doesn't exist
        mock_session.exec.return_value.first.return_value = None

        # Mock password hashing and secrets
        with patch("app.services.database_init.get_password_hash") as mock_hash:
            with patch("app.services.database_init.secrets") as mock_secrets:
                with patch("app.services.database_init.logger") as mock_logger:
                    mock_hash.return_value = "hashed_password"
                    mock_secrets.token_urlsafe.return_value = "test123"

                    # Call the method - should not raise exception
                    result = init_service.initialize_test_user()

        # Verify that user was still created successfully
        assert result["message"] == "Test user created successfully"
        assert result["email"] == "test@aideator.local"

        # Verify that warning was logged
        mock_logger.warning.assert_called_once()
        assert "Failed to create OpenAI provider key" in mock_logger.warning.call_args[0][0]

    @patch("app.services.database_init.get_settings")
    def test_existing_provider_key_not_duplicated(self, mock_get_settings, init_service, mock_session):
        """Test that existing provider key is not duplicated."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock existing user with existing provider key
        mock_user = Mock(spec=User)
        mock_user.id = "user_test_existing"
        mock_user.email = "test@aideator.local"

        mock_existing_api_key = Mock(spec=APIKey)
        mock_existing_provider_key = Mock(spec=ProviderAPIKeyDB)

        # Mock session responses: user exists, API key exists, provider key exists
        mock_exec_results = [mock_user, mock_existing_api_key, mock_existing_provider_key]
        mock_session.exec.return_value.first.side_effect = mock_exec_results

        # Mock provider key service
        with patch("app.services.database_init.ProviderKeyService") as mock_provider_service_class:
            mock_provider_service = Mock()
            mock_provider_service_class.return_value = mock_provider_service

            # Call the method
            result = init_service.initialize_test_user()

        # Verify that provider key was NOT created (already exists)
        mock_provider_service.create_provider_key.assert_not_called()

        # Verify that existing user response was returned
        assert result["message"] == "Test user already exists"
        assert result["api_key_exists"] is True
