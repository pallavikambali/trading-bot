"""
trading_bot/bot/cli.py

Command-Line Interface layer (argparse).
Parses user arguments, calls the validation layer, then the order layer,
and prints a clean summary to the terminal.

This module is intentionally thin — it only handles I/O.
All business logic lives in validators.py, client.py, and orders.py.
"""

from __future__ import annotations

import argparse
import os
import sys
import logging

from bot.logging_config import setup_logging
from bot.client import BinanceClient
from bot.orders import OrderManager
from bot.validators import validate_order_inputs

logger = logging.getLogger("trading_bot.cli")


# ── Argument parser ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet trading bot — place MARKET and LIMIT orders from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Place a MARKET BUY order
  python main.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Place a LIMIT SELL order
  python main.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500

  # Use environment variables for credentials (recommended)
  export BINANCE_API_KEY=your_key
  export BINANCE_API_SECRET=your_secret
  python main.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
        """,
    )

    # ── Required order arguments ───────────────────────────────────────────────
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT, ETHUSDT",
    )
    parser.add_argument(
        "--side",
        type=str,
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        type=str,
        required=True,
        choices=["MARKET", "LIMIT"],
        metavar="TYPE",
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--quantity",
        type=str,
        required=True,
        metavar="QTY",
        help="Order quantity (e.g. 0.001 for BTC)",
    )
    parser.add_argument(
        "--price",
        type=str,
        default=None,
        metavar="PRICE",
        help="Limit price — required for LIMIT orders, ignored for MARKET",
    )

    # ── Optional credential arguments (fallback if env vars not set) ──────────
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        metavar="KEY",
        help="Binance Testnet API key (default: BINANCE_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        type=str,
        default=None,
        metavar="SECRET",
        help="Binance Testnet API secret (default: BINANCE_API_SECRET env var)",
    )

    return parser


# ── Credential resolution ──────────────────────────────────────────────────────

def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """
    Resolve API credentials from CLI args or environment variables.

    Priority order:
      1. --api-key / --api-secret CLI flags
      2. BINANCE_API_KEY / BINANCE_API_SECRET environment variables

    Returns:
        (api_key, api_secret) tuple.

    Raises:
        SystemExit: If credentials are missing.
    """
    api_key = args.api_key or os.getenv("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            "\n❌  Missing API credentials.\n"
            "    Set them via environment variables:\n"
            "      export BINANCE_API_KEY=your_key\n"
            "      export BINANCE_API_SECRET=your_secret\n"
            "    Or pass them with --api-key and --api-secret.\n"
        )
        sys.exit(1)

    return api_key, api_secret


# ── Main entry point ───────────────────────────────────────────────────────────

def run() -> None:
    """
    Main CLI entry point.

    Flow:
      1. Parse arguments
      2. Set up logging
      3. Resolve credentials
      4. Validate inputs
      5. Place order
      6. Print results
    """
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    logger.info("=== Trading Bot Session Started ===")

    # ── Step 1: Validate inputs ────────────────────────────────────────────────
    try:
        validated = validate_order_inputs(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValueError as exc:
        print(f"\n❌  Validation Error: {exc}\n")
        logger.error("Input validation failed: %s", exc)
        sys.exit(1)

    # ── Step 2: Print order request summary ───────────────────────────────────
    print(f"\n{'─' * 50}")
    print(f"  📋  ORDER REQUEST SUMMARY")
    print(f"{'─' * 50}")
    print(f"  Symbol    : {validated['symbol']}")
    print(f"  Side      : {validated['side']}")
    print(f"  Type      : {validated['order_type']}")
    print(f"  Quantity  : {validated['quantity']}")
    if validated["price"]:
        print(f"  Price     : {validated['price']}")
    print(f"{'─' * 50}\n")

    logger.info(
        "Order request | symbol=%s side=%s type=%s qty=%s price=%s",
        validated["symbol"],
        validated["side"],
        validated["order_type"],
        validated["quantity"],
        validated["price"] or "N/A",
    )

    # ── Step 3: Resolve credentials and build client ───────────────────────────
    api_key, api_secret = resolve_credentials(args)

    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    # Quick connectivity check before placing the real order
    print("🔗  Checking testnet connectivity...")
    if not client.test_connectivity():
        print("\n❌  Cannot reach Binance Futures Testnet. Check your internet connection.\n")
        sys.exit(1)
    print("✅  Connected to Binance Futures Testnet\n")

    # ── Step 4: Place the order ────────────────────────────────────────────────
    print("⏳  Placing order...")
    order_manager = OrderManager(client)
    result = order_manager.place_order(
        symbol=validated["symbol"],
        side=validated["side"],
        order_type=validated["order_type"],
        quantity=validated["quantity"],
        price=validated["price"],
    )

    # ── Step 5: Display result ─────────────────────────────────────────────────
    print(result.display())

    if result.success:
        logger.info("Session completed successfully.")
        sys.exit(0)
    else:
        logger.error("Session ended with order failure: %s", result.error_message)
        sys.exit(1)
