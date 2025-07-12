"""Tests for DatabaseInitService to improve coverage."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session

from app.models.provider import ModelDefinition
from app.models.provider_key import ProviderAPIKeyDB
from app.models.user import APIKey, User
from app.services.database_init import DatabaseInitService


class TestDatabaseInitServiceCoverage:
    """Test DatabaseInitService methods for coverage."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db_session):
        """Create DatabaseInitService instance."""
        return DatabaseInitService(mock_db_session)

    def test_init(self, mock_db_session):
        """Test service initialization."""
        service = DatabaseInitService(mock_db_session)
        assert service.db == mock_db_session

    @patch("app.services.database_init.get_settings")
    @patch("app.services.database_init.get_password_hash")
    def test_initialize_test_user_new_user(self, mock_hash, mock_settings, service):
        """Test initializing a new test user."""
        # Setup
        settings = MagicMock()
        settings.test_user_email = "dev@aideator.com"
        mock_settings.return_value = settings
        mock_hash.return_value = "hashed_dev_password"

        # Mock no existing user
        service.db.exec.return_value.first.return_value = None

        # Mock add and commit
        service.db.add = MagicMock()
        service.db.commit = MagicMock()
        service.db.refresh = MagicMock()

        # Mock user creation
        def refresh_side_effect(obj):
            obj.id = "dev-user-123"

        service.db.refresh.side_effect = refresh_side_effect

        # Act
        result = service.initialize_test_user()

        # Assert
        assert "user_id" in result
        assert result["email"] == "test@aideator.local"
        assert result["message"] == "Test user created successfully"
        assert "api_key" in result
        service.db.add.assert_called()
        service.db.commit.assert_called()

    @patch("app.services.database_init.get_settings")
    def test_initialize_test_user_existing_user(self, mock_settings, service):
        """Test initializing test user when user already exists."""
        # Setup
        settings = MagicMock()
        settings.test_user_email = "test@aideator.local"
        mock_settings.return_value = settings

        existing_user = User(
            id="existing-admin-123",
            email="test@aideator.local",
            hashed_password="existing_hash",
            is_active=True,
        )

        # Mock the query to return existing user
        mock_exec_result = MagicMock()
        mock_exec_result.first.side_effect = [
            existing_user,
            None,
        ]  # First for user, second for API key
        service.db.exec.return_value = mock_exec_result

        # Act
        result = service.initialize_test_user()

        # Assert
        assert "user_id" in result
        assert result["email"] == "test@aideator.local"
        assert result["message"] == "Created API key for existing test user"
        assert "api_key" in result

    def test_initialize_test_user_with_existing_api_key(self, service):
        """Test initialize_test_user when user and API key already exist."""
        # Setup existing user
        existing_user = User(
            id="existing-user-123",
            email="test@aideator.local",
            hashed_password="existing_hash",
            is_active=True,
        )

        # Setup existing API key
        existing_key = APIKey(
            id="existing-key-123",
            user_id="existing-user-123",
            name="Development Test Key",
        )

        # Mock the queries
        mock_exec_result = MagicMock()
        mock_exec_result.first.side_effect = [existing_user, existing_key]
        service.db.exec.return_value = mock_exec_result

        # Act
        result = service.initialize_test_user()

        # Assert
        assert "user_id" in result
        assert result["email"] == "test@aideator.local"
        assert result["message"] == "Test user already exists"
        assert result["api_key_exists"] is True

    def test_initialize_test_user_exception(self, service):
        """Test exception handling in initialize_test_user."""
        service.db.exec.side_effect = Exception("Database connection failed")
        service.db.rollback = MagicMock()

        with pytest.raises(Exception, match="Database connection failed"):
            service.initialize_test_user()

        # Verify rollback was called
        service.db.rollback.assert_called_once()

    def test_initialize_model_catalog_success(self, service):
        """Test successful model catalog initialization."""
        # Mock no existing models
        service.db.exec.return_value.all.return_value = []
        service.db.add = MagicMock()
        service.db.commit = MagicMock()

        with patch("app.services.database_init.model_catalog") as mock_catalog:
            # Mock catalog models
            mock_models = [
                MagicMock(id="gpt-4-turbo"),
                MagicMock(id="claude-3-opus"),
            ]
            mock_catalog.to_model_definitions.return_value = mock_models

            # The method returns None
            service.initialize_model_catalog()

            # Verify models were added
            assert service.db.add.call_count == 2
            service.db.commit.assert_called()

    def test_initialize_model_catalog_existing_models(self, service):
        """Test model catalog initialization with existing models."""
        # Mock existing model
        existing_model = ModelDefinition(
            model_name="claude-3-haiku",
            provider="anthropic",
            model_type="chat",
            max_tokens=4096,
        )
        service.db.exec.return_value.all.return_value = [existing_model]

        # Mock existing model with proper ID
        existing_model.id = "claude-3-haiku"

        with patch("app.services.database_init.model_catalog") as mock_catalog:
            # Mock catalog to return the same model
            mock_model = MagicMock(id="claude-3-haiku")
            # Set all the attributes that will be updated
            for attr in [
                "display_name",
                "description",
                "context_window",
                "max_output_tokens",
                "input_price_per_1m_tokens",
                "output_price_per_1m_tokens",
                "capabilities",
                "requires_api_key",
                "requires_region",
                "requires_project_id",
                "default_parameters",
                "is_active",
            ]:
                setattr(mock_model, attr, f"test_{attr}")

            mock_catalog.to_model_definitions.return_value = [mock_model]

            # The method returns None
            service.initialize_model_catalog()

            # No models should be added since it already exists
            service.db.add.assert_not_called()
            service.db.commit.assert_called()

    def test_initialize_model_catalog_exception(self, service):
        """Test exception handling in model catalog initialization."""
        service.db.exec.side_effect = Exception("Failed to connect to model catalog")
        service.db.rollback = MagicMock()

        with pytest.raises(Exception, match="Failed to connect to model catalog"):
            service.initialize_model_catalog()

        service.db.rollback.assert_called_once()

    def test_create_provider_key_for_user_exception(self, service):
        """Test exception handling in provider key creation."""
        # Mock settings with OpenAI key
        with patch("app.services.database_init.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="sk-test-123")

            # Mock database query to return no existing key
            service.db.exec.return_value.first.return_value = None

            # Mock encryption service to raise an error
            with patch(
                "app.services.encryption_service.get_encryption_service"
            ) as mock_get_enc:
                mock_enc = MagicMock()
                mock_enc.encrypt_api_key.side_effect = Exception("Encryption failed")
                mock_get_enc.return_value = mock_enc

                # This should not raise - just logs a warning
                service._create_provider_key_for_user("user-123")

    def test_get_model_statistics(self, service):
        """Test getting model statistics."""
        # Mock models for statistics
        mock_total_models = [
            MagicMock(
                provider=MagicMock(value="openai"),
                is_active=True,
                requires_api_key=True,
                input_price_per_1m_tokens=0.01,
            ),
            MagicMock(
                provider=MagicMock(value="openai"),
                is_active=True,
                requires_api_key=True,
                input_price_per_1m_tokens=0.02,
            ),
            MagicMock(
                provider=MagicMock(value="anthropic"),
                is_active=True,
                requires_api_key=True,
                input_price_per_1m_tokens=0.03,
            ),
            MagicMock(
                provider=MagicMock(value="meta"),
                is_active=False,
                requires_api_key=False,
                input_price_per_1m_tokens=None,
            ),
        ]

        # Mock the two queries - first for all models, second for active models
        mock_exec_results = [MagicMock(), MagicMock()]
        mock_exec_results[0].all.return_value = mock_total_models
        mock_exec_results[1].all.return_value = mock_total_models[
            :3
        ]  # Only active models

        service.db.exec.side_effect = mock_exec_results

        result = service.get_model_statistics()

        assert result["total_models"] == 4
        assert result["active_models"] == 3
        assert result["inactive_models"] == 1
        assert "openai" in result["provider_stats"]
        assert result["provider_stats"]["openai"]["count"] == 2
        assert result["provider_stats"]["anthropic"]["count"] == 1

    @patch("app.services.database_init.logger")
    def test_create_provider_key_for_user_no_openai_key(self, mock_logger, service):
        """Test provider key creation when no OpenAI key in settings."""
        with patch("app.services.database_init.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key=None)

            # Should return early without creating key
            service._create_provider_key_for_user("user-123")

            # No database operations should have been called
            service.db.exec.assert_not_called()
            service.db.add.assert_not_called()

    def test_create_provider_key_for_user_existing_key(self, service):
        """Test provider key creation when key already exists."""
        # Mock settings with OpenAI key
        with patch("app.services.database_init.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openai_api_key="sk-test-123")

            # Mock existing provider key
            existing_key = MagicMock()
            service.db.exec.return_value.first.return_value = existing_key

            service._create_provider_key_for_user("user-123")

            # Should not add new key since one exists
            service.db.add.assert_not_called()
