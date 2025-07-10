#!/usr/bin/env python3
"""
Simple validation script for error handling improvements.
Tests the core logic without external dependencies.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_api_key_validation():
    """Test API key validation logic."""
    print("🔑 Testing API key validation logic...")
    
    # Mock the agent initialization
    from unittest.mock import patch
    
    # Test with no API keys
    with patch.dict(os.environ, {}, clear=True):
        try:
            from agent.main import AIdeatorAgent
            agent = AIdeatorAgent()
            available_keys = agent._check_available_api_keys()
            
            assert available_keys["openai"] is False
            assert available_keys["anthropic"] is False
            assert available_keys["gemini"] is False
            print("✅ API key validation: No keys detected correctly")
        except Exception as e:
            print(f"❌ API key validation failed: {e}")
            return False
    
    # Test with some API keys
    mock_env = {
        "OPENAI_API_KEY": "sk-test123456789",
        "ANTHROPIC_API_KEY": "",
        "GEMINI_API_KEY": "AIzatest123456789",
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        try:
            agent = AIdeatorAgent()
            available_keys = agent._check_available_api_keys()
            
            assert available_keys["openai"] is True
            assert available_keys["anthropic"] is False  # Empty string
            assert available_keys["gemini"] is True
            print("✅ API key validation: Partial keys detected correctly")
        except Exception as e:
            print(f"❌ Partial API key validation failed: {e}")
            return False
    
    return True

def test_model_provider_detection():
    """Test model provider detection."""
    print("🤖 Testing model provider detection...")
    
    try:
        from agent.main import AIdeatorAgent
        agent = AIdeatorAgent()
        
        test_cases = [
            ("gpt-4", "openai"),
            ("claude-3-sonnet", "anthropic"),
            ("gemini-1.5-pro", "gemini"),
            ("mistral-large", "mistral"),
            ("command-r", "cohere"),
            ("unknown-model", "openai"),  # Default
        ]
        
        for model, expected_provider in test_cases:
            actual_provider = agent._get_model_provider(model)
            assert actual_provider == expected_provider, f"Expected {expected_provider}, got {actual_provider} for {model}"
        
        print("✅ Model provider detection: All test cases passed")
        return True
    except Exception as e:
        print(f"❌ Model provider detection failed: {e}")
        return False

def test_error_message_generation():
    """Test error message generation."""
    print("💬 Testing error message generation...")
    
    try:
        from agent.main import AIdeatorAgent
        agent = AIdeatorAgent()
        agent.available_api_keys = {"openai": False, "anthropic": False, "gemini": False}
        
        is_valid, error_msg = agent._validate_model_credentials("claude-3-sonnet")
        
        assert is_valid is False
        assert "Missing API Key for Anthropic" in error_msg
        assert "claude-3-sonnet" in error_msg
        assert "kubectl create secret" in error_msg
        assert "https://console.anthropic.com/" in error_msg
        
        print("✅ Error message generation: Contains all required elements")
        return True
    except Exception as e:
        print(f"❌ Error message generation failed: {e}")
        return False

def test_model_catalog_validation():
    """Test model catalog validation."""
    print("📚 Testing model catalog validation...")
    
    try:
        from app.services.model_catalog import model_catalog
        
        # Test with no API keys
        available_keys = {"openai": False, "anthropic": False}
        
        is_valid, error_msg = model_catalog.validate_model_access("gpt-4", available_keys)
        assert is_valid is False
        assert "API key" in error_msg
        
        # Test with available key
        available_keys = {"openai": True, "anthropic": False}
        
        is_valid, error_msg = model_catalog.validate_model_access("gpt-4", available_keys)
        assert is_valid is True
        assert error_msg == ""
        
        print("✅ Model catalog validation: Working correctly")
        return True
    except Exception as e:
        print(f"❌ Model catalog validation failed: {e}")
        return False

def test_kubernetes_template():
    """Test Kubernetes template has optional secrets."""
    print("☸️  Testing Kubernetes template...")
    
    try:
        template_path = project_root / "k8s" / "jobs" / "agent-job-template.yaml"
        
        with open(template_path, "r") as f:
            template_content = f.read()
        
        # Check that secrets are marked as optional
        assert "optional: true" in template_content
        
        # Count occurrences - should have at least 8 optional secrets
        optional_count = template_content.count("optional: true")
        assert optional_count >= 8, f"Expected at least 8 optional secrets, found {optional_count}"
        
        # Verify specific secrets are present
        assert "openai-secret" in template_content
        assert "anthropic-secret" in template_content
        assert "gemini-secret" in template_content
        assert "mistral-secret" in template_content
        
        print(f"✅ Kubernetes template: {optional_count} optional secrets configured correctly")
        return True
    except Exception as e:
        print(f"❌ Kubernetes template validation failed: {e}")
        return False

def test_available_models_suggestion():
    """Test available models suggestion generation."""
    print("💡 Testing available models suggestion...")
    
    try:
        from agent.main import AIdeatorAgent
        agent = AIdeatorAgent()
        
        # Test with some available keys
        agent.available_api_keys = {
            "openai": True,
            "anthropic": False,
            "gemini": True,
            "mistral": False,
        }
        
        suggestion = agent._get_available_models_suggestion()
        
        assert "Available models with configured API keys:" in suggestion
        assert "OpenAI: gpt-4o, gpt-4o-mini" in suggestion
        assert "Google: gemini-1.5-pro" in suggestion
        assert "Anthropic" not in suggestion  # Should not be included
        
        # Test with no available keys
        agent.available_api_keys = {
            "openai": False,
            "anthropic": False,
            "gemini": False,
            "mistral": False,
        }
        
        suggestion = agent._get_available_models_suggestion()
        assert "No API keys are currently configured" in suggestion
        
        print("✅ Available models suggestion: Generated correctly")
        return True
    except Exception as e:
        print(f"❌ Available models suggestion failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🧪 Starting Error Handling Validation Tests")
    print("=" * 50)
    
    tests = [
        test_api_key_validation,
        test_model_provider_detection,
        test_error_message_generation,
        test_model_catalog_validation,
        test_kubernetes_template,
        test_available_models_suggestion,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All error handling validation tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)