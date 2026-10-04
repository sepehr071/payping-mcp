# payping-mcp

Local MCP server for PayPing (payping.ir) merchant accounts. Published: GitHub `sepehr071/payping-mcp`, PyPI
`payping-mcp`, MCP Registry `io.github.sepehr071/payping-mcp` (release on a `v*` tag; bump `pyproject.toml` and
`server.json`). Sibling of `../bale-mcp`; keep layout and
idioms in step. The API map it is built on lives in `../payping/` (official spec, dashboard catalog, captured shapes).

Scope (owner's decision 2026-10-03): read + create. No raw `/v3/pay`, verify, reverse, withdraw, refund, update or
delete tools; do not add them without the owner asking.

## Layout

- `src/payping_mcp/http.py`: the only HTTP code. Shared `httpx.AsyncClient` (`trust_env=False`, proxy only from
  `PAYPING_MCP_PROXY`), `call(method, path, params=, json=, host=)`, `ApiError(ToolError)` with `redact()` of the
  token, error text from problem JSON (`detail`, `errorCode` / `metaData.code`, `paypingTraceId`).
- `reports.py`: profile (oauth host), balance, sales summary, transactions, payment, withdrawals. Shared `Offset`,
  `Limit` (1-50), `Code`, `segment()`.
- `shop.py`: customers, products, coupons, invoices (list/get), create tools (`sends=True`), send invoice.
- `registry.py` + `server.py`: `@tool("Title", sends=...)`, annotations, `INSTRUCTIONS`. 21 tools, all `payping_*`.
- `tests/`: offline (`conftest.py` MockTransport keyed `"METHOD /path"`), `test_live.py` (`-m live`, read-only).

## Commands

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest -q
set -a; . ../.env; set +a; uv run pytest -m live   # PAYPING_TOKEN in ../.env
```

## Rules for changes

- Never put the token in output, errors or logs.
- Create/send tools: `sends=True`, docstring tells the agent to confirm with the user.
- Keep `README.md` tool tables equal to `list_tools()` (`test_readme_lists_every_tool`). Deps stay `mcp` + `httpx`.
- Persian ZWNJ and Arabic yeh/kaf in code: escapes, never literals.

## Unverified (check on first live run)

- Whether a panel API token is accepted by `/v1/report/Balance` and `/v1/report/DashboardSummery` (dashboard-only).
- Coupon/discount `type`: Percent=0, Toman=1, from the dashboard bundle enum.
- Pay page links `https://ppng.ir/d/{product code}` and `https://ppng.ir/v/{invoice code}`, from the dashboard bundle.
- `/v1/coupon/ListCount` and `/v1/product/ListCount` response shape (`{"count": n}` seen on the dashboard).
