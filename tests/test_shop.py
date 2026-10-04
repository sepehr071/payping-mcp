import httpx
import pytest

pytestmark = pytest.mark.anyio


async def call(client, name, args=None):
    result = await client.call_tool(name, args or {})
    assert not result.is_error, result.content[0].text
    return result.structured_content


def query(api, path):
    return dict(next(c for c in api.calls if c.url.path == path).url.params)


@pytest.mark.parametrize(
    ("tool", "path", "key"),
    [
        ("payping_list_customers", "/v1/customer", "customers"),
        ("payping_list_products", "/v1/product", "products"),
        ("payping_list_coupons", "/v1/coupon", "coupons"),
        ("payping_list_invoices", "/v2/invoice", "invoices"),
    ],
)
async def test_lists_page_search_and_total(client, api, tool, path, key):
    api[f"GET {path}/List"] = [{"code": "x1"}]
    api[f"GET {path}/ListCount"] = {"count": 7}
    out = await call(client, tool, {"search": "علی", "offset": 10, "limit": 5})
    assert out == {"total": 7, key: [{"code": "x1"}]}
    assert query(api, f"{path}/List").items() >= {"offset": "10", "limit": "5", "search": "علی"}.items()
    assert query(api, f"{path}/ListCount")["search"] == "علی"
    assert "offset" not in query(api, f"{path}/ListCount")


async def test_count_as_bare_number(client, api):
    api["GET /v1/coupon/List"] = []
    api["GET /v1/coupon/ListCount"] = 0
    assert (await call(client, "payping_list_coupons"))["total"] == 0


async def test_list_invoices_status_filter(client, api):
    api["GET /v2/invoice/List"] = []
    api["GET /v2/invoice/ListCount"] = {"count": 0}
    await call(client, "payping_list_invoices", {"status": "awaiting_payment", "customer_code": "c1"})
    assert query(api, "/v2/invoice/List")["status"] == "1"
    assert query(api, "/v2/invoice/List")["CustomerCode"] == "c1"
    assert query(api, "/v2/invoice/ListCount")["status"] == "1"


@pytest.mark.parametrize(
    ("tool", "path"),
    [
        ("payping_get_customer", "/v1/customer/c 1"),
        ("payping_get_product", "/v1/product/c 1"),
        ("payping_get_coupon", "/v1/coupon/c 1"),
    ],
)
async def test_get_by_code(client, api, tool, path):
    api[f"GET {path}"] = {"code": "c 1"}
    assert await call(client, tool, {"code": "c 1"}) == {"code": "c 1"}
    assert b"c%201" in api.calls[0].url.raw_path


async def test_get_invoice_adds_public_link(client, api):
    api["GET /v2/invoice/inv1"] = {"code": "inv1", "status": 1}
    out = await call(client, "payping_get_invoice", {"code": "inv1"})
    assert out["url"] == "https://ppng.ir/v/inv1"


async def test_create_customer_body(client, api):
    api["POST /v1/customer"] = {"code": "c9", "firstName": "Ali", "lastName": "Rezaei"}
    out = await call(
        client, "payping_create_customer", {"first_name": "Ali", "last_name": "Rezaei", "phone": "09120000000"}
    )
    assert out["code"] == "c9"
    assert api.body() == {"firstName": "Ali", "lastName": "Rezaei", "phone": "09120000000", "isBusiness": False}


async def test_create_product_fixed_price_unlimited(client, api):
    api["POST /v1/product"] = {"code": "p9"}
    out = await call(client, "payping_create_product", {"title": "Course", "amount_toman": 250000})
    assert out == {"code": "p9"}
    assert api.body() == {
        "title": "Course",
        "amount": 250000,
        "defineAmountByUser": False,
        "unlimited": True,
        "haveTax": False,
    }


async def test_create_product_needs_price_unless_payer_sets_it(client, api):
    result = await client.call_tool("payping_create_product", {"title": "Donation"})
    assert result.is_error and "amount_toman" in result.content[0].text
    assert not api.calls
    api["POST /v1/product"] = {"code": "p8"}
    await call(client, "payping_create_product", {"title": "Donation", "amount_set_by_payer": True, "quantity": 3})
    assert api.body() == {
        "title": "Donation",
        "defineAmountByUser": True,
        "unlimited": False,
        "quantity": 3,
        "haveTax": False,
    }


async def test_create_payment_link_returns_url(client, api):
    api["POST /v1/permalink"] = {"code": "p9"}
    out = await call(
        client, "payping_create_payment_link", {"product_code": "p9", "redirect_url": "https://x.ir/thanks"}
    )
    assert out == {"code": "p9", "url": "https://ppng.ir/d/p9"}
    assert api.body() == {"productCode": "p9", "redirectPage": "https://x.ir/thanks", "getAddress": False}


async def test_create_coupon_percent(client, api):
    api["POST /v1/coupon"] = {"code": "k1"}
    out = await call(
        client,
        "payping_create_coupon",
        {"name": "Yalda", "kind": "percent", "amount": 20, "coupon_code": "YALDA20", "max_uses": 100},
    )
    assert out == {"code": "k1"}
    assert api.body() == {
        "name": "Yalda",
        "type": 0,
        "amount": 20,
        "isActive": True,
        "userCouponCode": "YALDA20",
        "maxRedemption": 100,
    }


async def test_create_coupon_percent_over_100_rejected(client, api):
    result = await client.call_tool("payping_create_coupon", {"name": "x", "kind": "percent", "amount": 120})
    assert result.is_error and "100" in result.content[0].text
    assert not api.calls


async def test_create_invoice_fast_invoice_body_and_link(client, api):
    api["POST /v2/invoice/FastInvoice"] = {"code": "inv7", "payCode": "pc7", "customerCode": "c9"}
    out = await call(
        client,
        "payping_create_invoice",
        {
            "customer_code": "c9",
            "title": "Order 12",
            "items": [{"title": "Shirt", "amount_toman": 300000, "quantity": 2}],
        },
    )
    assert out == {"code": "inv7", "payCode": "pc7", "customerCode": "c9", "url": "https://ppng.ir/v/inv7"}
    assert api.body() == {
        "customer": {"code": "c9"},
        "title": "Order 12",
        "products": [{"title": "Shirt", "amount": 300000, "quantity": 2, "haveTax": False}],
    }


async def test_create_invoice_needs_items(client, api):
    result = await client.call_tool("payping_create_invoice", {"customer_code": "c9", "items": []})
    assert result.is_error and "items" in result.content[0].text
    assert not api.calls


async def test_send_invoice(client, api):
    api["POST /v2/invoice/Send/inv7"] = lambda r: httpx.Response(200, json={"success": True, "message": "ok"})
    assert await call(client, "payping_send_invoice", {"code": "inv7"}) == {"success": True, "message": "ok"}
