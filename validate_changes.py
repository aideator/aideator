#!/usr/bin/env python3
"""
Quick validation script for model sync changes.
"""

import sys
import importlib.util

def validate_imports():
    """Test that all imports work correctly."""
    try:
        # Test model definition imports
        from app.models.model_definition import ModelDefinitionDB, ModelSyncLog
        print("✅ Model definition imports work")
        
        # Test service imports
        from app.services.model_sync_service import ModelSyncService
        print("✅ Model sync service imports work")
        
        # Test task imports
        from app.tasks.model_sync_task import ModelSyncTask
        print("✅ Model sync task imports work")
        
        # Test admin endpoints
        from app.api.v1.endpoints.admin import router
        print("✅ Admin endpoints import work")
        
        # Test dependencies
        from app.api.v1.deps import require_admin
        print("✅ Dependencies import work")
        
        # Test updated config
        from app.core.config import Settings
        settings = Settings(
            SECRET_KEY="test-secret-key-32-characters-long",
            DATABASE_URL="sqlite:///:memory:",
            LITELLM_PROXY_URL="http://localhost:4000"
        )
        print("✅ Config with new fields works")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def validate_models():
    """Test model definitions."""
    try:
        from app.models.model_definition import ModelDefinitionDB
        from datetime import datetime
        
        # Test creating a model instance
        model = ModelDefinitionDB(
            model_name="test-model",
            litellm_provider="openai",
            display_name="Test Model",
            max_tokens=4096,
            supports_function_calling=True,
            supports_vision=False,
            supports_streaming=True,
            description="Test description",
            category="general",
            tags=["test"],
            is_recommended=False,
            is_popular=False,
            requires_api_key=True,
            is_active=True
        )
        
        print("✅ Model instance creation works")
        return True
        
    except Exception as e:
        print(f"❌ Model validation error: {e}")
        return False

def validate_services():
    """Test service instantiation."""
    try:
        from app.services.model_sync_service import ModelSyncService
        from app.tasks.model_sync_task import ModelSyncTask
        
        # Test service creation
        service = ModelSyncService()
        print("✅ Model sync service instantiation works")
        
        # Test task creation
        task = ModelSyncTask(sync_interval_minutes=60)
        print("✅ Model sync task instantiation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Service validation error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Validating model sync implementation...")
    
    success = True
    success &= validate_imports()
    success &= validate_models()
    success &= validate_services()
    
    if success:
        print("\n🎉 All validations passed! Implementation looks good.")
        sys.exit(0)
    else:
        print("\n❌ Some validations failed. Check the errors above.")
        sys.exit(1)