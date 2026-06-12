"""
trading_bot/bot/validators.py

Input validation layer.
All user-supplied CLI arguments are validated here before being sent to the API.
Raises ValueError with a human-readable message on invalid input.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger("trading_bot.validators")

# ── Allowed constant sets ──────────────────────────────────────────────────────
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


def _parse_positive_decimal(value: str, field_name: str) -> Decimal:
    """
    Convert a string to a positive Decimal.

    Args:
        value: String representation of the number.
        field_name: Human-readable name used in error messages.

    Returns:
        Positive Decimal value.

    Raises:
        ValueError: If the value cannot be parsed or is not positive.
    """
    try:
        dec = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"'{field_name}' must be a valid number. Got: {value!r}")

    if dec <= 0:
        raise ValueError(f"'{field_name}' must be greater than zero. Got: {dec}")

    return dec


def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
) -> dict:
    """
    Validate and normalise all order parameters.

    Args:
        symbol:     Trading pair, e.g. 'BTCUSDT'.
        side:       'BUY' or 'SELL' (case-insensitive).
        order_type: 'MARKET' or 'LIMIT' (case-insensitive).
        quantity:   Order quantity as a string.
        price:      Limit price as a string (required for LIMIT orders).

    Returns:
        Dictionary of validated and normalised parameters ready for the API.

    Raises:
        ValueError: On any invalid input.
    """
    logger.debug(
        "Validating inputs — symbol=%s side=%s type=%s qty=%s price=%s",
        symbol, side, order_type, quantity, price,
    )

    # ── Symbol ─────────────────────────────────────────────────────────────────
    symbol = symbol.strip().upper()
    if not symbol.isalpha():
        raise ValueError(
            f"Symbol must contain only letters (e.g. BTCUSDT). Got: {symbol!r}"
        )

    # ── Side ───────────────────────────────────────────────────────────────────
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Side must be one of {VALID_SIDES}. Got: {side!r}"
        )

    # ── Order type ─────────────────────────────────────────────────────────────
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type must be one of {VALID_ORDER_TYPES}. Got: {order_type!r}"
        )

    # ── Quantity ───────────────────────────────────────────────────────────────
    qty_decimal = _parse_positive_decimal(quantity, "quantity")

    # ── Price (LIMIT only) ────────────────────────────────────────────────────
    price_decimal: Optional[Decimal] = None
    if order_type == "LIMIT":
        if price is None or str(price).strip() == "":
            raise ValueError("'price' is required for LIMIT orders.")
        price_decimal = _parse_positive_decimal(price, "price")
    elif price is not None and str(price).strip() != "":
        logger.warning(
            "Price '%s' was supplied for a MARKET order and will be ignored.", price
        )

    validated = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": str(qty_decimal),
        "price": str(price_decimal) if price_decimal is not None else None,
    }

    logger.debug("Validation passed: %s", validated)
    return validated
