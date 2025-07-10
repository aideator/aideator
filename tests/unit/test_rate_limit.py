"""
Unit Tests for Rate Limit Middleware

This test suite covers the rate limiting middleware
to increase test coverage for app/middleware/rate_limit.py
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.middleware.rate_limit import RateLimitMiddleware


class MockSettings:
    """Mock settings for testing with smaller limits for easier testing."""
    rate_limit_requests = 5  # Use 5 for easier testing
    rate_limit_period = 60  # seconds
    api_key_header = "X-API-Key"


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def middleware(mock_settings):
    """Create middleware instance with mock settings."""
    app = MagicMock()
    with patch("app.middleware.rate_limit.settings", mock_settings):
        return RateLimitMiddleware(app)


@pytest.fixture
def create_request():
    """Factory to create mock requests."""
    def _create_request(
        path: str = "/api/test",
        headers: dict = None,
        client_host: str = "127.0.0.1"
    ):
        request = MagicMock(spec=Request)
        request.url.path = path
        request.headers = Headers(headers or {})
        if client_host:
            request.client = MagicMock()
            request.client.host = client_host
        else:
            request.client = None
        return request
    return _create_request


@pytest.fixture
def call_next():
    """Create mock call_next function."""
    async def _call_next(request):
        response = Response("OK", status_code=200, headers={})
        return response
    return _call_next


@pytest.mark.asyncio
class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class."""

    async def test_middleware_initialization(self, mock_settings):
        """Test middleware initialization."""
        app = MagicMock()
        with patch("app.middleware.rate_limit.settings", mock_settings):
            middleware = RateLimitMiddleware(app)

        assert middleware.requests == {}
        assert middleware.cleanup_interval == 60
        assert middleware.last_cleanup > 0

    async def test_health_check_bypass(self, middleware, create_request, call_next):
        """Test that health check endpoints bypass rate limiting."""
        # Test /health endpoint
        request = create_request(path="/health")
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        assert middleware.requests == {}  # No rate limit tracking

        # Test /metrics endpoint
        request = create_request(path="/metrics")
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        assert middleware.requests == {}

        # Test root endpoint
        request = create_request(path="/")
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        assert middleware.requests == {}

    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_rate_limit_with_api_key(self, middleware, create_request, call_next):
        """Test rate limiting with API key identification."""
        api_key = "test-api-key"
        headers = {"X-API-Key": api_key}

        # Make requests up to the limit
        for i in range(5):
            request = create_request(headers=headers)
            response = await middleware.dispatch(request, call_next)

            assert response.status_code == 200
            assert response.headers["X-RateLimit-Limit"] == "5"
            assert response.headers["X-RateLimit-Remaining"] == str(4 - i)

        # The 6th request should be rate limited
        request = create_request(headers=headers)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        assert isinstance(response, JSONResponse)

    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_rate_limit_with_ip_address(self, middleware, create_request, call_next):
        """Test rate limiting with IP address identification."""
        client_host = "192.168.1.100"

        # Make requests up to the limit
        for i in range(5):
            request = create_request(client_host=client_host)
            response = await middleware.dispatch(request, call_next)

            assert response.status_code == 200
            assert response.headers["X-RateLimit-Remaining"] == str(4 - i)

        # The 6th request should be rate limited
        request = create_request(client_host=client_host)
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429

    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_rate_limit_unknown_client(self, middleware, create_request, call_next):
        """Test rate limiting with unknown client (no IP, no API key)."""
        # Create request with no client
        request = create_request(client_host=None)

        # Should still track rate limits under "unknown"
        for i in range(5):
            request = create_request(client_host=None)
            response = await middleware.dispatch(request, call_next)
            assert response.status_code == 200

        # The 6th request should be rate limited
        request = create_request(client_host=None)
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 429

    async def test_cleanup_old_requests(self, middleware, mock_settings):
        """Test cleanup of old request timestamps."""
        # Add some old and new timestamps
        old_time = time.time() - 120  # 2 minutes ago
        recent_time = time.time() - 30  # 30 seconds ago

        middleware.requests["client1"] = [old_time, old_time, recent_time]
        middleware.requests["client2"] = [old_time, old_time]  # All old
        middleware.requests["client3"] = [recent_time]  # All recent

        # Force cleanup by setting last_cleanup to old time
        middleware.last_cleanup = time.time() - 70

        # Call cleanup
        middleware._cleanup_old_requests()

        # Check results
        assert len(middleware.requests["client1"]) == 1  # Only recent timestamp
        assert "client2" not in middleware.requests  # Completely removed
        assert len(middleware.requests["client3"]) == 1  # Still there

    async def test_no_cleanup_within_interval(self, middleware):
        """Test that cleanup doesn't run within the interval."""
        # Set last_cleanup to recent time
        middleware.last_cleanup = time.time() - 10  # 10 seconds ago

        # Add some data
        middleware.requests["client1"] = [time.time()]

        # Store the data before cleanup attempt
        before_cleanup = dict(middleware.requests)

        # Try to cleanup
        middleware._cleanup_old_requests()

        # Data should remain unchanged (no cleanup performed)
        assert middleware.requests == before_cleanup

    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_rate_limit_headers_in_error_response(self, middleware, create_request, call_next):
        """Test rate limit headers in 429 error response."""
        # Fill up the rate limit
        for _ in range(5):
            request = create_request()
            await middleware.dispatch(request, call_next)

        # Get rate limited response
        request = create_request()
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "X-RateLimit-Reset" in response.headers

        # Check reset time is in the future
        reset_time = int(response.headers["X-RateLimit-Reset"])
        assert reset_time > time.time()

    async def test_get_client_id_priority(self, middleware, create_request):
        """Test that API key takes priority over IP for client identification."""
        # Request with both API key and IP
        request = create_request(
            headers={"X-API-Key": "test-key"},
            client_host="192.168.1.1"
        )

        client_id = middleware._get_client_id(request)
        assert client_id == "api_key:test-key"

        # Request with only IP
        request = create_request(client_host="192.168.1.1")
        client_id = middleware._get_client_id(request)
        assert client_id == "ip:192.168.1.1"

        # Request with neither
        request = create_request(client_host=None)
        client_id = middleware._get_client_id(request)
        assert client_id == "unknown"

    async def test_is_rate_limited_filters_old_requests(self, middleware, mock_settings):
        """Test that _is_rate_limited filters out old requests."""
        client_id = "test_client"
        current_time = time.time()

        # Add mix of old and recent timestamps
        middleware.requests[client_id] = [
            current_time - 120,  # Too old
            current_time - 90,   # Too old
            current_time - 30,   # Recent
            current_time - 20,   # Recent
            current_time - 10,   # Recent
        ]

        # Check rate limit (should only count recent requests)
        is_limited, count = middleware._is_rate_limited(client_id)

        assert not is_limited  # 3 recent + 1 new = 4, under limit of 5
        assert count == 4
        # After the call, old timestamps are removed and new one is added
        assert len(middleware.requests[client_id]) == 4

    @patch("app.middleware.rate_limit.logger")
    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_rate_limit_logging(self, mock_logger, middleware, create_request, call_next):
        """Test that rate limit violations are logged."""
        # Fill up the rate limit
        for _ in range(5):
            request = create_request()
            await middleware.dispatch(request, call_next)

        # Trigger rate limit
        request = create_request()
        await middleware.dispatch(request, call_next)

        # Check logger was called
        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args[0]
        kwargs = mock_logger.warning.call_args[1]

        assert args[0] == "rate_limit_exceeded"
        assert kwargs["client_id"] == "ip:127.0.0.1"
        assert kwargs["request_count"] == 5
        assert kwargs["limit"] == 5

    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_concurrent_requests_handling(self, middleware, create_request, call_next):
        """Test handling of concurrent requests from same client."""
        client_host = "10.0.0.1"

        # Simulate rapid concurrent requests
        tasks = []
        for _ in range(10):
            request = create_request(client_host=client_host)
            tasks.append(middleware.dispatch(request, call_next))

        # Execute all requests
        responses = await asyncio.gather(*tasks)

        # Count successful vs rate limited
        successful = sum(1 for r in responses if r.status_code == 200)
        rate_limited = sum(1 for r in responses if r.status_code == 429)

        assert successful == 5  # Exactly the limit
        assert rate_limited == 5  # The rest are rate limited

    @patch("app.middleware.rate_limit.settings", MockSettings())
    async def test_rate_limit_reset_after_period(self, middleware, create_request, call_next, mock_settings):
        """Test that rate limit resets after the period expires."""
        client_host = "10.0.0.2"

        # Fill up the rate limit
        for _ in range(5):
            request = create_request(client_host=client_host)
            await middleware.dispatch(request, call_next)

        # Should be rate limited now
        request = create_request(client_host=client_host)
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 429

        # Simulate time passing by modifying timestamps
        client_id = f"ip:{client_host}"
        middleware.requests[client_id] = [
            ts - mock_settings.rate_limit_period - 1
            for ts in middleware.requests[client_id]
        ]

        # Should be allowed again
        request = create_request(client_host=client_host)
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
