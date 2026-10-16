import json

import httpx
import pytest
from mcp import Client

from payping_mcp import http
from payping_mcp.server import mcp

FAKE_TOKEN = "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF-1"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def fresh_http_client():
    """The shared httpx client is bound to one event loop; each test gets a new loop."""
    http.set_transport(None)
    yield
    http.set_transport(None)


@pytest.fixture
def api(monkeypatch):
    """Fake PayPing API: api["GET /v1/report/Balance"] = body, or a callable(request) -> httpx.Response.

    Keys are "METHOD /path" (host and query ignored). A plain value is returned as HTTP 200 JSON.
    Every request is appended to api.calls; api.body(i) returns its JSON body.
    """
    monkeypatch.setenv("PAYPING_TOKEN", FAKE_TOKEN)

    class Routes(dict):
        calls: list[httpx.Request]

        def body(self, i=-1):
            return json.loads(self.calls[i].content)

    routes = Routes()
    routes.calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        routes.calls.append(request)
        target = routes.get(f"{request.method} {request.url.path}")
        if target is None:
            return httpx.Response(404, json={"message": "no Route matched with those values"})
        if callable(target):
            return target(request)
        return httpx.Response(200, json=target)

    http.set_transport(httpx.MockTransport(handler))
    return routes


@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as c:
        call_tool = c.call_tool

        async def parsed(*args, **kwargs):
            result = await call_tool(*args, **kwargs)
            if not result.is_error:
                result.structured_content = json.loads(result.content[0].text)
            return result

        c.call_tool = parsed
        yield c
