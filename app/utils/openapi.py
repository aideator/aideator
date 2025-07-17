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
            "GitHubAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "GitHub Token",
                "description": "GitHub OAuth token for authentication",
            }
        }

        # Add global security requirement
        openapi_schema["security"] = [{"GitHubAuth": []}]

        # Add tags with descriptions
        openapi_schema["tags"] = [
            {
                "name": "Tasks",
                "description": "Task management and monitoring endpoints",
            },
            {
                "name": "System",
                "description": "System health and monitoring",
            },
            {
                "name": "Auth",
                "description": "GitHub OAuth authentication",
            },
        ]

        # Add additional info
        openapi_schema["info"]["x-logo"] = {
            "url": "https://example.com/logo.png",
            "altText": "AIdeator Logo",
        }

        # Add contact info
        openapi_schema["info"]["contact"] = {
            "name": "AIdeator Support",
            "url": "https://github.com/aideator/aideator",
            "email": "support@aideator.com",
        }

        # Add license info
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }

        # Add external docs
        openapi_schema["externalDocs"] = {
            "description": "Find more info here",
            "url": "https://github.com/aideator/aideator",
        }

        # Add examples for common endpoints
        if "paths" in openapi_schema:
            # Add example for task creation
            if "/api/v1/tasks" in openapi_schema["paths"]:
                if "post" in openapi_schema["paths"]["/api/v1/tasks"]:
                    openapi_schema["paths"]["/api/v1/tasks"]["post"]["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "github_url": {"type": "string"},
                                        "prompt": {"type": "string"},
                                        "model_names": {"type": "array", "items": {"type": "string"}},
                                        "agent_mode": {"type": "string"},
                                        "variations": {"type": "integer"},
                                    },
                                    "required": ["github_url", "prompt"],
                                },
                                "examples": {
                                    "basic_task": {
                                        "summary": "Basic coding task",
                                        "value": {
                                            "github_url": "https://github.com/octocat/Hello-World",
                                            "prompt": "Add error handling to the main function",
                                            "model_names": ["gpt-4o-mini"],
                                            "agent_mode": "claude-cli",
                                            "variations": 1,
                                        },
                                    },
                                    "multi_variation": {
                                        "summary": "Multi-variation task",
                                        "value": {
                                            "github_url": "https://github.com/octocat/Hello-World",
                                            "prompt": "Refactor the code for better readability",
                                            "model_names": ["gpt-4o-mini", "claude-3-5-sonnet"],
                                            "agent_mode": "claude-cli",
                                            "variations": 2,
                                        },
                                    },
                                },
                            }
                        }
                    }

        # WebSocket endpoints removed - using HTTP polling for real-time updates
        # The system now uses HTTP polling via /api/v1/tasks/{task_id}/outputs for real-time monitoring

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return openapi