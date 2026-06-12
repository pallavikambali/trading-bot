# 🤖 Binance Futures Testnet Trading Bot

A clean, production-style Python CLI trading bot for placing **MARKET** and **LIMIT** orders on Binance Futures Demo Trading (USDT-M), using the API base endpoint `https://demo-fapi.binance.com`.

---

## 📁 Project Structure
trading_bot/
├── bot/
│   ├── init.py          # Package exports
│   ├── client.py            # Binance REST API client (auth, signing, HTTP)
│   ├── orders.py            # Order placement logic + OrderResult dataclass
│   ├── validators.py        # Input validation layer
│   ├── logging_config.py    # Rotating file + console logging setup
│   └── cli.py               # argparse CLI entry point
├── logs/
│   └── trading.log          # Auto-created on first run
├── main.py                  # Application entry point
├── requirements.txt
└── README.md

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python **3.10+** (uses `match` syntax internally; `tuple[str, str]` type hints)
- `pip` package manager

### 2. Create & Activate a Virtual Environment

```bash
# Create
python -m venv venv

# Activate (Linux / macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Your Binance Futures Demo Trading API Keys

> Demo trading is completely free — no real money is involved.

1. Log in to your existing Binance account at [https://www.binance.com](https://www.binance.com)
2. Navigate to [https://demo.binance.com](https://demo.binance.com) and click **"Start demo trading"**
3. Switch to the **"Futures"** tab
4. Go to **Account → API Management** (`demo.binance.com/en/my/settings/api-management`)
5. Click **"Create API"**, give it a label (e.g. `tradingbot`), and confirm
6. Copy both the **API Key** and **Secret Key** immediately (the secret is shown only once)
7. Ensure **"Enable Futures"** is checked under API restrictions

> Note: Binance previously used `testnet.binancefuture.com` with GitHub login; this has been superseded by the Demo Trading platform above, which uses your regular Binance account and the API base endpoint `https://demo-fapi.binance.com`.

### 5. Configure Your API Credentials

**Option A — Environment variables (recommended)**

```bash
# Linux / macOS
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"

# Windows (Command Prompt)
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here
```

**Option B — `.env` file (with python-dotenv)**

Create a `.env` file in the project root:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

Then load it at the top of `main.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

**Option C — CLI flags (quick testing only)**

```bash
python main.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol BTCUSDT ...
```

> ⚠️  Never commit API keys to Git. Add `.env` to your `.gitignore`.

---

## 🚀 How to Run

### General Syntax

```bash
python main.py \
  --symbol   <SYMBOL>    \   # e.g. BTCUSDT
  --side     <BUY|SELL>  \   # order direction
  --type     <MARKET|LIMIT> \
  --quantity <QTY>       \   # e.g. 0.001
  [--price   <PRICE>]        # required for LIMIT orders
```

---

## 📖 Sample Commands

### ✅ MARKET BUY Order

```bash
python main.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

**Expected terminal output:**
──────────────────────────────────────────────────
📋  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
Symbol    : BTCUSDT
Side      : BUY
Type      : MARKET
Quantity  : 0.001
──────────────────────────────────────────────────
🔗  Checking testnet connectivity...
✅  Connected to Binance Futures Testnet
⏳  Placing order...
──────────────────────────────────────────────────
✅  ORDER PLACED SUCCESSFULLY
──────────────────────────────────────────────────
Order ID     : 3851920471
Symbol       : BTCUSDT
Side         : BUY
Type         : MARKET
Status       : FILLED
Orig Qty     : 0.001
Executed Qty : 0.001
Avg Fill Price: 57821.40
──────────────────────────────────────────────────

---

### ✅ LIMIT SELL Order

```bash
python main.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 3450
```

**Expected terminal output:**
──────────────────────────────────────────────────
📋  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
Symbol    : ETHUSDT
Side      : SELL
Type      : LIMIT
Quantity  : 0.05
Price     : 3450
──────────────────────────────────────────────────
🔗  Checking testnet connectivity...
✅  Connected to Binance Futures Testnet
⏳  Placing order...
──────────────────────────────────────────────────
✅  ORDER PLACED SUCCESSFULLY
──────────────────────────────────────────────────
Order ID     : 3851993204
Symbol       : ETHUSDT
Side         : SELL
Type         : LIMIT
Status       : NEW
Orig Qty     : 0.05
Executed Qty : 0
Price        : 3450.00000
──────────────────────────────────────────────────

> A LIMIT order with status `NEW` means it has been accepted and is waiting for the market price to reach your limit price.

---

### ❌ Error Example — Missing Price for LIMIT

```bash
python main.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001
```
❌  Validation Error: 'price' is required for LIMIT orders.

---

## 📝 Log Files

Logs are written to `logs/trading.log` and rotate automatically (max 5 MB, 3 backups).

Each run logs:

| Level   | Content |
|---------|---------|
| `INFO`  | Session start/end, connectivity check, order summary |
| `DEBUG` | Full request params, raw API responses |
| `ERROR` | Validation failures, API errors, network issues |

**Sample log — MARKET order:**
2025-07-10 14:22:01 | trading_bot.cli      | INFO     | === Trading Bot Session Started ===
2025-07-10 14:22:01 | trading_bot.orders   | INFO     | Placing BUY MARKET order | symbol=BTCUSDT qty=0.001
2025-07-10 14:22:02 | trading_bot.orders   | INFO     | Order accepted | orderId=3851920471 status=FILLED executedQty=0.001
2025-07-10 14:22:02 | trading_bot.cli      | INFO     | Session completed successfully.

**Sample log — LIMIT order:**
2025-07-10 14:35:17 | trading_bot.cli      | INFO     | === Trading Bot Session Started ===
2025-07-10 14:35:18 | trading_bot.orders   | INFO     | Placing SELL LIMIT order | symbol=ETHUSDT qty=0.05 price=3450.00
2025-07-10 14:35:18 | trading_bot.orders   | INFO     | Order accepted | orderId=3851993204 status=NEW executedQty=0
2025-07-10 14:35:18 | trading_bot.cli      | INFO     | Session completed successfully.

---

## 🏗️ Architecture Overview
main.py
└─ cli.py          ← parses args, prints UI, orchestrates the flow
├─ validators.py   ← sanitises and validates all user input
├─ client.py       ← handles HTTP, HMAC signing, error parsing
└─ orders.py       ← builds request params, calls client, wraps response

Each layer has a single responsibility:

- **`validators.py`** — Pure validation. No HTTP, no side effects.
- **`client.py`** — Pure transport. No business logic; just sign, send, parse.
- **`orders.py`** — Business logic. Translates validated params → API call → structured result.
- **`cli.py`** — I/O only. Reads CLI args, prints to terminal, calls the layers above.

---

## 🔍 Assumptions

1. Only **USDT-M Futures** (linear perpetuals) are targeted; the endpoint is `/fapi/v1/order`.
2. LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) — the most common default.
3. Credentials are never stored in code; they must come from environment variables or CLI flags.
4. The bot places **one order per invocation** — this is intentional for simplicity and auditability.
5. All prices and quantities are treated as strings to preserve decimal precision (no floating-point rounding).

---

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Missing API credentials` | Set `BINANCE_API_KEY` and `BINANCE_API_SECRET` env vars |
| `Binance API error -2014` | API key format is invalid — re-generate on testnet |
| `Binance API error -1121` | Symbol is invalid for testnet (try `BTCUSDT` or `ETHUSDT`) |
| `Network connection failed` | Check your internet connection; testnet may be briefly down |
| `Order rejected — insufficient margin` | Testnet accounts start with demo funds; reset balance in the testnet UI |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client for REST API calls |
| `python-dotenv` | Optional: load `.env` credentials file |

No Binance SDK is used — all communication is via raw REST calls for full transparency and minimal dependencies.
