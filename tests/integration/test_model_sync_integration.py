"""
Integration test for model sync functionality.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock
import httpx
from sqlmodel import create_engine, Session, SQLModel

from app.models.model_definition import ModelDefinitionDB, ModelSyncLog
from app.services.model_sync_service import ModelSyncService
from app.core.config import Settings


class TestModelSyncIntegration:
    """Integration tests for model sync."""
    
    @pytest.fixture
    def test_db(self):
        """Create a test database."""
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings."""
        return Settings(
            LITELLM_PROXY_URL="http://localhost:4000",
            LITELLM_PROXY_API_KEY="test-key",
            SECRET_KEY="test-secret-key-32-characters-long",
            DATABASE_URL="sqlite:///:memory:"
        )
    
    @pytest.mark.asyncio
    async def test_full_sync_flow(self, test_db, test_settings):
        """Test the complete sync flow with mocked HTTP responses."""
        
        # Mock LiteLLM proxy responses
        mock_models_response = {
            "data": [
                {"id": "gpt-4", "object": "model"},
                {"id": "claude-3-opus-20240229", "object": "model"}
            ]
        }
        
        mock_model_info_response = {
            "data": [
                {
                    "model_name": "gpt-4",
                    "litellm_params": {"model": "gpt-4"},
                    "model_info": {
                        "litellm_provider": "openai",
                        "max_tokens": 8192,
                        "input_cost_per_token": 0.00003,
                        "output_cost_per_token": 0.00006,
                        "supports_function_calling": True,
                        "supports_vision": False,
                        "supports_streaming": True
                    }
                },
                {
                    "model_name": "claude-3-opus-20240229",
                    "litellm_params": {"model": "claude-3-opus-20240229"},
                    "model_info": {
                        "litellm_provider": "anthropic",
                        "max_tokens": 200000,
                        "input_cost_per_token": 0.000015,
                        "output_cost_per_token": 0.000075,
                        "supports_function_calling": True,
                        "supports_vision": True,
                        "supports_streaming": True
                    }
                }
            ]
        }
        
        # Patch settings and HTTP client
        with patch('app.services.model_sync_service.settings', test_settings), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Setup mock HTTP responses
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            async def mock_get(url, **kwargs):
                response = Mock()
                response.raise_for_status = Mock()
                
                if "/v1/models" in url:
                    response.json = Mock(return_value=mock_models_response)
                elif "/v1/model/info" in url:
                    response.json = Mock(return_value=mock_model_info_response)
                else:
                    response.json = Mock(return_value={})
                
                return response
            
            mock_instance.get = mock_get
            
            # Create service and run sync
            service = ModelSyncService()
            
            with Session(test_db) as session:
                sync_log = await service.sync_models(session)
                
                # Verify sync results
                assert sync_log.status == "success"
                assert sync_log.models_discovered == 2
                assert sync_log.models_added == 2
                assert sync_log.models_updated == 0
                assert sync_log.models_deactivated == 0
                
                # Verify models were added to database
                models = session.query(ModelDefinitionDB).all()
                assert len(models) == 2
                
                # Verify GPT-4 model
                gpt4 = next(m for m in models if m.model_name == "gpt-4")
                assert gpt4.litellm_provider == "openai"
                assert gpt4.display_name == "GPT 4"
                assert gpt4.max_tokens == 8192
                assert gpt4.supports_function_calling is True
                assert gpt4.supports_vision is False
                assert gpt4.category == "advanced"
                assert gpt4.is_recommended is True
                
                # Verify Claude model
                claude = next(m for m in models if m.model_name == "claude-3-opus-20240229")
                assert claude.litellm_provider == "anthropic"
                assert claude.display_name == "Claude 3 Opus 20240229"
                assert claude.max_tokens == 200000
                assert claude.supports_vision is True
                assert "large-context" in claude.tags
    
    @pytest.mark.asyncio
    async def test_sync_with_existing_models(self, test_db, test_settings):
        """Test sync when models already exist in database."""
        
        # Add existing model to database
        with Session(test_db) as session:
            existing_model = ModelDefinitionDB(
                model_name="gpt-4",
                litellm_provider="openai",
                display_name="GPT-4 Old",
                max_tokens=4096,  # Old value
                is_active=True
            )
            session.add(existing_model)
            session.commit()
        
        # Mock response with updated info
        mock_response = {
            "data": [{
                "model_name": "gpt-4",
                "litellm_params": {"model": "gpt-4"},
                "model_info": {
                    "litellm_provider": "openai",
                    "max_tokens": 8192,  # New value
                    "supports_function_calling": True
                }
            }]
        }
        
        with patch('app.services.model_sync_service.settings', test_settings), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            async def mock_get(url, **kwargs):
                response = Mock()
                response.raise_for_status = Mock()
                
                if "/v1/models" in url:
                    response.json = Mock(return_value={"data": [{"id": "gpt-4"}]})
                else:
                    response.json = Mock(return_value=mock_response)
                
                return response
            
            mock_instance.get = mock_get
            
            service = ModelSyncService()
            
            with Session(test_db) as session:
                sync_log = await service.sync_models(session)
                
                # Verify update
                assert sync_log.models_updated == 1
                assert sync_log.models_added == 0
                
                # Verify model was updated
                model = session.query(ModelDefinitionDB).filter_by(model_name="gpt-4").first()
                assert model.max_tokens == 8192  # Updated value
                assert model.display_name == "GPT-4 Old"  # Preserved
    
    @pytest.mark.asyncio
    async def test_sync_error_handling(self, test_db, test_settings):
        """Test error handling during sync."""
        
        with patch('app.services.model_sync_service.settings', test_settings), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Make HTTP call fail
            mock_instance = Mock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = httpx.HTTPError("Connection failed")
            
            service = ModelSyncService()
            
            with Session(test_db) as session:
                sync_log = await service.sync_models(session)
                
                # Verify error was handled
                assert sync_log.status == "failed"
                assert "Connection failed" in sync_log.error_message
                assert sync_log.completed_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])