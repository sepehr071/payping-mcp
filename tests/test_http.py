import logging

import httpx
import pytest
from conftest import FAKE_TOKEN

from payping_mcp import http

pytestmark = pytest.mark.anyio


async def test_missing_token(api, monkeypatch):
    monkeypatch.delenv("PAYPING_TOKEN")
    with pytest.raises(http.ApiError, match="PAYPING_TOKEN is not set"):
        await http.call("GET", "/v1/report/Balance")
    assert not api.calls


async def test_sends_bearer_token_and_drops_empty_params(api):
    api["GET /v1/customer/List"] = [{"code": "c1"}]
    assert await http.call("GET", "/v1/customer/List", params={"offset": 0, "search": None}) == [{"code": "c1"}]
    req = api.calls[0]
    assert req.headers["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert req.url.host == "api.payping.ir"
    assert dict(req.url.params) == {"offset": "0"}


async def test_oauth_host(api):
    api["GET /connect/userinfo"] = {"username": "u"}
    assert await http.call("GET", "/connect/userinfo", host=http.OAUTH) == {"username": "u"}
    assert api.calls[0].url.host == "oauth.payping.ir"


async def test_rejected_token_is_actionable_and_redacted(api):
    api["GET /v1/report/Balance"] = lambda r: httpx.Response(401, text=f"invalid token {FAKE_TOKEN}")
    with pytest.raises(http.ApiError) as e:
        await http.call("GET", "/v1/report/Balance")
    assert "rejected the token" in str(e.value) and FAKE_TOKEN not in str(e.value)
    assert e.value.status == 401


async def test_problem_json_carries_detail_code_and_trace_id(api):
    problem = {
        "title": "UserNotInitialized",
        "status": 400,
        "detail": "سرویس استرداد",
        "paypingTraceId": "0HNOU26HV8MDO:00000001",
        "errorCode": 4006,
        "errors": {},
    }
    api["GET /v1/refund/Balance"] = lambda r: httpx.Response(400, json=problem)
    with pytest.raises(http.ApiError) as e:
        await http.call("GET", "/v1/refund/Balance")
    text = str(e.value)
    assert problem["detail"] in text and "4006" in text and "0HNOU26HV8MDO:00000001" in text


async def test_v3_metadata_errors(api):
    problem = {
        "title": "ValidationException",
        "status": 400,
        "metaData": {"code": 101, "errors": [{"message": "bad amount"}]},
    }
    api["POST /v1/product"] = lambda r: httpx.Response(400, json=problem)
    with pytest.raises(http.ApiError, match=r"code 101.*bad amount"):
        await http.call("POST", "/v1/product", json={})


async def test_legacy_error_dict(api):
    api["POST /v1/coupon"] = lambda r: httpx.Response(400, json={"amount": "amount is required"})
    with pytest.raises(http.ApiError, match="amount is required"):
        await http.call("POST", "/v1/coupon", json={})


async def test_empty_success_returns_none(api):
    api["POST /v2/invoice/Send/inv1"] = lambda r: httpx.Response(204)
    assert await http.call("POST", "/v2/invoice/Send/inv1") is None


async def test_non_json_success_is_an_error(api):
    api["GET /v1/report/Balance"] = lambda r: httpx.Response(200, text="<html>")
    with pytest.raises(http.ApiError, match="non-JSON"):
        await http.call("GET", "/v1/report/Balance")


def test_httpx_does_not_log_requests():
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() >= logging.WARNING
