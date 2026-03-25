import pytest
from unittest.mock import AsyncMock
from starlette.requests import Request
from starlette.responses import Response
from fast_api.middleware.sunset_headers import SunsetHeadersMiddleware


class TestSunsetHeadersMiddleware:

    @pytest.mark.asyncio
    async def test_api_version_header_always_present(self):
        app = AsyncMock()
        middleware = SunsetHeadersMiddleware(app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "query_string": b"",
            "headers": [],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(req):
            return Response(status_code=200)

        response = await middleware.dispatch(Request(scope), call_next)
        assert response.headers.get("API-Version") == "v1"

    @pytest.mark.asyncio
    async def test_deprecated_endpoint_gets_sunset_header(self):
        deprecated = {
            "/api/v0/sims": {
                "sunset": "2025-06-01T00:00:00Z",
                "deprecated_since": "2024-12-01T00:00:00Z",
                "replacement": "/api/v1/recycled-sims",
            }
        }
        app = AsyncMock()
        middleware = SunsetHeadersMiddleware(app, deprecated_endpoints=deprecated)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v0/sims",
            "query_string": b"",
            "headers": [],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(req):
            return Response(status_code=200)

        response = await middleware.dispatch(Request(scope), call_next)
        assert response.headers.get("Sunset") == "2025-06-01T00:00:00Z"
        assert response.headers.get("Deprecation") == "2024-12-01T00:00:00Z"
        assert "/api/v1/recycled-sims" in response.headers.get("Link", "")

    @pytest.mark.asyncio
    async def test_non_deprecated_endpoint_no_sunset(self):
        deprecated = {
            "/api/v0/sims": {"sunset": "2025-06-01T00:00:00Z"},
        }
        app = AsyncMock()
        middleware = SunsetHeadersMiddleware(app, deprecated_endpoints=deprecated)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/recycled-sims",
            "query_string": b"",
            "headers": [],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(req):
            return Response(status_code=200)

        response = await middleware.dispatch(Request(scope), call_next)
        assert "Sunset" not in response.headers
        assert response.headers.get("API-Version") == "v1"

    @pytest.mark.asyncio
    async def test_empty_deprecated_list(self):
        app = AsyncMock()
        middleware = SunsetHeadersMiddleware(app, deprecated_endpoints={})
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test",
            "query_string": b"",
            "headers": [],
            "server": ("localhost", 8000),
            "root_path": "",
        }

        async def call_next(req):
            return Response(status_code=200)

        response = await middleware.dispatch(Request(scope), call_next)
        assert response.headers.get("API-Version") == "v1"
        assert "Sunset" not in response.headers
