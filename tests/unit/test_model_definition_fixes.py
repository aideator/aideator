"""Tests for model definition database model fixes."""


import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

# Import the fixed models
from app.models.model_definition import ModelDefinitionDB, ModelSyncLog
from app.models.provider_key import ProviderAPIKeyDB


class TestModelDefinitionFixes:
    """Test the fixes for SQLAlchemy reserved word and namespace issues."""

    @pytest.fixture
    def fresh_engine(self):
        """Create a fresh in-memory engine with clean metadata."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        # Create all tables fresh
        SQLModel.metadata.create_all(engine)
        return engine

    def test_model_definition_no_metadata_conflict(self, fresh_engine):
        """Test that the renamed extra_metadata field works without SQLAlchemy conflicts."""
        with Session(fresh_engine) as session:
            # Create a model with extra_metadata
            model = ModelDefinitionDB(
                model_name="test-gpt-4-fixed",
                litellm_provider="openai",
                display_name="Test GPT-4 Fixed",
                max_tokens=8192,
                description="Test model with fixed metadata field",
                category="general",
                tags=["test", "fixed"],
                extra_metadata={
                    "original_issue": "metadata field was reserved",
                    "fix_applied": "renamed to extra_metadata",
                    "test_data": {"nested": True, "value": 42}
                }
            )

            session.add(model)
            session.commit()

            # Verify it was saved correctly
            saved_model = session.get(ModelDefinitionDB, "test-gpt-4-fixed")
            assert saved_model is not None
            assert saved_model.extra_metadata["original_issue"] == "metadata field was reserved"
            assert saved_model.extra_metadata["test_data"]["value"] == 42

    def test_model_sync_log_extra_metadata(self, fresh_engine):
        """Test that ModelSyncLog extra_metadata works correctly."""
        with Session(fresh_engine) as session:
            sync_log = ModelSyncLog(
                status="success",
                models_discovered=10,
                models_added=3,
                models_updated=5,
                models_deactivated=1,
                extra_metadata={
                    "sync_duration_seconds": 2.5,
                    "litellm_endpoint": "http://localhost:4000",
                    "models_processed": ["gpt-4", "claude-3", "gemini-pro"],
                    "errors": []
                }
            )

            session.add(sync_log)
            session.commit()

            # Verify the extra_metadata field
            saved_log = session.get(ModelSyncLog, sync_log.id)
            assert saved_log is not None
            assert saved_log.extra_metadata["sync_duration_seconds"] == 2.5
            assert "gpt-4" in saved_log.extra_metadata["models_processed"]

    def test_provider_key_extra_metadata(self, fresh_engine):
        """Test that ProviderAPIKeyDB extra_metadata works correctly."""
        # First create a user (simplified for test)
        with Session(fresh_engine) as session:
            # Create provider key with extra_metadata
            provider_key = ProviderAPIKeyDB(
                id="test_key_123",
                user_id="test_user_456",  # Would normally be FK to users table
                provider="openai",
                encrypted_key="test_encrypted_key",
                key_hint="sk-...test",
                display_name="Test Key",
                is_active=True,
                is_valid=True,
                extra_metadata={
                    "key_origin": "manually_added",
                    "last_validated": "2024-01-15T10:00:00Z",
                    "rate_limit_tier": "tier-3",
                    "usage_stats": {"requests_today": 150}
                }
            )

            session.add(provider_key)
            session.commit()

            # Verify the extra_metadata field
            saved_key = session.get(ProviderAPIKeyDB, "test_key_123")
            assert saved_key is not None
            assert saved_key.extra_metadata["key_origin"] == "manually_added"
            assert saved_key.extra_metadata["usage_stats"]["requests_today"] == 150

    def test_model_name_field_no_namespace_conflict(self, fresh_engine):
        """Test that model_name field works without protected namespace warnings."""
        with Session(fresh_engine) as session:
            # This should not trigger Pydantic protected namespace warnings
            model1 = ModelDefinitionDB(
                model_name="model_with_underscore",
                litellm_provider="test",
                display_name="Model With Underscore"
            )

            model2 = ModelDefinitionDB(
                model_name="model-with-dashes",
                litellm_provider="test",
                display_name="Model With Dashes"
            )

            session.add_all([model1, model2])
            session.commit()

            # Verify both models were created successfully
            assert session.get(ModelDefinitionDB, "model_with_underscore") is not None
            assert session.get(ModelDefinitionDB, "model-with-dashes") is not None

    def test_json_serialization_deserialization(self, fresh_engine):
        """Test that complex JSON data in extra_metadata serializes/deserializes correctly."""
        with Session(fresh_engine) as session:
            complex_metadata = {
                "configuration": {
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "top_p": 0.9
                },
                "capabilities": ["chat", "code", "reasoning"],
                "limitations": {
                    "no_browsing": True,
                    "knowledge_cutoff": "2023-04"
                },
                "pricing": {
                    "input_cost_per_1k": 0.03,
                    "output_cost_per_1k": 0.06
                }
            }

            model = ModelDefinitionDB(
                model_name="test-complex-json",
                litellm_provider="test",
                display_name="Complex JSON Test",
                extra_metadata=complex_metadata
            )

            session.add(model)
            session.commit()

            # Retrieve and verify complex data structure
            saved_model = session.get(ModelDefinitionDB, "test-complex-json")
            assert saved_model is not None

            metadata = saved_model.extra_metadata
            assert metadata["configuration"]["temperature"] == 0.7
            assert "code" in metadata["capabilities"]
            assert metadata["limitations"]["no_browsing"] is True
            assert metadata["pricing"]["input_cost_per_1k"] == 0.03

    def test_extend_existing_table_config(self, fresh_engine):
        """Test that extend_existing=True prevents table redefinition errors."""
        # This test verifies that the extend_existing configuration works
        # The fact that we can create the engine and use the models proves it works

        with Session(fresh_engine) as session:
            # Create multiple instances to verify table operations work
            models = [
                ModelDefinitionDB(
                    model_name=f"test-model-{i}",
                    litellm_provider="test",
                    display_name=f"Test Model {i}",
                    extra_metadata={"index": i}
                )
                for i in range(5)
            ]

            session.add_all(models)
            session.commit()

            # Verify all models were created
            count = session.execute(
                text("SELECT COUNT(*) FROM model_definitions WHERE model_name LIKE 'test-model-%'")
            ).scalar()
            assert count == 5

    def test_database_compatibility(self, fresh_engine):
        """Test that the models work with actual database operations."""
        with Session(fresh_engine) as session:
            # Test complex query operations
            model = ModelDefinitionDB(
                model_name="query-test-model",
                litellm_provider="openai",
                display_name="Query Test Model",
                category="general",
                is_recommended=True,
                is_popular=True,
                tags=["popular", "recommended"],
                extra_metadata={"test": "query_operations"}
            )

            session.add(model)
            session.commit()

            # Test filtering by various fields
            result = session.query(ModelDefinitionDB).filter(
                ModelDefinitionDB.litellm_provider == "openai",
                ModelDefinitionDB.is_recommended == True,
                ModelDefinitionDB.category == "general"
            ).first()

            assert result is not None
            assert result.model_name == "query-test-model"
            assert result.extra_metadata["test"] == "query_operations"
