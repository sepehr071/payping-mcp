"""Shared async HTTP client for the PayPing API.

The token goes only into the Authorization header. Upstream text goes through `redact` before it
reaches the model, and httpx request logging is silenced.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server.mcpserver.exceptions import ToolError

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

API = "https://api.payping.ir"
OAUTH = "https://oauth.payping.ir"
MAX_CONCURRENCY = 4
RETRY_STATUS = {429, 502, 503}
RETRY_DELAY = 1.0  # seconds

_transport: httpx.AsyncBaseTransport | None = None
_client: httpx.AsyncClient | None = None
_limit: asyncio.Semaphore | None = None


class ApiError(ToolError):
    """A failed PayPing call. `status` is the HTTP status, or None for network and setup errors."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(redact(message))
        self.status = status


def set_transport(transport: httpx.AsyncBaseTransport | None) -> None:
    """Swap the transport (tests use httpx.MockTransport). Drops the current client."""
    global _transport, _client, _limit
    _transport, _client, _limit = transport, None, None


def redact(text: str) -> str:
    token = os.environ.get("PAYPING_TOKEN", "").strip()
    return text.replace(token, "***") if len(token) >= 8 else text


def token() -> str:
    t = os.environ.get("PAYPING_TOKEN", "").strip()
    if not t:
        raise ApiError(
            "PAYPING_TOKEN is not set. Create an API token in the PayPing panel (app.payping.ir, "
            "Connections > Developers > Tokens) with the scopes you need, then set PAYPING_TOKEN."
        )
    return t


def _get_client() -> tuple[httpx.AsyncClient, asyncio.Semaphore]:
    global _client, _limit
    if _client is None:
        # System proxy settings are ignored; PAYPING_MCP_PROXY opts back in.
        _client = httpx.AsyncClient(
            transport=_transport,
            timeout=30,
            trust_env=False,
            proxy=os.environ.get("PAYPING_MCP_PROXY") or None,
            headers={"User-Agent": "payping-mcp"},
        )
        _limit = asyncio.Semaphore(MAX_CONCURRENCY)
    assert _limit is not None
    return _client, _limit


def _error_text(body: Any) -> str:
    """Readable text from PayPing's error bodies: RFC 7807 problem JSON (v1 `errorCode`, v3 `metaData`),
    legacy {"field": "message"} dicts, or the gateway's {"message": ...}."""
    if not isinstance(body, dict):
        return str(body or "")[:300]
    meta = body.get("metaData")
    meta = meta if isinstance(meta, dict) else {}
    code = body.get("errorCode") or meta.get("code")
    parts = [str(body.get("detail") or body.get("title") or body.get("message") or "")]
    parts += [str(e.get("message")) for e in meta.get("errors") or [] if isinstance(e, dict) and e.get("message")]
    if isinstance(body.get("errors"), dict):
        parts += [f"{k}: {v}" for k, v in body["errors"].items()]
    if not any(parts) and "status" not in body:
        parts = [f"{k}: {v}" for k, v in body.items()]
    text = "; ".join(p for p in parts if p)[:500]
    if code:
        text = f"code {code}: {text}"
    if body.get("paypingTraceId"):
        text += f" (PayPing trace id {body['paypingTraceId']}, give it to PayPing support)"
    return text


async def call_obj(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Like `call`, but the body must be a JSON object (an empty or odd reply becomes an ApiError)."""
    out = await call(*args, **kwargs)
    if not isinstance(out, dict):
        raise ApiError("PayPing returned an empty or unexpected response.")
    return out


async def call(
    method: str, path: str, *, params: dict[str, Any] | None = None, json: Any = None, host: str = API
) -> Any:
    """Call PayPing and return the JSON body (None for an empty success). Errors become ApiError."""
    headers = {"Authorization": f"Bearer {token()}"}
    params = {k: v for k, v in (params or {}).items() if v is not None}
    client, limit = _get_client()
    for attempt in range(2 if method == "GET" else 1):  # only idempotent GETs are retried, once
        try:
            async with limit:
                r = await client.request(method, host + path, params=params or None, json=json, headers=headers)
        except httpx.TimeoutException as e:
            raise ApiError("PayPing did not answer in time. Try again in a moment.") from e
        except httpx.RequestError as e:
            raise ApiError(
                f"Could not reach PayPing ({type(e).__name__}). Check the internet connection, or set "
                "PAYPING_MCP_PROXY to route through a proxy."
            ) from e
        if r.status_code not in RETRY_STATUS or attempt:
            break
        await asyncio.sleep(RETRY_DELAY)
    try:
        body = r.json() if r.content else None
    except ValueError:
        if r.is_success:
            raise ApiError(f"PayPing returned a non-JSON response (HTTP {r.status_code}).", r.status_code) from None
        body = r.text
    if r.is_success:
        return body
    if r.status_code == 401:
        raise ApiError(
            "PayPing rejected the token (HTTP 401). Check PAYPING_TOKEN. A new token works only after PayPing "
            "approves it (about 10 minutes later).",
            401,
        )
    hint = " The token may lack the scope this tool needs." if r.status_code == 403 else ""
    raise ApiError(f"PayPing error (HTTP {r.status_code}): {_error_text(body)}.{hint}", r.status_code)
