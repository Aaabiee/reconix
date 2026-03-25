import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from starlette.responses import Response
from fast_api.middleware.tracing import TracingMiddleware


def make_request(path="/api/v1/test", method="GET", headers=None):
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
        "server": ("localhost", 8000),
        "root_path": "",
    }
    request = Request(scope)
    request._url = MagicMock()
    request._url.path = path
    request._client = MagicMock()
    request._client.host = "127.0.0.1"
    return request


class TestTracingMiddleware:

    @pytest.mark.asyncio
    async def test_excluded_path_skips_tracing(self):
        app = AsyncMock()
        middleware = TracingMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "query_string": b"",
            "headers": [],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(request):
            return Response(status_code=200)

        response = await middleware.dispatch(Request(scope), call_next)
        assert response.status_code == 200
        assert "X-Trace-ID" not in response.headers

    @pytest.mark.asyncio
    async def test_trace_id_added_to_response(self):
        app = AsyncMock()
        middleware = TracingMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "query_string": b"",
            "headers": [(b"host", b"localhost")],
            "server": ("localhost", 8000),
            "root_path": "",
        }
        request = Request(scope)

        async def call_next(req):
            return Response(status_code=200)

        response = await middleware.dispatch(request, call_next)
        assert "X-Trace-ID" in response.headers
        assert "X-Span-ID" in response.headers
        assert len(response.headers["X-Trace-ID"]) == 32

    @pytest.mark.asyncio
    async def test_custom_trace_id_preserved(self):
        app = AsyncMock()
        middleware = TracingMiddleware(app)
        custom_trace = "abc123def456"
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "query_string": b"",
            "headers": [
                (b"host", b"localhost"),
                (b"x-trace-id", custom_trace.encode()),
            ],
            "server": ("localhost", 8000),
            "root_path": "",
        }
        request = Request(scope)

        async def call_next(req):
            return Response(status_code=200)

        response = await middleware.dispatch(request, call_next)
        assert response.headers["X-Trace-ID"] == custom_trace

    @pytest.mark.asyncio
    async def test_metrics_path_excluded(self):
        app = AsyncMock()
        middleware = TracingMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/metrics",
            "query_string": b"",
            "headers": [],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(request):
            return Response(status_code=200)

        response = await middleware.dispatch(Request(scope), call_next)
        assert "X-Trace-ID" not in response.headers

    @pytest.mark.asyncio
    async def test_exception_propagated(self):
        app = AsyncMock()
        middleware = TracingMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/error",
            "query_string": b"",
            "headers": [(b"host", b"localhost")],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(req):
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await middleware.dispatch(Request(scope), call_next)
