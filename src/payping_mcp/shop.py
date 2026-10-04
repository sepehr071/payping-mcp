"""Customers, products, payment links, coupons and invoices: list/get, and create (confirm first). Amounts are Toman."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from .http import ApiError, call
from .registry import tool
from .reports import Code, Limit, Offset, segment

LINK = "https://ppng.ir"  # PayPing's public short links: /v/{invoice code}, /d/{product code}
Search = Annotated[str | None, Field(max_length=100, description="Text to search for.")]
Archived = Annotated[bool, Field(description="Include archived items.")]
INVOICE_STATUS = {"draft": 0, "awaiting_payment": 1, "paid": 2, "overdue": 3, "cancelled": 4}


def _count(body: Any) -> Any:
    return body.get("count", body.get("result")) if isinstance(body, dict) else body


async def _page(path: str, key: str, params: dict[str, Any]) -> dict[str, Any]:
    """One page of `{path}/List` plus the total from `{path}/ListCount` for the same filter."""
    filters = {k: v for k, v in params.items() if k not in ("offset", "limit")}
    rows, count = await asyncio.gather(
        call("GET", f"{path}/List", params=params), call("GET", f"{path}/ListCount", params=filters)
    )
    return {"total": _count(count), key: rows or []}


def _set(d: dict[str, Any], **fields: Any) -> dict[str, Any]:
    d.update({k: v for k, v in fields.items() if v is not None})
    return d


@tool("PayPing: list customers")
async def payping_list_customers(search: Search = None, offset: Offset = 0, limit: Limit = 20) -> dict[str, Any]:
    """List saved customers (code, name, phone, email, business name) with the total count."""
    return await _page("/v1/customer", "customers", {"offset": offset, "limit": limit, "search": search})


@tool("PayPing: customer detail")
async def payping_get_customer(code: Code) -> dict[str, Any]:
    """One customer by code: name, contact details, address, national id, memo."""
    return await call("GET", f"/v1/customer/{segment(code)}")


@tool("PayPing: list products")
async def payping_list_products(
    search: Search = None, include_archived: Archived = False, offset: Offset = 0, limit: Limit = 20
) -> dict[str, Any]:
    """List products (PayPing "financial items"): code, title, price (Toman), stock, active, has a payment link."""
    params = {"offset": offset, "limit": limit, "search": search, "witharchived": include_archived}
    return await _page("/v1/product", "products", params)


@tool("PayPing: product detail")
async def payping_get_product(code: Code) -> dict[str, Any]:
    """One product by code: title, description, price (Toman), stock, tax, image, category."""
    return await call("GET", f"/v1/product/{segment(code)}")


@tool("PayPing: list coupons")
async def payping_list_coupons(
    search: Search = None, include_archived: Archived = False, offset: Offset = 0, limit: Limit = 20
) -> dict[str, Any]:
    """List discount coupons: name, type (0 = percent, 1 = Toman), amount, code, active, products it applies to."""
    params = {"offset": offset, "limit": limit, "search": search, "witharchived": include_archived}
    return await _page("/v1/coupon", "coupons", params)


@tool("PayPing: coupon detail")
async def payping_get_coupon(code: Code) -> dict[str, Any]:
    """One coupon by code: amount, expiry, max uses, number of buyers and their total spend."""
    return await call("GET", f"/v1/coupon/{segment(code)}")


@tool("PayPing: list invoices")
async def payping_list_invoices(
    status: Annotated[Literal["draft", "awaiting_payment", "paid", "overdue", "cancelled"] | None, Field()] = None,
    customer_code: Annotated[str | None, Field(max_length=100)] = None,
    search: Search = None,
    offset: Offset = 0,
    limit: Limit = 20,
) -> dict[str, Any]:
    """List invoices: code, number, title, status (0 draft, 1 awaiting payment, 2 paid, 3 overdue, 4 cancelled),
    total (Toman), due and paid dates, customer."""
    params = {
        "offset": offset,
        "limit": limit,
        "search": search,
        "status": INVOICE_STATUS[status] if status else None,
        "CustomerCode": customer_code,
    }
    return await _page("/v2/invoice", "invoices", params)


@tool("PayPing: invoice detail")
async def payping_get_invoice(code: Code) -> dict[str, Any]:
    """One invoice by code with its items, customer, status and payment code, plus `url`, the public page where
    the customer pays."""
    out = await call("GET", f"/v2/invoice/{segment(code)}")
    out["url"] = f"{LINK}/v/{segment(code)}"
    return out


@tool("PayPing: create customer", sends=True)
async def payping_create_customer(
    first_name: Annotated[str, Field(min_length=1, max_length=100)],
    last_name: Annotated[str, Field(min_length=1, max_length=100)],
    phone: Annotated[str | None, Field(max_length=20, description="Mobile number, e.g. 09121234567.")] = None,
    email: Annotated[str | None, Field(max_length=200)] = None,
    business_name: Annotated[str | None, Field(max_length=200)] = None,
    is_business: Annotated[bool, Field(description="True for a company (legal person).")] = False,
    national_id: Annotated[str | None, Field(max_length=20, description="National code or economic code.")] = None,
    memo: Annotated[str | None, Field(max_length=1000, description="Private note.")] = None,
) -> dict[str, Any]:
    """Save a new customer in the PayPing account and return it with its `code` (needed for invoices).
    Creates real data: confirm the details with the user before calling."""
    body = _set(
        {"firstName": first_name, "lastName": last_name, "isBusiness": is_business},
        phone=phone,
        email=email,
        businessName=business_name,
        nationalId=national_id,
        memo=memo,
    )
    return await call("POST", "/v1/customer", json=body)


@tool("PayPing: create product", sends=True)
async def payping_create_product(
    title: Annotated[str, Field(min_length=1, max_length=200)],
    amount_toman: Annotated[int | None, Field(ge=1, description="Price in Toman.")] = None,
    amount_set_by_payer: Annotated[bool, Field(description="Payer types the amount (donations); no price.")] = False,
    quantity: Annotated[int | None, Field(ge=1, description="Stock; omit for unlimited.")] = None,
    description: Annotated[str | None, Field(max_length=2000)] = None,
    has_tax: Annotated[bool, Field(description="Add VAT to the price.")] = False,
) -> dict[str, Any]:
    """Create a product (financial item) and return its `code`. Then payping_create_payment_link makes a public
    payment page for it. Creates real data: confirm title and price with the user before calling."""
    if amount_toman is None and not amount_set_by_payer:
        raise ApiError("amount_toman is required unless amount_set_by_payer is true.")
    body = _set(
        {"title": title, "defineAmountByUser": amount_set_by_payer, "unlimited": quantity is None, "haveTax": has_tax},
        amount=None if amount_set_by_payer else amount_toman,
        quantity=quantity,
        description=description,
    )
    return await call("POST", "/v1/product", json=body)


@tool("PayPing: create payment link", sends=True)
async def payping_create_payment_link(
    product_code: Code,
    redirect_url: Annotated[str | None, Field(max_length=500, description="Page to open after payment.")] = None,
    ask_address: Annotated[bool, Field(description="Ask the payer for a postal address.")] = False,
) -> dict[str, Any]:
    """Make a permanent public payment page for a product and return its `url` (https://ppng.ir/d/...), which
    anyone can open and pay. Creates real data: confirm with the user before calling."""
    body = _set({"productCode": product_code, "getAddress": ask_address}, redirectPage=redirect_url)
    out = await call("POST", "/v1/permalink", json=body)
    return {"code": (out or {}).get("code", product_code), "url": f"{LINK}/d/{segment(product_code)}"}


@tool("PayPing: create coupon", sends=True)
async def payping_create_coupon(
    name: Annotated[str, Field(min_length=1, max_length=100)],
    kind: Annotated[Literal["percent", "toman"], Field(description="'percent' off, or a fixed Toman amount off.")],
    amount: Annotated[int, Field(ge=1, description="Percent (1-100) or Toman, per `kind`.")],
    coupon_code: Annotated[str | None, Field(max_length=50, description="Code buyers type; omit to generate.")] = None,
    max_uses: Annotated[int | None, Field(ge=1)] = None,
    expires_on: Annotated[date | None, Field(description="Last valid day (YYYY-MM-DD).")] = None,
    product_codes: Annotated[list[str] | None, Field(description="Limit to these products; omit for all.")] = None,
) -> dict[str, Any]:
    """Create an active discount coupon and return its `code`. Creates real data: confirm with the user first."""
    if kind == "percent" and amount > 100:
        raise ApiError("A percent coupon amount must be 1-100.")
    body = _set(
        {"name": name, "type": 0 if kind == "percent" else 1, "amount": amount, "isActive": True},
        userCouponCode=coupon_code,
        maxRedemption=max_uses,
        redeemDate=f"{expires_on.isoformat()}T23:59:59Z" if expires_on else None,
        activeProductCode=product_codes,
    )
    return await call("POST", "/v1/coupon", json=body)


class InvoiceItem(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount_toman: int = Field(ge=1, description="Unit price in Toman.")
    quantity: int = Field(default=1, ge=1)
    description: str | None = Field(default=None, max_length=1000)
    has_tax: bool = Field(default=False, description="Add VAT to this item.")


@tool("PayPing: create invoice", sends=True)
async def payping_create_invoice(
    customer_code: Annotated[str, Field(min_length=1, max_length=100, description="From payping_create_customer.")],
    items: Annotated[list[InvoiceItem], Field(min_length=1, max_length=100)],
    title: Annotated[str | None, Field(max_length=200)] = None,
    due_date: Annotated[date | None, Field(description="Pay by this day (YYYY-MM-DD).")] = None,
    notes: Annotated[str | None, Field(max_length=2000, description="Shown to the customer.")] = None,
) -> dict[str, Any]:
    """Create an invoice for a saved customer, ready to pay, and return its `code`, `payCode` and `url` (the
    public page where the customer pays). It is not sent; use payping_send_invoice or share the url.
    Creates real data: confirm customer, items and prices with the user before calling."""
    products = [
        _set(
            {"title": i.title, "amount": i.amount_toman, "quantity": i.quantity, "haveTax": i.has_tax},
            description=i.description,
        )
        for i in items
    ]
    body = _set(
        {"customer": {"code": customer_code}, "products": products},
        title=title,
        dueDate=f"{due_date.isoformat()}T23:59:59Z" if due_date else None,
        notes=notes,
    )
    out = await call("POST", "/v2/invoice/FastInvoice", json=body)
    return {**out, "url": f"{LINK}/v/{segment(out['code'])}"}


@tool("PayPing: send invoice", sends=True)
async def payping_send_invoice(code: Code) -> dict[str, Any]:
    """Send an invoice to its customer by SMS/email from PayPing. Messages a real person: confirm with the user
    before calling."""
    return await call("POST", f"/v2/invoice/Send/{segment(code)}") or {"success": True}
