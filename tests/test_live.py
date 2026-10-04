"""Calls the real PayPing API with PAYPING_TOKEN. Read-only: pytest -m live"""

import os

import pytest

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("PAYPING_TOKEN"), reason="PAYPING_TOKEN not set"),
]


async def call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    assert not result.is_error, result.content[0].text
    return result.structured_content


async def test_profile(client):
    assert (await call(client, "payping_get_profile"))["username"]


@pytest.mark.parametrize("tool", ["payping_get_balance", "payping_get_sales_summary"])
async def test_dashboard_endpoints(client, tool):
    await call(client, tool)


@pytest.mark.parametrize(
    "tool",
    [
        "payping_list_transactions",
        "payping_list_withdrawals",
        "payping_list_customers",
        "payping_list_products",
        "payping_list_coupons",
        "payping_list_invoices",
    ],
)
async def test_lists(client, tool):
    out = await call(client, tool, {"limit": 2})
    assert isinstance(out["total"], int)
