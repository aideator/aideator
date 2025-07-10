"""
Unit Tests for OpenAPI utilities

This test suite covers the custom OpenAPI schema generation
to increase test coverage for app/utils/openapi.py
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.utils.openapi import custom_openapi


class TestCustomOpenAPI:
    """Test custom OpenAPI schema generation."""
    
    def test_custom_openapi_creates_schema(self):
        """Test that custom_openapi creates a proper schema."""
        # Create a mock FastAPI app
        app = FastAPI(
            title="Test API",
            version="1.0.0",
            description="Test API Description"
        )
        
        # Add a test route
        @app.get("/test")
        def test_route():
            return {"test": "route"}
        
        # Get the custom openapi function
        openapi_func = custom_openapi(app)
        
        # Call it to generate schema
        schema = openapi_func()
        
        # Verify basic schema structure
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
        assert schema["info"]["description"] == "Test API Description"
        
        # Verify security schemes were added
        assert "components" in schema
        assert "securitySchemes" in schema["components"]
        assert "ApiKeyAuth" in schema["components"]["securitySchemes"]
        assert schema["components"]["securitySchemes"]["ApiKeyAuth"]["type"] == "apiKey"
        assert schema["components"]["securitySchemes"]["ApiKeyAuth"]["in"] == "header"
        assert schema["components"]["securitySchemes"]["ApiKeyAuth"]["name"] == "X-API-Key"
        
        # Verify global security requirement
        assert "security" in schema
        assert {"ApiKeyAuth": []} in schema["security"]
        
        # Verify tags were added
        assert "tags" in schema
        tag_names = [tag["name"] for tag in schema["tags"]]
        assert "Runs" in tag_names
        assert "Streaming" in tag_names
        assert "System" in tag_names
        assert "Auth" in tag_names
        
        # Verify responses were added
        assert "responses" in schema["components"]
        assert "ValidationError" in schema["components"]["responses"]
        assert "UnauthorizedError" in schema["components"]["responses"]
        assert "RateLimitError" in schema["components"]["responses"]
    
    def test_custom_openapi_caches_schema(self):
        """Test that schema is cached after first generation."""
        app = FastAPI(title="Test API")
        
        # Get the custom openapi function
        openapi_func = custom_openapi(app)
        
        # Call it twice
        schema1 = openapi_func()
        schema2 = openapi_func()
        
        # Should return the same cached schema object
        assert schema1 is schema2
        assert app.openapi_schema is schema1
    
    def test_custom_openapi_returns_existing_schema(self):
        """Test that existing schema is returned if already set."""
        app = FastAPI(title="Test API")
        
        # Set an existing schema
        existing_schema = {"existing": "schema"}
        app.openapi_schema = existing_schema
        
        # Get the custom openapi function
        openapi_func = custom_openapi(app)
        
        # Call it
        schema = openapi_func()
        
        # Should return the existing schema unchanged
        assert schema is existing_schema
        assert schema == {"existing": "schema"}
    
    def test_custom_openapi_with_servers(self):
        """Test schema generation with custom servers."""
        app = FastAPI(
            title="Test API",
            servers=[
                {"url": "https://api.example.com", "description": "Production"},
                {"url": "http://localhost:8000", "description": "Local"}
            ]
        )
        
        openapi_func = custom_openapi(app)
        schema = openapi_func()
        
        # Verify servers are included
        assert "servers" in schema
        assert len(schema["servers"]) == 2
        assert schema["servers"][0]["url"] == "https://api.example.com"
        assert schema["servers"][1]["url"] == "http://localhost:8000"
    
    def test_custom_openapi_all_response_schemas(self):
        """Test all response schemas have correct structure."""
        app = FastAPI(title="Test API")
        
        openapi_func = custom_openapi(app)
        schema = openapi_func()
        
        responses = schema["components"]["responses"]
        
        # Verify ValidationError response
        assert "ValidationError" in responses
        assert responses["ValidationError"]["description"] == "Validation error"
        assert "application/json" in responses["ValidationError"]["content"]
        assert "$ref" in responses["ValidationError"]["content"]["application/json"]["schema"]
        assert responses["ValidationError"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/HTTPValidationError"
        
        # Verify UnauthorizedError response
        assert "UnauthorizedError" in responses
        assert responses["UnauthorizedError"]["description"] == "API key is missing or invalid"
        assert "application/json" in responses["UnauthorizedError"]["content"]
        assert "$ref" in responses["UnauthorizedError"]["content"]["application/json"]["schema"]
        assert responses["UnauthorizedError"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"
        
        # Verify RateLimitError response
        assert "RateLimitError" in responses
        assert responses["RateLimitError"]["description"] == "Rate limit exceeded"
        assert "application/json" in responses["RateLimitError"]["content"]
        assert "$ref" in responses["RateLimitError"]["content"]["application/json"]["schema"]
        assert responses["RateLimitError"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"
    
    def test_custom_openapi_all_tags(self):
        """Test all tags have correct descriptions."""
        app = FastAPI(title="Test API")
        
        openapi_func = custom_openapi(app)
        schema = openapi_func()
        
        tags = {tag["name"]: tag["description"] for tag in schema["tags"]}
        
        assert tags["Runs"] == "Agent run management endpoints"
        assert tags["Streaming"] == "Server-Sent Events for real-time agent output"
        assert tags["System"] == "System health and monitoring"
        assert tags["Auth"] == "Authentication endpoints"
    
    @patch('app.utils.openapi.get_openapi')
    def test_custom_openapi_calls_get_openapi_correctly(self, mock_get_openapi):
        """Test that get_openapi is called with correct parameters."""
        app = FastAPI(
            title="Test API",
            version="2.0.0",
            description="Test Description",
            servers=[{"url": "http://test.com"}]
        )
        
        # Add routes
        @app.get("/route1")
        def route1():
            pass
        
        @app.post("/route2")
        def route2():
            pass
        
        # Mock the get_openapi return value
        mock_get_openapi.return_value = {
            "info": {},
            "paths": {},
            "components": {}
        }
        
        openapi_func = custom_openapi(app)
        schema = openapi_func()
        
        # Verify get_openapi was called with correct args
        mock_get_openapi.assert_called_once()
        call_args = mock_get_openapi.call_args
        
        assert call_args.kwargs["title"] == "Test API"
        assert call_args.kwargs["version"] == "2.0.0"
        assert call_args.kwargs["description"] == "Test Description"
        assert call_args.kwargs["servers"] == [{"url": "http://test.com"}]
        # Routes should be passed
        assert len(call_args.kwargs["routes"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])