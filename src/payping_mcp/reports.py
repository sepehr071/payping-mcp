"""Account, balance, sales, transaction and withdrawal tools (read-only). Amounts are Toman."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any, Literal
from urllib.parse import quote

from pydantic import Field

from .http import OAUTH, ApiError, call
from .registry import tool

Offset = Annotated[int, Field(ge=0, description="Skip this many items (paging).")]
Limit = Annotated[int, Field(ge=1, le=50, description="Items to return, 1-50 (PayPing's maximum is 50).")]
Code = Annotated[str, Field(min_length=1, max_length=100)]
FromDate = Annotated[date | None, Field(description="First day to include (YYYY-MM-DD, UTC).")]
ToDate = Annotated[date | None, Field(description="Last day to include (YYYY-MM-DD, UTC).")]

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
    """Show the PayPing account behind PAYPING_TOKEN: username, name, email, phone and verification flags.
    Use first to confirm the token works."""
    info = await call("GET", "/connect/userinfo", host=OAUTH)
    return {k: v for k, v in info.items() if not k.startswith("http")}


@tool("PayPing: wallet balance")
async def payping_get_balance() -> dict[str, Any]:
    """Current PayPing wallet balance in Toman (money received and not yet withdrawn)."""
    body = await call("GET", "/v1/report/Balance")
    return {"balance_toman": body.get("result") if isinstance(body, dict) else body}


@tool("PayPing: sales summary")
async def payping_get_sales_summary(from_date: FromDate = None, to_date: ToDate = None) -> dict[str, Any]:
    """Sales totals for a period: total amount (Toman), transaction count and daily averages.
    Defaults to the last 30 days."""
    to_date = to_date or datetime.now(timezone.utc).date()
    from_date = from_date or to_date - timedelta(days=30)
    body = {"clientId": [], "fromDate": from_date.isoformat(), "terminalId": 0, "toDate": to_date.isoformat()}
    return _no_nulls(await call("POST", "/v1/report/DashboardSummery", json=body))


@tool("PayPing: list transactions")
async def payping_list_transactions(
    from_date: FromDate = None,
    to_date: ToDate = None,
    kind: Annotated[
        Literal["received", "paid"] | None,
        Field(description="'received' = payments to you, 'paid' = payments you made; omit for both."),
    ] = None,
    offset: Offset = 0,
    limit: Limit = 20,
) -> dict[str, Any]:
    """List payments (newest first) with amount (Toman), payer, description, isPaid and payment code, plus the
    total count for the same filter. Use payping_get_payment with a code for full detail."""
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
    """Full detail of one payment by its payment code: amount, dates, payer, card, fees, refund state and
    paymentStatus with a plain-English status_text. Use it to check whether a payment really succeeded."""
    out = await call("GET", f"/v1/report/{segment(code)}")
    if out.get("paymentStatus") in PAYMENT_STATUS:
        out["status_text"] = PAYMENT_STATUS[out["paymentStatus"]]
    return out


@tool("PayPing: list withdrawals")
async def payping_list_withdrawals(offset: Offset = 0, limit: Limit = 20) -> dict[str, Any]:
    """List settlements (withdrawals to your bank account): date, amount (Toman), code and whether it was paid
    out, plus the total count."""
    rows, count = await asyncio.gather(
        call("POST", "/v1/report/WithdrawTransactions", json={"offset": offset, "limit": limit}),
        call("POST", "/v1/report/WithdrawTransactionsCount", json={}),
    )
    return {"total": (count or {}).get("result"), "withdrawals": rows or []}


@tool("PayPing: withdrawal detail")
async def payping_get_withdrawal(code: Code) -> dict[str, Any]:
    """Detail of one settlement by code: amount (Toman), request and payout dates, IBAN, bank tracking number."""
    return await call("GET", f"/v1/withdraw/{segment(code)}")
