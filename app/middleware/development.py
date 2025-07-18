"""Development middleware for simplified authentication flow."""

import secrets
from datetime import datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Password hashing removed - using GitHub OAuth only
from app.core.config import get_settings
from app.core.database import async_session_maker
from app.models.user import User
from app.utils.dev_user import get_or_create_dev_user


class DevelopmentAuthMiddleware:
    """Middleware that simplifies authentication in development mode."""

    def __init__(self, app):
        self.app = app
        self.settings = get_settings()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Only apply in development modes
        if not (self.settings.simple_dev_mode or self.settings.auto_create_test_user):
            await self.app(scope, receive, send)
            return

        # Skip for health checks and static files
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            await self.app(scope, receive, send)
            return

        # Skip for auth endpoints
        if request.url.path.startswith("/api/v1/auth/"):
            await self.app(scope, receive, send)
            return

        # Auto-create test user if needed
        if self.settings.auto_create_test_user:
            await self._ensure_test_user_exists()

        # Add development user to request state for bypassing auth
        if self.settings.simple_dev_mode:
            async with async_session_maker() as db:
                test_user = await get_or_create_dev_user(db)
                request.state.dev_user = test_user

        await self.app(scope, receive, send)

    async def _ensure_test_user_exists(self):
        """Ensure test user exists in database."""
        async with async_session_maker() as db:
            await get_or_create_dev_user(db)


async def get_dev_user_from_request(request: Request) -> User | None:
    """Get development user from request state if available."""
    return getattr(request.state, "dev_user", None)
