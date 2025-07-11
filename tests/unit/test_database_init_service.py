"""
Test database initialization service.
"""

from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from app.models.provider import ProviderType
from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import APIKey, User
from app.services.database_init import DatabaseInitService


class TestDatabaseInitService:
    """Test cases for database initialization service."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.exec = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.refresh = Mock()
        return session

    @pytest.fixture
    def db_init_service(self, mock_session):
        """Create DatabaseInitService instance."""
        return DatabaseInitService(mock_session)

    def test_initialize_test_user_new_user(self, db_init_service, mock_session):
        """Test initializing test user when user doesn't exist."""
        # Mock no existing user
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with (
            patch("app.services.database_init.get_password_hash") as mock_hash,
            patch("app.services.database_init.secrets.token_urlsafe") as mock_token,
        ):
            mock_hash.return_value = "hashed_password"
            mock_token.return_value = "test_token"

            result = db_init_service.initialize_test_user()

            # Verify user was created
            assert mock_session.add.call_count >= 1
            assert mock_session.commit.called
            assert result["email"] == "test@aideator.local"
            assert "api_key" in result

    def test_initialize_test_user_existing_user_with_key(
        self, db_init_service, mock_session
    ):
        """Test initializing test user when user and key already exist."""
        # Mock existing user
        existing_user = User(
            id="user_123",
            email="test@aideator.local",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True,
        )
        existing_key = APIKey(
            id="key_123",
            user_id="user_123",
            name="Development Test Key",
            key_hash="hashed_key",
            is_active=True,
        )

        # Mock session.exec to return different results for different queries
        mock_session.exec.side_effect = [
            Mock(first=Mock(return_value=existing_user)),  # User query
            Mock(first=Mock(return_value=existing_key)),  # API key query
        ]

        with patch.object(
            db_init_service, "_create_provider_key_for_user"
        ) as mock_create_key:
            result = db_init_service.initialize_test_user()

            assert result["user_id"] == "user_123"
            assert result["email"] == "test@aideator.local"
            assert result["api_key_exists"] is True
            assert result["message"] == "Test user already exists"
            mock_create_key.assert_called_once_with("user_123")

    def test_initialize_test_user_existing_user_without_key(
        self, db_init_service, mock_session
    ):
        """Test initializing test user when user exists but no API key."""
        # Mock existing user
        existing_user = User(
            id="user_123",
            email="test@aideator.local",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True,
        )

        # Mock session.exec to return user but no API key
        mock_session.exec.side_effect = [
            Mock(first=Mock(return_value=existing_user)),  # User query
            Mock(first=Mock(return_value=None)),  # API key query
        ]

        with (
            patch("app.services.database_init.get_password_hash") as mock_hash,
            patch("app.services.database_init.secrets.token_urlsafe") as mock_token,
            patch.object(
                db_init_service, "_create_provider_key_for_user"
            ) as mock_create_key,
        ):
            mock_hash.return_value = "hashed_key"
            mock_token.return_value = "test_token"

            result = db_init_service.initialize_test_user()

            # Verify API key was created
            assert mock_session.add.call_count >= 1
            assert mock_session.commit.called
            assert result["user_id"] == "user_123"
            assert "api_key" in result
            mock_create_key.assert_called_once_with("user_123")

    def test_create_provider_key_for_user(self, db_init_service, mock_session):
        """Test creating provider key for user."""
        # Mock no existing provider key
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        with patch("app.services.database_init.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "sk-test-key"

            with patch(
                "app.services.database_init.ProviderKeyService"
            ) as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                mock_service.create_provider_key = Mock()

                # Call the method
                db_init_service._create_provider_key_for_user("user_123")

                # Verify service was called
                mock_service.create_provider_key.assert_called_once()

    def test_create_provider_key_for_user_existing_key(
        self, db_init_service, mock_session
    ):
        """Test creating provider key when key already exists."""
        # Mock existing provider key
        existing_key = ProviderAPIKeyDB(
            id="key_123",
            user_id="user_123",
            provider="openai",
            encrypted_key="encrypted_key",
            key_hint="sk-...test",
            is_active=True,
        )
        mock_result = Mock()
        mock_result.first.return_value = existing_key
        mock_session.exec.return_value = mock_result

        with patch(
            "app.services.database_init.ProviderKeyService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.create_provider_key = Mock()

            # Call the method
            db_init_service._create_provider_key_for_user("user_123")

            # Verify service was NOT called since key exists
            mock_service.create_provider_key.assert_not_called()

    def test_initialize_model_catalog(self, db_init_service, mock_session):
        """Test initializing model catalog."""
        # Mock no existing models
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        with patch("app.services.database_init.model_catalog") as mock_catalog:
            mock_catalog.get_available_models.return_value = [
                {
                    "model_name": "gpt-4",
                    "provider": "openai",
                    "model_type": "chat",
                    "supports_streaming": True,
                    "max_tokens": 4096,
                    "input_cost_per_token": 0.03,
                    "output_cost_per_token": 0.06,
                }
            ]

            db_init_service.initialize_model_catalog()

            # The method should run without errors and commit changes
            assert mock_session.commit.called

    def test_initialize_model_catalog_existing_models(
        self, db_init_service, mock_session
    ):
        """Test initializing model catalog when models already exist."""
        # Mock existing models
        mock_result = Mock()
        mock_result.all.return_value = [Mock(), Mock()]  # 2 existing models
        mock_session.exec.return_value = mock_result

        # Mock model_catalog to return same models
        with patch("app.services.database_init.model_catalog") as mock_catalog:
            mock_catalog.get_available_models.return_value = []

            db_init_service.initialize_model_catalog()

            # Should still commit (even if no new models)
            assert mock_session.commit.called

    def test_initialize_model_catalog_error_handling(
        self, db_init_service, mock_session
    ):
        """Test error handling in initialize_model_catalog."""
        # Mock exception during catalog initialization
        mock_session.exec.side_effect = Exception("Database error")

        with patch("app.services.database_init.model_catalog") as mock_catalog:
            mock_catalog.get_available_models.return_value = []

            with pytest.raises(Exception, match="Database error"):
                db_init_service.initialize_model_catalog()

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    def test_get_model_statistics(self, db_init_service, mock_session):
        """Test getting model statistics."""
        # Mock model queries
        mock_models = [
            Mock(
                provider=ProviderType.OPENAI,
                requires_api_key=True,
                input_price_per_1m_tokens=10.0,
            ),
            Mock(
                provider=ProviderType.OPENAI,
                requires_api_key=False,
                input_price_per_1m_tokens=None,
            ),
            Mock(
                provider=ProviderType.ANTHROPIC,
                requires_api_key=True,
                input_price_per_1m_tokens=15.0,
            ),
        ]

        mock_session.exec.return_value.all.return_value = mock_models

        result = db_init_service.get_model_statistics()

        # Verify statistics were calculated
        assert isinstance(result, dict)
        assert mock_session.exec.call_count >= 2  # total and active queries

    def test_get_model_statistics_empty_catalog(self, db_init_service, mock_session):
        """Test getting model statistics with empty catalog."""
        # Mock empty model queries
        mock_session.exec.return_value.all.return_value = []

        result = db_init_service.get_model_statistics()

        # Verify statistics were calculated
        assert isinstance(result, dict)
        assert result["total_models"] == 0
        assert result["active_models"] == 0
        assert result["provider_stats"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
