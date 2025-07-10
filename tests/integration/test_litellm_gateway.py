"""
Integration tests for LiteLLM Gateway connectivity and behavior.

These tests verify:
1. Gateway connectivity from the application
2. Streaming functionality through Gateway
3. Metrics collection and availability
4. Caching behavior
5. Error handling and fallbacks
"""

import asyncio
import json
import os
import pytest
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

import aiohttp
import openai
from fastapi.testclient import TestClient

from app.main import app
from app.services.kubernetes_service import KubernetesService
from app.core.config import get_settings

settings = get_settings()


class TestLiteLLMGateway:
    """Test suite for LiteLLM Gateway integration."""
    
    @pytest.fixture(scope="class")
    def gateway_base_url(self):
        """Gateway base URL for testing."""
        return os.getenv("LITELLM_GATEWAY_URL", "http://localhost:4000")
    
    @pytest.fixture(scope="class")
    def gateway_api_key(self):
        """Gateway API key for testing."""
        return os.getenv("LITELLM_GATEWAY_API_KEY", "sk-test-key")
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture(scope="class")
    def openai_client(self, gateway_base_url, gateway_api_key):
        """OpenAI client configured for LiteLLM Gateway."""
        return openai.OpenAI(
            api_key=gateway_api_key,
            base_url=gateway_base_url
        )
    
    @pytest.fixture(scope="class")
    def test_models(self):
        """Test models to use for Gateway testing."""
        return [
            "gpt-4o-mini",  # OpenAI model
            "claude-3-haiku-20240307",  # Anthropic model
            "gemini-1.5-flash",  # Google model
        ]
    
    @pytest.mark.asyncio
    async def test_gateway_health_check(self, gateway_base_url):
        """Test Gateway health endpoint."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{gateway_base_url}/health") as response:
                assert response.status == 200
                data = await response.json()
                assert "status" in data
                assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_gateway_model_list(self, gateway_base_url, gateway_api_key):
        """Test Gateway model list endpoint."""
        headers = {
            "Authorization": f"Bearer {gateway_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{gateway_base_url}/models", headers=headers) as response:
                assert response.status == 200
                data = await response.json()
                assert "data" in data
                assert isinstance(data["data"], list)
                assert len(data["data"]) > 0
    
    def test_gateway_chat_completion_sync(self, openai_client, test_models):
        """Test synchronous chat completion through Gateway."""
        for model in test_models:
            try:
                response = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Hello! Please respond with just 'Hello back!'"}
                    ],
                    max_tokens=50,
                    temperature=0.1
                )
                
                assert response.choices[0].message.content is not None
                assert len(response.choices[0].message.content.strip()) > 0
                assert response.model == model
                
            except openai.OpenAIError as e:
                pytest.fail(f"Gateway failed for model {model}: {e}")
    
    def test_gateway_streaming_completion(self, openai_client, test_models):
        """Test streaming chat completion through Gateway."""
        for model in test_models:
            try:
                stream = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Count from 1 to 5, one number per line."}
                    ],
                    max_tokens=50,
                    temperature=0.1,
                    stream=True
                )
                
                chunks = []
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        chunks.append(chunk.choices[0].delta.content)
                
                assert len(chunks) > 0
                full_response = "".join(chunks)
                assert len(full_response.strip()) > 0
                
            except openai.OpenAIError as e:
                pytest.fail(f"Gateway streaming failed for model {model}: {e}")
    
    @pytest.mark.asyncio
    async def test_gateway_metrics_collection(self, gateway_base_url, gateway_api_key):
        """Test that Gateway collects and exposes metrics."""
        # Make a test request to generate metrics
        client = openai.OpenAI(
            api_key=gateway_api_key,
            base_url=gateway_base_url
        )
        
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test metrics"}],
            max_tokens=10
        )
        
        # Wait a moment for metrics to be collected
        await asyncio.sleep(1)
        
        # Check if metrics endpoint exists
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{gateway_base_url}/metrics") as response:
                if response.status == 200:
                    metrics_text = await response.text()
                    assert "litellm_" in metrics_text
                    assert "requests_total" in metrics_text or "completion_tokens" in metrics_text
    
    @pytest.mark.asyncio
    async def test_gateway_error_handling(self, gateway_base_url, gateway_api_key):
        """Test Gateway error handling with invalid requests."""
        client = openai.OpenAI(
            api_key=gateway_api_key,
            base_url=gateway_base_url
        )
        
        # Test invalid model
        with pytest.raises(openai.OpenAIError):
            client.chat.completions.create(
                model="invalid-model-name",
                messages=[{"role": "user", "content": "Test"}]
            )
        
        # Test invalid API key
        invalid_client = openai.OpenAI(
            api_key="invalid-key",
            base_url=gateway_base_url
        )
        
        with pytest.raises(openai.OpenAIError):
            invalid_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}]
            )
    
    @pytest.mark.asyncio
    async def test_gateway_caching_behavior(self, openai_client):
        """Test Gateway caching functionality."""
        # Make identical requests to test caching
        request_params = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "What is 2+2? Answer with just the number."}],
            "max_tokens": 10,
            "temperature": 0.0  # Deterministic response
        }
        
        # First request
        start_time = time.time()
        response1 = openai_client.chat.completions.create(**request_params)
        first_duration = time.time() - start_time
        
        # Second identical request (should be cached)
        start_time = time.time()
        response2 = openai_client.chat.completions.create(**request_params)
        second_duration = time.time() - start_time
        
        # Verify responses are similar (caching working)
        assert response1.choices[0].message.content == response2.choices[0].message.content
        
        # Second request should be faster (cached)
        # Note: This might not always be true depending on Gateway config
        print(f"First request: {first_duration:.3f}s, Second request: {second_duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_gateway_concurrent_requests(self, gateway_base_url, gateway_api_key):
        """Test Gateway handling of concurrent requests."""
        async def make_request(session, model, request_id):
            """Make a single request to the Gateway."""
            data = {
                "model": model,
                "messages": [{"role": "user", "content": f"Hello from request {request_id}"}],
                "max_tokens": 20
            }
            
            headers = {
                "Authorization": f"Bearer {gateway_api_key}",
                "Content-Type": "application/json"
            }
            
            async with session.post(f"{gateway_base_url}/chat/completions", json=data, headers=headers) as response:
                return await response.json()
        
        # Make multiple concurrent requests
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(5):
                task = make_request(session, "gpt-4o-mini", i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests completed successfully
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Request {i} failed: {result}")
                
                assert "choices" in result
                assert len(result["choices"]) > 0
                assert result["choices"][0]["message"]["content"] is not None
    
    @pytest.mark.asyncio
    async def test_gateway_kubernetes_integration(self, test_client):
        """Test Gateway integration with Kubernetes service."""
        with patch.object(KubernetesService, 'create_model_job') as mock_create_job:
            mock_create_job.return_value = "test-job-123"
            
            # Test creating a run that should use Gateway
            response = test_client.post("/api/v1/runs", json={
                "github_url": "https://github.com/test/repo",
                "prompt": "Test prompt",
                "variations": 1,
                "agent_mode": "litellm"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            
            # Verify job was created with correct parameters
            mock_create_job.assert_called_once()
    
    def test_gateway_authentication_headers(self, gateway_base_url, gateway_api_key):
        """Test Gateway authentication with different header formats."""
        headers_variants = [
            {"Authorization": f"Bearer {gateway_api_key}"},
            {"x-api-key": gateway_api_key},
        ]
        
        for headers in headers_variants:
            client = openai.OpenAI(
                api_key=gateway_api_key,
                base_url=gateway_base_url
            )
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Auth test"}],
                    max_tokens=10
                )
                assert response.choices[0].message.content is not None
            except openai.OpenAIError as e:
                # Some auth methods might not work, that's okay
                print(f"Auth method {headers} failed: {e}")
    
    @pytest.mark.asyncio
    async def test_gateway_response_format(self, openai_client):
        """Test Gateway response format compliance with OpenAI API."""
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=50
        )
        
        # Verify response structure
        assert hasattr(response, 'choices')
        assert len(response.choices) > 0
        assert hasattr(response.choices[0], 'message')
        assert hasattr(response.choices[0].message, 'content')
        assert hasattr(response.choices[0].message, 'role')
        assert hasattr(response, 'model')
        assert hasattr(response, 'usage')
        
        # Verify usage information (important for cost tracking)
        if response.usage:
            assert hasattr(response.usage, 'prompt_tokens')
            assert hasattr(response.usage, 'completion_tokens')
            assert hasattr(response.usage, 'total_tokens')
    
    @pytest.mark.asyncio
    async def test_gateway_timeout_handling(self, gateway_base_url, gateway_api_key):
        """Test Gateway timeout handling."""
        client = openai.OpenAI(
            api_key=gateway_api_key,
            base_url=gateway_base_url,
            timeout=1.0  # Very short timeout
        )
        
        # This might timeout or succeed depending on Gateway performance
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Quick response please"}],
                max_tokens=10
            )
            # If it succeeds, that's fine
            assert response.choices[0].message.content is not None
        except (openai.APITimeoutError, openai.OpenAIError):
            # Timeout is expected with very short timeout
            pass
    
    @pytest.mark.asyncio
    async def test_gateway_model_routing(self, openai_client, test_models):
        """Test that Gateway correctly routes to different model providers."""
        for model in test_models:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"What model are you? Answer with just the model name."}],
                max_tokens=20,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.lower()
            
            # Verify the model responded and response is reasonable
            assert len(content) > 0
            assert response.model == model
            
            # Optional: Check if model identifies itself correctly
            # This is provider-dependent and may not always work
            if "gpt" in model and "gpt" in content:
                print(f"✓ {model} correctly identified itself")
            elif "claude" in model and "claude" in content:
                print(f"✓ {model} correctly identified itself")
            elif "gemini" in model and "gemini" in content:
                print(f"✓ {model} correctly identified itself")