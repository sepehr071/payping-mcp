import json
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.anyio


async def call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    assert not result.is_error, result.content[0].text
    return result.structured_content


async def error(client, name, args=None):
    result = await client.call_tool(name, args or {})
    assert result.is_error
    return result.content[0].text


async def test_profile_uses_oauth_host_and_drops_claim_urls(client, api):
    api["GET /connect/userinfo"] = {
        "username": "shop",
        "firstname": "Ali",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name": "shop",
    }
    assert await call(client, "payping_get_profile") == {"username": "shop", "firstname": "Ali"}
    assert api.calls[0].url.host == "oauth.payping.ir"


async def test_balance_is_toman(client, api):
    api["GET /v1/report/Balance"] = {"result": 125000}
    assert await call(client, "payping_get_balance") == {"balance_toman": 125000}


async def test_sales_summary_body(client, api):
    api["POST /v1/report/DashboardSummery"] = {"totalAmount": 900, "transactionCount": 3, "daily": None}
    out = await call(client, "payping_get_sales_summary", {"from_date": "2026-09-01", "to_date": "2026-09-30"})
    assert api.body() == {"clientId": [], "fromDate": "2026-09-01", "terminalId": 0, "toDate": "2026-09-30"}
    assert out == {"totalAmount": 900, "transactionCount": 3}


async def test_sales_summary_defaults_to_last_30_days(client, api):
    api["POST /v1/report/DashboardSummery"] = {"totalAmount": 0}
    await call(client, "payping_get_sales_summary")
    today = datetime.now(timezone.utc).date()
    assert api.body()["toDate"] == today.isoformat()
    assert api.body()["fromDate"] == (today - timedelta(days=30)).isoformat()


async def test_list_transactions_filters_and_total(client, api):
    api["POST /v1/report/TransactionReport"] = [{"code": "p1", "amount": 5000, "isPaid": True}]
    api["POST /v1/report/TransactionReportCount"] = {"result": 41}
    out = await call(
        client,
        "payping_list_transactions",
        {"from_date": "2026-09-01", "to_date": "2026-09-30", "kind": "received", "offset": 20, "limit": 10},
    )
    assert out == {"total": 41, "transactions": [{"code": "p1", "amount": 5000, "isPaid": True}]}
    bodies = {c.url.path: c for c in api.calls}
    listed = json.loads(bodies["/v1/report/TransactionReport"].content)
    counted = json.loads(bodies["/v1/report/TransactionReportCount"].content)
    assert listed == {
        "offset": 20,
        "limit": 10,
        "fromDate": "2026-09-01T00:00:00Z",
        "toDate": "2026-09-30T23:59:59Z",
        "transactionType": 6,
    }
    assert counted == {k: v for k, v in listed.items() if k not in ("offset", "limit")}


@pytest.mark.parametrize("limit", [0, 51])
async def test_limit_outside_1_to_50_is_rejected(client, api, limit):
    assert "limit" in await error(client, "payping_list_transactions", {"limit": limit})
    assert not api.calls


async def test_get_payment_quotes_code_and_names_status(client, api):
    api["GET /v1/report/a/b"] = {"amount": 1000, "paymentStatus": 5}
    out = await call(client, "payping_get_payment", {"code": "a/b"})
    assert out["status_text"] == "returned from bank, waiting for merchant verify"
    assert api.calls[0].url.raw_path == b"/v1/report/a%2Fb"


@pytest.mark.parametrize("code", [".", "..", "..."])
async def test_dot_codes_cannot_climb_the_path(client, api, code):
    assert "Invalid code" in await error(client, "payping_get_payment", {"code": code})
    assert not api.calls


async def test_list_withdrawals_and_total(client, api):
    api["POST /v1/report/WithdrawTransactions"] = [{"code": "w1", "amount": 70000, "isRepaid": True}]
    api["POST /v1/report/WithdrawTransactionsCount"] = {"result": 1}
    out = await call(client, "payping_list_withdrawals", {"limit": 5})
    assert out == {"total": 1, "withdrawals": [{"code": "w1", "amount": 70000, "isRepaid": True}]}
    bodies = {c.url.path: json.loads(c.content) for c in api.calls}
    assert bodies["/v1/report/WithdrawTransactions"] == {"offset": 0, "limit": 5}
    assert bodies["/v1/report/WithdrawTransactionsCount"] == {}


async def test_get_withdrawal(client, api):
    api["GET /v1/withdraw/w1"] = {"amount": 70000, "isRepaid": False}
    assert await call(client, "payping_get_withdrawal", {"code": "w1"}) == {"amount": 70000, "isRepaid": False}
