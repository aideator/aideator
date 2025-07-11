from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> Callable[[], dict[str, Any]]:
    """Create custom OpenAPI schema."""

    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            servers=app.servers,
        )

        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}

        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for authentication",
            }
        }

        # Add global security requirement
        openapi_schema["security"] = [{"ApiKeyAuth": []}]

        # Add tags with descriptions
        openapi_schema["tags"] = [
            {
                "name": "Runs",
                "description": "Agent run management endpoints",
            },
            {
                "name": "Streaming",
                "description": "Server-Sent Events for real-time agent output",
            },
            {
                "name": "System",
                "description": "System health and monitoring",
            },
            {
                "name": "Auth",
                "description": "Authentication endpoints",
            },
        ]

        # Add example responses
        if "responses" not in openapi_schema["components"]:
            openapi_schema["components"]["responses"] = {}

        openapi_schema["components"]["responses"] = {
            "ValidationError": {
                "description": "Validation error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                    }
                },
            },
            "UnauthorizedError": {
                "description": "API key is missing or invalid",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                },
            },
            "RateLimitError": {
                "description": "Rate limit exceeded",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                },
            },
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return openapi
