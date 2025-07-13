import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()

    def _cleanup_old_requests(self) -> None:
        """Remove old request timestamps."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff = current_time - settings.rate_limit_period
            for client_id in list(self.requests.keys()):
                self.requests[client_id] = [
                    ts for ts in self.requests[client_id] if ts > cutoff
                ]
                if not self.requests[client_id]:
                    del self.requests[client_id]
            self.last_cleanup = current_time

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use API key if present
        api_key = request.headers.get(settings.api_key_header)
        if api_key:
            return f"api_key:{api_key}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        return "unknown"

    def _is_rate_limited(self, client_id: str) -> tuple[bool, int]:
        """Check if client is rate limited."""
        current_time = time.time()
        cutoff = current_time - settings.rate_limit_period

        # Filter recent requests
        recent_requests = [ts for ts in self.requests[client_id] if ts > cutoff]
        self.requests[client_id] = recent_requests

        # Check limit
        if len(recent_requests) >= settings.rate_limit_requests:
            return True, len(recent_requests)

        # Add current request
        self.requests[client_id].append(current_time)
        return False, len(recent_requests) + 1

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Apply rate limiting."""
        # Skip rate limiting for health checks, metrics, and WebSocket endpoints
        if request.url.path in ["/health", "/metrics", "/"] or request.url.path.startswith("/ws/"):
            return await call_next(request)

        # Periodic cleanup
        self._cleanup_old_requests()

        # Get client ID
        client_id = self._get_client_id(request)

        # Check rate limit
        is_limited, request_count = self._is_rate_limited(client_id)

        if is_limited:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                request_count=request_count,
                limit=settings.rate_limit_requests,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": settings.rate_limit_requests,
                    "period": settings.rate_limit_period,
                },
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(time.time() + settings.rate_limit_period)
                    ),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = settings.rate_limit_requests - request_count
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time() + settings.rate_limit_period)
        )

        return response
