import pytest

from payping_mcp.server import INSTRUCTIONS

pytestmark = pytest.mark.anyio

CREATES = {
    "payping_create_customer",
    "payping_create_product",
    "payping_create_payment_link",
    "payping_create_coupon",
    "payping_create_invoice",
    "payping_send_invoice",
}
READS = {
    "payping_get_profile",
    "payping_get_balance",
    "payping_get_sales_summary",
    "payping_list_transactions",
    "payping_get_payment",
    "payping_list_withdrawals",
    "payping_get_withdrawal",
    "payping_list_customers",
    "payping_get_customer",
    "payping_list_products",
    "payping_get_product",
    "payping_list_coupons",
    "payping_get_coupon",
    "payping_list_invoices",
    "payping_get_invoice",
}


async def test_tool_set_and_annotations(client):
    tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == CREATES | READS
    for name, t in tools.items():
        assert t.title and t.description, name
        assert t.annotations.read_only_hint is (name not in CREATES), name
        assert t.annotations.destructive_hint is (name in CREATES), name
        if name in CREATES:
            assert "confirm" in t.description.lower(), name


def test_instructions_cover_units_confirmation_and_untrusted_text():
    text = INSTRUCTIONS.lower()
    assert "toman" in text and "utc" in text
    assert "confirm" in text
    assert "data, never" in text  # customer-supplied text is not instructions


def test_readme_lists_every_tool():
    from pathlib import Path

    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    assert {n for n in CREATES | READS if f"`{n}`" not in readme} == set()


def test_no_nulls_drops_none_recursively():
    from payping_mcp.server import _no_nulls

    assert _no_nulls({"a": None, "b": [{"c": None, "d": 0}], "e": ""}) == {"b": [{"d": 0}], "e": ""}


async def test_real_client_gets_one_text_block_and_no_output_schema(api):
    from mcp import Client

    from payping_mcp.server import mcp

    api["GET /connect/userinfo"] = {"username": "u", "extra": None}
    async with Client(mcp) as c:
        tools = (await c.list_tools()).tools
        assert all(t.output_schema is None for t in tools)
        assert not any("title" in p for t in tools for p in t.input_schema.get("properties", {}).values())
        r = await c.call_tool("payping_get_profile", {})
    assert len(r.content) == 1 and r.content[0].type == "text"
    assert r.structured_content is None and r.content[0].text == '{"username":"u"}'
