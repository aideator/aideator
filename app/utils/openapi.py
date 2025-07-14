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
                "name": "WebSocket",
                "description": "WebSocket endpoints for real-time streaming",
            },
            {
                "name": "System",
                "description": "System health and monitoring",
            },
            {
                "name": "Auth",
                "description": "Authentication endpoints",
            },
            {
                "name": "Sessions",
                "description": "Session management endpoints",
            },
            {
                "name": "Models",
                "description": "AI model configuration endpoints",
            },
            {
                "name": "Credentials",
                "description": "API credential management",
            },
            {
                "name": "Provider Keys",
                "description": "Provider API key management",
            },
            {
                "name": "Preferences",
                "description": "User preference management",
            },
            {
                "name": "Admin",
                "description": "Administrative endpoints",
            },
            {
                "name": "Admin Messaging",
                "description": "Administrative messaging endpoints",
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

        # Add WebSocket paths manually since FastAPI doesn't auto-generate them
        if "paths" not in openapi_schema:
            openapi_schema["paths"] = {}

        # WebSocket endpoints for streaming
        openapi_schema["paths"]["/ws/runs/{run_id}"] = {
            "get": {
                "tags": ["WebSocket"],
                "summary": "WebSocket stream for agent outputs",
                "description": """
                WebSocket endpoint for real-time streaming of agent outputs.

                **Connection:**
                - Connect to: `ws://localhost:8000/api/v1/ws/runs/{run_id}`
                - Protocol: WebSocket
                - Authentication: Optional (query params or headers)

                **Message Types Received:**
                - `connected` - Connection confirmation
                - `llm` - Agent LLM output with content
                - `stdout` - Agent stdout logs
                - `status` - Status updates (running, completed, failed)
                - `control_ack` - Control command acknowledgments
                - `error` - Error messages
                - `pong` - Ping response

                **Message Types Sent:**
                - `cancel` - Cancel the run
                - `ping` - Keepalive ping

                **Message Format:**
                ```json
                {
                  "type": "llm|stdout|status|control_ack|error|pong",
                  "message_id": "stream_id",
                  "data": {
                    "run_id": "run-abc123",
                    "variation_id": "0",
                    "content": "Agent output text...",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "metadata": {}
                  }
                }
                ```
                """,
                "parameters": [
                    {
                        "name": "run_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "The run ID to stream",
                    }
                ],
                "responses": {
                    "101": {"description": "WebSocket connection established"},
                    "404": {"description": "Run not found"},
                    "403": {"description": "Access denied"},
                },
            }
        }

        openapi_schema["paths"]["/ws/runs/{run_id}/debug"] = {
            "get": {
                "tags": ["WebSocket"],
                "summary": "WebSocket debug stream for stdout logs only",
                "description": """
                WebSocket endpoint for debugging - streams only stdout logs for a specific variation.

                **Connection:**
                - Connect to: `ws://localhost:8000/api/v1/ws/runs/{run_id}/debug?variation_id=0`
                - Protocol: WebSocket
                - Filters: Only stdout messages for specified variation

                **Message Format:**
                ```json
                {
                  "type": "stdout",
                  "message_id": "stream_id",
                  "data": {
                    "run_id": "run-abc123",
                    "variation_id": "0",
                    "content": "Debug log output...",
                    "timestamp": "2024-01-01T00:00:00Z"
                  }
                }
                ```
                """,
                "parameters": [
                    {
                        "name": "run_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "The run ID to debug",
                    },
                    {
                        "name": "variation_id",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 0},
                        "description": "Variation ID to filter logs (default: 0)",
                    },
                ],
                "responses": {
                    "101": {"description": "WebSocket connection established"},
                    "404": {"description": "Run not found"},
                },
            }
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return openapi
