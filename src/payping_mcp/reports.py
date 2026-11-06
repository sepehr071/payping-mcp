"""Account, balance, sales, transaction and withdrawal tools (read-only). Amounts are Toman."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any, Literal
from urllib.parse import quote

from pydantic import Field

from .http import OAUTH, ApiError, call, call_obj
from .registry import tool

Offset = Annotated[int, Field(ge=0)]
Limit = Annotated[int, Field(ge=1, le=50)]
Code = Annotated[str, Field(min_length=1, max_length=100)]
FromDate = Annotated[date | None, Field(description="First day, YYYY-MM-DD UTC.")]
ToDate = Annotated[date | None, Field(description="Last day, YYYY-MM-DD UTC.")]

PAYMENT_STATUS = {
    0: "created, payer has not opened the gateway",
    1: "paid and verified (final)",
    2: "payer is at the bank gateway",
    3: "cancelled by the payer",
    4: "paid at the gateway but bank verification failed",
    5: "returned from bank, waiting for merchant verify",
}


def segment(code: str) -> str:
    """A code as one URL path segment. "." and ".." are refused: URL normalization would climb out of the path."""
    if code.strip(".") == "":
        raise ApiError(f"Invalid code {code!r}.")
    return quote(code, safe="")


def _no_nulls(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _range(from_date: date | None, to_date: date | None) -> dict[str, str]:
    out = {}
    if from_date:
        out["fromDate"] = f"{from_date.isoformat()}T00:00:00Z"
    if to_date:
        out["toDate"] = f"{to_date.isoformat()}T23:59:59Z"
    return out


@tool("PayPing: account profile")
async def payping_get_profile() -> dict[str, Any]:
    """Show the PayPing account behind PAYPING_TOKEN: username, name, email, phone and verification flags."""
    info = await call_obj("GET", "/connect/userinfo", host=OAUTH)
    return {k: v for k, v in info.items() if not k.startswith("http")}


@tool("PayPing: wallet balance")
async def payping_get_balance() -> dict[str, Any]:
    """Current PayPing wallet balance in Toman (money received and not yet withdrawn)."""
    body = await call("GET", "/v1/report/Balance")
    return {"balance_toman": body.get("result") if isinstance(body, dict) else body}


@tool("PayPing: sales summary")
async def payping_get_sales_summary(from_date: FromDate = None, to_date: ToDate = None) -> dict[str, Any]:
    """Sales totals for a period (default last 30 days): amount in Toman, count, daily averages."""
    to_date = to_date or datetime.now(timezone.utc).date()
    from_date = from_date or to_date - timedelta(days=30)
    body = {"clientId": [], "fromDate": from_date.isoformat(), "terminalId": 0, "toDate": to_date.isoformat()}
    return _no_nulls(await call_obj("POST", "/v1/report/DashboardSummery", json=body))


@tool("PayPing: list transactions")
async def payping_list_transactions(
    from_date: FromDate = None,
    to_date: ToDate = None,
    kind: Annotated[
        Literal["received", "paid"] | None,
        Field(description="received = to you, paid = by you; omit for both."),
    ] = None,
    offset: Offset = 0,
    limit: Limit = 20,
) -> dict[str, Any]:
    """List payments, newest first, with total count. Use payping_get_payment for one payment's detail."""
    filters: dict[str, Any] = _range(from_date, to_date)
    if kind:
        filters["transactionType"] = 6 if kind == "received" else 7
    rows, count = await asyncio.gather(
        call("POST", "/v1/report/TransactionReport", json={"offset": offset, "limit": limit, **filters}),
        call("POST", "/v1/report/TransactionReportCount", json=filters),
    )
    return {"total": (count or {}).get("result"), "transactions": rows or []}


@tool("PayPing: payment detail")
async def payping_get_payment(code: Code) -> dict[str, Any]:
    """One payment by code: amount, payer, fees, refund state, paymentStatus and status_text. Use to check a payment succeeded."""
    out = await call_obj("GET", f"/v1/report/{segment(code)}")
    if out.get("paymentStatus") in PAYMENT_STATUS:
        out["status_text"] = PAYMENT_STATUS[out["paymentStatus"]]
    return out


@tool("PayPing: list withdrawals")
async def payping_list_withdrawals(offset: Offset = 0, limit: Limit = 20) -> dict[str, Any]:
    """List settlements (withdrawals to your bank) with total count."""
    rows, count = await asyncio.gather(
        call("POST", "/v1/report/WithdrawTransactions", json={"offset": offset, "limit": limit}),
        call("POST", "/v1/report/WithdrawTransactionsCount", json={}),
    )
    return {"total": (count or {}).get("result"), "withdrawals": rows or []}


@tool("PayPing: withdrawal detail")
async def payping_get_withdrawal(code: Code) -> dict[str, Any]:
    """One settlement by code: amount, dates, IBAN, bank tracking number."""
    return await call("GET", f"/v1/withdraw/{segment(code)}")
