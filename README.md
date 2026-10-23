<!-- mcp-name: io.github.sepehr071/payping-mcp -->

<div align="center">

<img src="https://raw.githubusercontent.com/sepehr071/payping-mcp/main/.github/banner.png" alt="payping-mcp: unofficial PayPing MCP server for Claude, Cursor and Copilot" width="100%">

# payping-mcp: PayPing MCP server for AI agents

**Let your AI agent work with your PayPing (<span dir="rtl">پی&zwnj;پینگ</span>) merchant account.**<br>
An unofficial MCP server for [PayPing](https://payping.ir), the Iranian payment gateway and invoicing service:<br>
read balance, sales, transactions, customers, products, coupons and invoices, and create invoices, payment links and coupons after you confirm, from Claude, Cursor or Copilot.

[![PyPI](https://img.shields.io/pypi/v/payping-mcp?color=2563eb)](https://pypi.org/project/payping-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/payping-mcp)](https://pypi.org/project/payping-mcp/)
[![CI](https://github.com/sepehr071/payping-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehr071/payping-mcp/actions/workflows/ci.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.sepehr071%2Fpayping--mcp-7c3aed)](https://registry.modelcontextprotocol.io/?q=payping-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](https://github.com/sepehr071/payping-mcp/blob/main/LICENSE)

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=payping&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJwYXlwaW5nLW1jcCJdLCJlbnYiOnsiUEFZUElOR19UT0tFTiI6InlvdXItdG9rZW4ifX0=)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_payping--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=payping&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22payping-mcp%22%5D%2C%22env%22%3A%7B%22PAYPING_TOKEN%22%3A%22your-token%22%7D%7D)

[For AI agents](#for-ai-agents) · [Why](#why) · [What it can do](#what-it-can-do) · [Quick start](#quick-start) · [Tools](#tools) · [Security](#privacy-and-security) · [Troubleshooting](#troubleshooting) · [FAQ](#faq) · [فارسی](#فارسی)

</div>

---

## For AI agents

- **What:** unofficial MCP server (model context protocol) for a PayPing (payping.ir, Iran) merchant account. Amounts are Toman, dates UTC.
- **Install:** `uvx payping-mcp` (needs [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.10+; or `pip install payping-mcp`). Transport: stdio.
- **Claude Code:** `claude mcp add payping -e PAYPING_TOKEN=your-token -- uvx payping-mcp`
- **Auth:** `PAYPING_TOKEN` (required, a PayPing API token whose scopes decide what works); `PAYPING_MCP_PROXY` (optional HTTP proxy).
- **Access:** acts on the user's own account, so it is not read-only: 15 read tools and 6 create/send tools. Ask the user to confirm before any create or send tool. No tool can withdraw, refund, reverse or delete.
- **Tools:** 21, prefixed `payping_*`. Start with `payping_get_profile`, `payping_get_balance`, `payping_get_sales_summary`, `payping_list_transactions`, `payping_list_invoices`. Balance and sales summary use dashboard endpoints that PayPing may reject for API tokens; the other tools still work.
- **Typical sequence:** `payping_create_customer` -> `payping_create_invoice` -> `payping_send_invoice`; or `payping_create_product` -> `payping_create_payment_link`.
- **Units:** **Toman** (not Rial), dates and times UTC.
- **Use when:** the user wants to see or create invoices, payment links, coupons, customers or sales figures in their own PayPing account.
- **Do not use when:** the task is taking raw payments, verifying or refunding a payment, or paying out; there are no tools for these.
- **Output:** compact JSON; lists return at most 50 items with `total` (page with `offset`); pass codes (customer, product, invoice) between tools.
- **Machine-readable:** [`server.json`](https://github.com/sepehr071/payping-mcp/blob/main/server.json); catalog of all Iran MCP servers: [iran-mcp](https://github.com/sepehr071/iran-mcp) (`TOOLS.md`, `servers.json`, `llms.txt`).

## Why

The PayPing panel is built for people clicking through screens. Answering "how much did I sell this month, which payments failed, and who still owes me?" means opening several pages, and creating an invoice means filling in a customer, items and a send step by hand. With `payping-mcp` an agent does it in a few calls: it reads the numbers, drafts the invoice, shows you the details and only creates and sends it after you say yes.

> **You:** Create an invoice for Ali Rezaei: 2 hours of consulting at 1,500,000 Toman each, and send it.
>
> **Agent:** *calls* `payping_list_customers` -> shows you the invoice details and waits for your OK -> `payping_create_invoice` -> `payping_send_invoice`
>
> It gives you the public pay page link (`https://ppng.ir/v/<invoice code>`) and tells you PayPing sent the invoice by SMS/email.

Everything runs on your machine with your own token. There is no hosted relay in between.

## What it can do

- **Money:** wallet balance, sales totals for a period, transactions, one payment's real status, settlements to your bank
- **Shop data:** list and search customers, products, coupons and invoices
- **Get paid:** create a customer and an invoice with a pay page link, or a reusable payment link for a product, then have PayPing send the invoice by SMS/email
- **Safe by design:** runs on your machine, talks only to PayPing, asks before creating anything, and cannot withdraw, refund, reverse a payment or delete anything

Example prompts:

- "Show my PayPing profile."
- "What is my PayPing balance and how much did I sell this month?"
- "List this week's received payments and tell me which ones failed."
- "Which invoices are overdue?"
- "Create a product called Monthly plan at 490,000 Toman and give me a payment link."
- "Create an invoice for Ali Rezaei: 2 hours of consulting at 1,500,000 Toman each. Show me before you create it."
- <span dir="rtl">فاکتورهای پرداخت&zwnj;نشده این ماه را نشان بده.</span>
- <span dir="rtl">موجودی پی&zwnj;پینگ من چقدر است و این ماه چقدر فروش داشتم؟</span>
- <span dir="rtl">یک لینک پرداخت برای محصول «اشتراک ماهانه» بساز.</span>
- <span dir="rtl">آخرین تسویه&zwnj;های من به حساب بانکی را نشان بده.</span>

## Quick start

You need:

- a PayPing merchant account with a **complete profile** (PayPing only approves tokens for complete profiles)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- an MCP client: Claude Code, Claude Desktop, Cursor, VS Code, or any other

Then:

1. [Create a PayPing token](#1-create-a-payping-token) and wait for PayPing to approve it.
2. [Add the server](#2-add-the-server-to-your-mcp-client) to your MCP client.
3. [Check that it works](#3-check-that-it-works).

### 1. Create a PayPing token

1. Sign in at [app.payping.ir](https://app.payping.ir).
2. Open **اتصالات** (Connections) → **توسعه دهندگان** (Developers). The page title is **توکن ها** (Tokens).
3. Click **توکن جدید** (New token) and fill in the form:

   | Field | What to enter |
   |---|---|
   | توکن تست (test token) | Leave off to work with your real account. |
   | نام توکن (token name) | Any name, e.g. `payping-mcp on my laptop` |
   | آی&zwnj;پی&zwnj;های مجاز (allowed IPs) | Optional. If you fill it in, list the public IP your computer reaches PayPing from. Calls from any other IP fail with error code 166. |
   | تاریخ انقضا (expiry date) | When the token stops working. Shorter is safer. |
   | دسترسی&zwnj;ها (scopes) | See the table below. |
   | توضیحات (description) | e.g. `MCP server for AI agents` |
   | رمز پیامکی (SMS code) | Click **ارسال رمز** (send code) and type the code PayPing sends to your phone. |

4. Click **توکن جدید** to submit. **Copy the token now: PayPing shows it only once.**
5. Wait for approval. PayPing staff review every new token. After approval, wait about 10 more minutes; until then the token gets HTTP 401.

**Scopes.** The form preselects **گزارش پرداخت&zwnj;ها** and **ساخت پرداخت**. Remove **ساخت پرداخت**: this server never uses it. Then add what you need:

| Panel label | Scope | Tools that need it |
|---|---|---|
| گزارش پرداخت&zwnj;ها | `pay:read` | transactions, payment detail, withdrawals |
| مشاهده و گزارش از مشتریان | `customer:read` | list and get customers |
| ساخت و ویرایش مشتریان | `customer:write` | create customer |
| مشاهده و گزارش از محصولات | `product:read` | list and get products |
| ساخت و ویرایش محصولات | `product:write` | create product, create payment link |
| مشاهده و گزارش کدهای تخفیف | `coupon:read` | list and get coupons |
| ساخت و ویرایش کدهای تخفیف | `coupon:write` | create coupon |
| مشاهده و گزارش از فاکتورها | `invoice:read` | list and get invoices |
| ساخت و ویرایش فاکتور | `invoice:write` | create and send invoices |
| ساخت پرداخت | `pay:write` | none: leave it out |

Want a read-only agent? Select only the read scopes. The create tools then fail with HTTP 403 and nothing in the account can change.

### 2. Add the server to your MCP client

Put your token where it says `your-token`.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add payping -e PAYPING_TOKEN=your-token -- uvx payping-mcp
```

This saves the server, with the token, in your user config (`~/.claude.json`), not in the project. Add `--scope user` to use it in every project.
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config, then add:

```json
{
  "mcpServers": {
    "payping": {
      "command": "uvx",
      "args": ["payping-mcp"],
      "env": { "PAYPING_TOKEN": "your-token" }
    }
  }
}
```

Restart Claude Desktop after saving.
</details>

<details>
<summary><b>Cursor</b></summary>

Click **Install in Cursor** at the top and fill in the token, or add the Claude Desktop block to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project).
</details>

<details>
<summary><b>VS Code (Copilot agent mode)</b></summary>

Click **Install in VS Code** at the top, or add to `.vscode/mcp.json`. VS Code asks for the token once and stores it securely, so the file is safe to commit:

```json
{
  "inputs": [
    { "type": "promptString", "id": "payping-token", "description": "PayPing API token", "password": true }
  ],
  "servers": {
    "payping": {
      "type": "stdio",
      "command": "uvx",
      "args": ["payping-mcp"],
      "env": { "PAYPING_TOKEN": "${input:payping-token}" }
    }
  }
}
```
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
codex mcp add payping --env PAYPING_TOKEN=your-token -- uvx payping-mcp
```

Or in `~/.codex/config.toml`:

```toml
[mcp_servers.payping]
command = "uvx"
args = ["payping-mcp"]

[mcp_servers.payping.env]
PAYPING_TOKEN = "your-token"
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "payping": {
      "command": "uvx",
      "args": ["payping-mcp"],
      "env": { "PAYPING_TOKEN": "your-token" }
    }
  }
}
```
</details>

<details>
<summary><b>Windsurf</b></summary>

Add the Claude Desktop block to `~/.codeium/windsurf/mcp_config.json`.
</details>

<details>
<summary><b>From GitHub instead of PyPI</b></summary>

Replace `uvx payping-mcp` with:

```bash
uvx --from git+https://github.com/sepehr071/payping-mcp payping-mcp
```

In JSON configs: `"args": ["--from", "git+https://github.com/sepehr071/payping-mcp", "payping-mcp"]`.
</details>

<details>
<summary><b>Anything else</b></summary>

It's a standard stdio MCP server: run `uvx payping-mcp`, or `pip install payping-mcp` and run `payping-mcp`, with
`PAYPING_TOKEN` in the environment.
</details>

### 3. Check that it works

Ask the agent: *"Show my PayPing profile."* You should see your PayPing username. If you see an error, look it up in
[Troubleshooting](#troubleshooting).

Then try the example prompts under [What it can do](#what-it-can-do).

## Tools

All amounts are Toman, all dates UTC. Lists return at most 50 items per call and include `total`.

Read-only (15):

| Tool | What it does |
|---|---|
| `payping_get_profile` | Account behind the token: username, name, contact, verification flags |
| `payping_get_balance` | Wallet balance |
| `payping_get_sales_summary` | Total sales, count and daily averages for a period (default last 30 days) |
| `payping_list_transactions` | Payments in a date range, received or paid |
| `payping_get_payment` | One payment by code, with its real status (paid and verified, cancelled, ...) |
| `payping_list_withdrawals` | Settlements to your bank account |
| `payping_get_withdrawal` | One settlement by code: IBAN, bank tracking number |
| `payping_list_customers` | Saved customers, searchable |
| `payping_get_customer` | One customer |
| `payping_list_products` | Products (financial items), searchable |
| `payping_get_product` | One product |
| `payping_list_coupons` | Discount coupons |
| `payping_get_coupon` | One coupon with buyer count and total |
| `payping_list_invoices` | Invoices, filter by status or customer |
| `payping_get_invoice` | One invoice with items and its pay page url |

Create and send (6; the agent must confirm with you first):

| Tool | What it does |
|---|---|
| `payping_create_customer` | Save a customer; returns its code |
| `payping_create_product` | Create a product with a fixed or payer-set price |
| `payping_create_payment_link` | Public pay page for a product: `https://ppng.ir/d/<product code>` |
| `payping_create_coupon` | Percent or Toman discount coupon |
| `payping_create_invoice` | Invoice for a saved customer; returns its pay page `https://ppng.ir/v/<invoice code>` |
| `payping_send_invoice` | PayPing sends the invoice to the customer by SMS/email |

## How it works

```text
  AI agent  (Claude, Cursor, Copilot, ...)
      │
      │  MCP over stdio
      ▼
  payping-mcp  (runs on your machine, holds PAYPING_TOKEN)
      │
      │  HTTPS (REST, Bearer token, optional proxy)
      ├──────▶  api.payping.ir    (reports, customers, products, coupons, invoices)
      └──────▶  oauth.payping.ir  (profile)
```

`payping-mcp` runs locally and calls PayPing's API with your own token. There's no hosted server in between. It ignores system proxy settings, retries a failed GET once after a second on HTTP 429, 502 or 503 (never a create or send call), keeps no cache, and returns each result as one compact JSON block with empty fields dropped.

## Privacy and security

- **Local only.** The server runs on your machine and talks only to `api.payping.ir` and `oauth.payping.ir`. There is no relay server and no telemetry.
- **The token never leaks.** It is sent only in the `Authorization` header to PayPing and never appears in tool output, errors or logs.
- **Treat the token like a password.** Anyone who has it can use your account within its scopes. Don't commit it; use VS Code `inputs` or your client's user config. Give it only the scopes you need and an expiry date.
- **Lost or leaked token?** In the panel, open the token and use **حذف** (delete) or **تعویض توکن** (swap token, which issues a new value). Then update your MCP config.
- **Confirm before creating.** Create and send tools are annotated `destructiveHint`, so MCP clients ask before running them. Their descriptions also tell the agent to confirm the details with you.
- **No money moves out.** No tool can withdraw, refund, reverse a payment or delete anything.
- **Prompt-injection aware.** Customer names, descriptions and notes come from other people. The server tells the agent to treat them as data, never as instructions.

## Good to know

- **Toman, not Rial.** PayPing uses Toman in every service, and so does every tool. Dates and times are UTC.
- **Not read-only.** Six tools create data or message a real customer. Use read-only scopes if you want an agent that can only look.
- **Limits.** Lists return at most 50 items per call (limit 1-50); page with `offset`. `redirect_url` must be https.
- **Balance and sales summary are less certain.** `payping_get_balance` and `payping_get_sales_summary` use endpoints from the PayPing dashboard, not the public API docs. If PayPing rejects them for API tokens, the tool error says so, and every other tool keeps working.
- **No raw payments.** Raw `POST /v3/pay` payments are left out on purpose. They need your own callback server and a verify call within 10 minutes, or PayPing refunds the payer. Invoices and payment links use PayPing's own pay page instead.
- **What it does not do.** No withdrawals, refunds, payment reversal, verification of raw payments, updates or deletes.
- **Changing scopes needs a swap.** After you edit a token's website, return URL or scopes, PayPing applies the change only after **تعویض توکن** (swap token). The swap gives a new token value; put it in your MCP config.
- **Proxy.** Set `PAYPING_MCP_PROXY` if your network needs a proxy to reach PayPing. System proxy variables are ignored on purpose.

## Troubleshooting

<details>
<summary><b>"PAYPING_TOKEN is not set"</b></summary>

The MCP client did not pass the token. Check the `env` block (or `-e PAYPING_TOKEN=...` for Claude Code) and restart the client.
</details>

<details>
<summary><b>"PayPing rejected the token (HTTP 401)"</b></summary>

One of these:

- PayPing has not approved the token yet, or approved it less than 10 minutes ago.
- The token expired. The panel shows **منقضی شده** (expired) on it.
- The token was swapped or deleted, or was copied incompletely.
</details>

<details>
<summary><b>HTTP 403: "The token may lack the scope this tool needs"</b></summary>

Add the scope from the [scope table](#1-create-a-payping-token) to the token, then **تعویض توکن** (swap token) and use the new value.
</details>

<details>
<summary><b>"code 166"</b></summary>

Your IP is not in the token's allowed IPs. Add your current public IP to **آی&zwnj;پی&zwnj;های مجاز** or clear the list. If you route through a proxy, the IP PayPing sees is the proxy's exit IP.
</details>

<details>
<summary><b>"Could not reach PayPing" or "PayPing did not answer in time"</b></summary>

The server ignores system proxy settings on purpose. If your network needs a proxy to reach PayPing, set `PAYPING_MCP_PROXY`, e.g. `http://127.0.0.1:10809`. In testing, PayPing's API hosts answered both from Iran and from a foreign exit.
</details>

<details>
<summary><b>Claude Desktop says <code>uvx</code> is not found</b></summary>

Use the full path to `uvx` (`where uvx` on Windows, `which uvx` on macOS/Linux) as `command`.
</details>

<details>
<summary><b>How do I see exactly what the agent sees?</b></summary>

```bash
npx @modelcontextprotocol/inspector -e PAYPING_TOKEN=your-token uvx payping-mcp
```
</details>

Errors that carry a PayPing trace id: give that id to PayPing support.

## FAQ

<details>
<summary><b>Is there a PayPing API for AI agents or an MCP server?</b></summary>

Yes. `payping-mcp` wraps the PayPing merchant API as 21 MCP tools, so any MCP client can use it with your own token.
</details>

<details>
<summary><b>How do I use PayPing with Claude, Cursor or Copilot?</b></summary>

Create a PayPing token, then add the server with `claude mcp add payping -e PAYPING_TOKEN=your-token -- uvx payping-mcp` or the config blocks in [Quick start](#quick-start).
</details>

<details>
<summary><b>Is it official, safe and free?</b></summary>

It is unofficial and free (MIT). It runs on your machine, talks only to PayPing and cannot withdraw or refund. Give the token only the scopes you need; read-only scopes make it read-only.
</details>

<details>
<summary><b>Can the agent create invoices or payment links without asking me?</b></summary>

The tools are annotated so MCP clients ask before running them, and the server tells the agent to confirm the details with you first. Your client's permission settings have the last word, and a token with only read scopes cannot create anything.
</details>

<details>
<summary><b>Can it move money out of my account?</b></summary>

No. There are no tools to withdraw, refund, reverse a payment or delete anything.
</details>

<details>
<summary><b>Why does the token get HTTP 401 right after PayPing approved it?</b></summary>

PayPing staff review every new token, and the token starts working about 10 minutes after approval.
</details>

<details>
<summary><b>Why do balance or sales summary fail?</b></summary>

They use dashboard endpoints, not the documented public API, and PayPing may reject them for API tokens. The error says so and the other tools keep working.
</details>

<details>
<summary><b>Does it work outside Iran?</b></summary>

The PayPing API hosts answered both from Iran and from a foreign exit in testing. You still need a PayPing merchant account; set `PAYPING_MCP_PROXY` if your network needs a proxy.
</details>

<details>
<summary><b>Are amounts in Rial or Toman?</b></summary>

Toman, in every tool.
</details>

## Configuration

| Variable | Required | Meaning |
|---|---|---|
| `PAYPING_TOKEN` | yes | API token from the PayPing panel (app.payping.ir, Connections > Developers > Tokens). Secret. |
| `PAYPING_MCP_PROXY` | no | HTTP proxy URL for every request, e.g. `http://user:pass@host:port`. System proxy settings are ignored. |

<a id="فارسی"></a>

## فارسی: سرور MCP پی&zwnj;پینگ

<div dir="rtl">

**payping-mcp** یک سرور MCP غیررسمی برای پی&zwnj;پینگ (درگاه پرداخت و فاکتورنویسی آنلاین در ایران) است و به دستیار هوش مصنوعی شما (Claude، Cursor، Copilot و ...) اجازه می&zwnj;دهد موجودی، فروش، تراکنش&zwnj;ها، تسویه&zwnj;ها، مشتریان، محصولات، کدهای تخفیف و فاکتورهای حساب پی&zwnj;پینگ شما را ببیند، و پس از تأیید شما مشتری، محصول، لینک پرداخت، کد تخفیف و فاکتور بسازد.

- روی سیستم خود شما اجرا می&zwnj;شود و توکن فقط به سرورهای پی&zwnj;پینگ فرستاده می&zwnj;شود.
- فقط&zwnj;خواندنی نیست: ابزارهای ساخت و ارسال روی حساب واقعی شما کار می&zwnj;کنند و باید پیش از اجرا تأیید بدهید. اگر فقط دسترسی&zwnj;های خواندن را به توکن بدهید، چیزی در حساب تغییر نمی&zwnj;کند.
- برداشت، استرداد، برگشت پرداخت و حذف با این ابزار ممکن نیست.
- مبالغ به تومان و تاریخ&zwnj;ها به وقت UTC هستند.

**ساخت توکن:**

1. در [پنل پی&zwnj;پینگ](https://app.payping.ir) به «اتصالات ← توسعه دهندگان» بروید و «توکن جدید» را بزنید.
2. نام توکن، تاریخ انقضا و توضیحات را وارد کنید. «آی&zwnj;پی&zwnj;های مجاز» اختیاری است؛ اگر پر کنید، درخواست از آی&zwnj;پی دیگر با خطای 166 رد می&zwnj;شود.
3. در «دسترسی&zwnj;ها» فقط موارد لازم را انتخاب کنید و «ساخت پرداخت» را حذف کنید؛ این ابزار به آن نیازی ندارد.
4. رمز پیامکی را بگیرید و وارد کنید. توکن فقط یک بار نمایش داده می&zwnj;شود؛ همان لحظه کپی کنید.
5. پروفایل شما باید کامل باشد. کارشناس پی&zwnj;پینگ توکن را تأیید می&zwnj;کند و تا حدود ۱۰ دقیقه بعد از تأیید ممکن است خطای 401 بگیرید.

**نصب در Claude Code:**

</div>

```bash
claude mcp add payping -e PAYPING_TOKEN=your-token -- uvx payping-mcp
```

<div dir="rtl">

**نمونه پرسش&zwnj;ها**

- «موجودی پی&zwnj;پینگ من چقدر است و این ماه چقدر فروختم؟»
- «فاکتورهای پرداخت&zwnj;نشده این ماه را نشان بده.»
- «یک فاکتور برای علی رضایی بساز: ۲ ساعت مشاوره، ساعتی ۱٬۵۰۰٬۰۰۰ تومان. قبل از ساخت به من نشان بده.»
- «برای محصول من لینک پرداخت بساز.»
- «آخرین تسویه&zwnj;ها به حساب بانکی من چه بوده&zwnj;اند؟»

توکن را مثل رمز عبور نگه دارید و در گیت قرار ندهید. اگر لو رفت، در پنل آن را حذف یا «تعویض توکن» کنید.

</div>

## Development

```bash
git clone https://github.com/sepehr071/payping-mcp && cd payping-mcp
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest -q                                   # offline, against a mocked PayPing API
PAYPING_TOKEN=your-token uv run pytest -m live     # read-only calls to the real API
```

Tools live in `src/payping_mcp/reports.py` (account, money) and `shop.py` (customers, products, coupons, invoices);
`http.py` is the only HTTP code. Each tool is a typed async function with a docstring that tells the agent when to
use it. Issues and PRs are welcome.

Releases: bump the version in `pyproject.toml` and `server.json`, then push a `v*` tag. GitHub Actions tests,
publishes to PyPI and the [MCP Registry](https://registry.modelcontextprotocol.io), and creates the GitHub Release.

## Related servers

- [iran-mcp](https://github.com/sepehr071/iran-mcp): catalog of all Iranian-service MCP servers
- [bale-mcp](https://github.com/sepehr071/bale-mcp) for sending messages through a Bale bot, the other account tool in this family
- [iran-tax-mcp](https://github.com/sepehr071/iran-tax-mcp) for Iranian tax data
- [tgju-mcp](https://github.com/sepehr071/tgju-mcp) for dollar, gold, coin and commodity prices from TGJU
- [iran-crypto-mcp](https://github.com/sepehr071/iran-crypto-mcp) for crypto prices on Iranian exchanges

## Disclaimer

Unofficial and not affiliated with or endorsed by PayPing. It uses PayPing's API with your own token. Follow
PayPing's terms. It acts on your own account: review what the agent is about to create or send.

If this saves you clicks, a star helps others find it.

## Author

<a href="https://www.linkedin.com/in/sepehr-radmard"><img src="https://raw.githubusercontent.com/sepehr071/iran-mcp/main/assets/author-banner.png" alt="Sepehr Radmard: open-source MCP servers for the Iranian web. LinkedIn: linkedin.com/in/sepehr-radmard" width="100%"></a>

Built and maintained by **Sepehr Radmard** (سپهر رادمرد). Connect on [LinkedIn](https://www.linkedin.com/in/sepehr-radmard) or follow [@sepehr071 on GitHub](https://github.com/sepehr071) for more MCP servers for Iranian websites, all listed in [iran-mcp](https://github.com/sepehr071/iran-mcp). If this saves you time, a star on the repo helps other people find it.

## License

[MIT](https://github.com/sepehr071/payping-mcp/blob/main/LICENSE)
