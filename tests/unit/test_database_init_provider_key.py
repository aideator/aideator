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
    @patch("app.services.encryption_service.get_encryption_service")
    def test_new_user_gets_openai_provider_key(
        self, mock_get_encryption, mock_get_settings, init_service, mock_session
    ):
        """Test that new test user gets OpenAI provider key from settings."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock encryption service
        mock_encryption = Mock()
        mock_encryption.encrypt_api_key.return_value = ("encrypted_key", "sk-...7890")
        mock_get_encryption.return_value = mock_encryption

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

        # Verify that encryption service was called correctly
        mock_encryption.encrypt_api_key.assert_called_once_with("sk-test1234567890")

        # Verify that a provider key was added to the database
        assert mock_session.add.call_count >= 2  # User, API key, and provider key

        # Check that the provider key was created by examining the add calls
        add_calls = mock_session.add.call_args_list
        provider_key_added = any(
            isinstance(call[0][0], ProviderAPIKeyDB) for call in add_calls
        )
        assert provider_key_added

    @patch("app.services.database_init.get_settings")
    @patch("app.services.encryption_service.get_encryption_service")
    def test_existing_user_gets_provider_key_if_missing(
        self, mock_get_encryption, mock_get_settings, init_service, mock_session
    ):
        """Test that existing test user gets provider key if they don't have one."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock encryption service
        mock_encryption = Mock()
        mock_encryption.encrypt_api_key.return_value = ("encrypted_key", "sk-...7890")
        mock_get_encryption.return_value = mock_encryption

        # Mock existing user
        mock_user = Mock(spec=User)
        mock_user.id = "user_test_existing"
        mock_user.email = "test@aideator.local"

        # Mock no existing API key
        mock_exec_results = [
            mock_user,
            None,
            None,
        ]  # user exists, no API key, no provider key
        mock_session.exec.return_value.first.side_effect = mock_exec_results

        # Mock password hashing and secrets
        with patch("app.services.database_init.get_password_hash") as mock_hash:
            with patch("app.services.database_init.secrets") as mock_secrets:
                mock_hash.return_value = "hashed_password"
                mock_secrets.token_urlsafe.return_value = "test123"

                # Call the method
                init_service.initialize_test_user()

        # Verify that encryption service was called
        mock_encryption.encrypt_api_key.assert_called_once_with("sk-test1234567890")

        # Verify that a provider key was added
        add_calls = mock_session.add.call_args_list
        provider_key_added = any(
            isinstance(call[0][0], ProviderAPIKeyDB) for call in add_calls
        )
        assert provider_key_added

    @patch("app.services.database_init.get_settings")
    def test_no_provider_key_created_when_no_openai_key(
        self, mock_get_settings, init_service, mock_session
    ):
        """Test that no provider key is created when OpenAI API key is not available."""
        # Mock settings with no OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = None
        mock_get_settings.return_value = mock_settings

        # Mock that test user doesn't exist
        mock_session.exec.return_value.first.return_value = None

        # Mock password hashing and secrets
        with patch("app.services.database_init.get_password_hash") as mock_hash:
            with patch("app.services.database_init.secrets") as mock_secrets:
                mock_hash.return_value = "hashed_password"
                mock_secrets.token_urlsafe.return_value = "test123"

                # Call the method
                result = init_service.initialize_test_user()

        # Verify user was still created successfully
        assert result["message"] == "Test user created successfully"

        # Verify that no provider key was added (since no OpenAI key available)
        add_calls = mock_session.add.call_args_list
        provider_key_added = any(
            isinstance(call[0][0], ProviderAPIKeyDB) for call in add_calls
        )
        assert not provider_key_added

    @patch("app.services.database_init.get_settings")
    @patch("app.services.encryption_service.get_encryption_service")
    def test_provider_key_creation_failure_doesnt_break_user_creation(
        self, mock_get_encryption, mock_get_settings, init_service, mock_session
    ):
        """Test that provider key creation failure doesn't prevent user creation."""
        # Mock settings with OpenAI API key
        mock_settings = Mock()
        mock_settings.openai_api_key = "sk-test1234567890"
        mock_get_settings.return_value = mock_settings

        # Mock encryption service that raises an exception
        mock_encryption = Mock()
        mock_encryption.encrypt_api_key.side_effect = Exception("Encryption failed")
        mock_get_encryption.return_value = mock_encryption

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
        assert (
            "Failed to create OpenAI provider key"
            in mock_logger.warning.call_args[0][0]
        )

    @patch("app.services.database_init.get_settings")
    def test_existing_provider_key_not_duplicated(
        self, mock_get_settings, init_service, mock_session
    ):
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
        mock_exec_results = [
            mock_user,
            mock_existing_api_key,
            mock_existing_provider_key,
        ]
        mock_session.exec.return_value.first.side_effect = mock_exec_results

        # Call the method
        result = init_service.initialize_test_user()

        # Verify that existing user response was returned
        assert result["message"] == "Test user already exists"
        assert result["api_key_exists"] is True

        # Verify that no new provider key was added (since one already exists)
        add_calls = mock_session.add.call_args_list
        # Since user and API key already exist, no new objects should be added
        assert len(add_calls) == 0
