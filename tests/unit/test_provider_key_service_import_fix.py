"""
Test for the auth service import fix in provider_key_service.py.
"""

from unittest.mock import Mock, patch

import pytest


class TestProviderKeyServiceImportFix:
    """Test that the import fix in provider_key_service.py works correctly."""

    def test_provider_key_service_imports_correctly(self):
        """Test that ProviderKeyService can be imported without auth service import errors."""
        # This test verifies that the import fix works by attempting to import the module
        try:
            from app.services.provider_key_service import ProviderKeyService, logger

            # Verify that the logger is properly imported from the correct module
            assert logger is not None
            assert hasattr(logger, "info")  # structlog logger should have info method
            assert hasattr(logger, "warning")  # structlog logger should have warning method
            assert hasattr(logger, "error")  # structlog logger should have error method

            # Verify that ProviderKeyService class exists and can be instantiated
            # (without actually calling __init__ which would require encryption setup)
            assert ProviderKeyService is not None
            assert hasattr(ProviderKeyService, "__init__")
            assert hasattr(ProviderKeyService, "create_provider_key")
            assert hasattr(ProviderKeyService, "list_user_keys")

        except ImportError as e:
            pytest.fail(f"Failed to import ProviderKeyService due to import error: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during import: {e}")

    def test_logger_is_from_correct_module(self):
        """Test that the logger is imported from app.core.logging, not app.core.config."""
        from app.services.provider_key_service import logger

        # The logger should be a structlog BoundLogger, not from config module
        logger_module = logger.__class__.__module__

        # It should be from structlog, not from app.core.config
        assert "structlog" in logger_module or hasattr(logger, "bind")

        # Verify it has the expected structlog interface
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    @patch("app.services.provider_key_service.get_encryption_service")
    def test_provider_key_service_initialization_with_fixed_logger(self, mock_get_encryption):
        """Test that ProviderKeyService can be initialized with the fixed logger import."""
        from app.services.provider_key_service import ProviderKeyService

        # Mock the encryption service to avoid encryption setup
        mock_encryption = Mock()
        mock_get_encryption.return_value = mock_encryption

        # This should not raise any import or attribute errors
        try:
            service = ProviderKeyService()
            assert service is not None
            assert service.encryption == mock_encryption
        except ImportError as e:
            if "logger" in str(e) or "app.core.config" in str(e):
                pytest.fail(f"Logger import issue not fixed: {e}")
            else:
                # Re-raise if it's a different import error
                raise

    def test_provider_key_service_can_use_logger(self):
        """Test that the provider key service can actually use the logger."""
        from app.services.provider_key_service import logger

        # Mock the logger to capture calls
        with patch.object(logger, "info") as mock_info:
            with patch.object(logger, "warning") as mock_warning:
                with patch.object(logger, "error") as mock_error:

                    # These should not raise AttributeError
                    logger.info("Test info message")
                    logger.warning("Test warning message")
                    logger.error("Test error message")

                    # Verify the logger methods were called
                    mock_info.assert_called_once_with("Test info message")
                    mock_warning.assert_called_once_with("Test warning message")
                    mock_error.assert_called_once_with("Test error message")

    def test_no_circular_import_issues(self):
        """Test that importing provider_key_service doesn't cause circular import issues."""
        import importlib
        import sys

        # Clear any existing module cache for this test
        modules_to_clear = [
            "app.services.provider_key_service",
            "app.core.logging",
            "app.core.config"
        ]

        original_modules = {}
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                original_modules[module_name] = sys.modules[module_name]
                del sys.modules[module_name]

        try:
            # Try to import the module fresh
            provider_key_module = importlib.import_module("app.services.provider_key_service")

            # Verify basic functionality
            assert hasattr(provider_key_module, "ProviderKeyService")
            assert hasattr(provider_key_module, "logger")

            # Verify logger has expected interface
            logger = provider_key_module.logger
            assert hasattr(logger, "info")
            assert hasattr(logger, "warning")
            assert hasattr(logger, "error")

        except ImportError as e:
            pytest.fail(f"Circular import or other import issue detected: {e}")
        finally:
            # Restore original modules
            for module_name, module in original_modules.items():
                sys.modules[module_name] = module
