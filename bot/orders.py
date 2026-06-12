"""
trading_bot/bot/orders.py

Order placement logic layer.
Translates validated order parameters into Binance Futures API calls
and returns structured order result objects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from bot.client import BinanceClient, BinanceClientError

logger = logging.getLogger("trading_bot.orders")

# Binance Futures order endpoint
ORDER_ENDPOINT = "/fapi/v1/order"


@dataclass
class OrderResult:
    """
    Structured representation of a Binance order response.

    Attributes:
        success:       True if the order was placed without errors.
        order_id:      Binance-assigned order ID.
        symbol:        Trading pair (e.g. 'BTCUSDT').
        side:          'BUY' or 'SELL'.
        order_type:    'MARKET' or 'LIMIT'.
        status:        Order status string from Binance (e.g. 'FILLED', 'NEW').
        orig_qty:      Original requested quantity.
        executed_qty:  Quantity that has been filled so far.
        avg_price:     Average fill price (may be '0' for unfilled LIMIT orders).
        price:         Limit price (empty string for MARKET orders).
        error_message: Human-readable error description (only set on failure).
        raw_response:  Full raw dict returned by the API.
    """
    success: bool
    order_id: Optional[int] = None
    symbol: str = ""
    side: str = ""
    order_type: str = ""
    status: str = ""
    orig_qty: str = ""
    executed_qty: str = ""
    avg_price: str = ""
    price: str = ""
    error_message: str = ""
    raw_response: dict = field(default_factory=dict)

    def display(self) -> str:
        """Return a formatted multi-line summary of the order result."""
        if not self.success:
            return (
                f"\n{'─' * 50}\n"
                f"  ❌  ORDER FAILED\n"
                f"  Error : {self.error_message}\n"
                f"{'─' * 50}"
            )

        price_line = f"  Price        : {self.price}" if self.price and self.price != "0" else ""
        avg_price_line = (
            f"  Avg Fill Price: {self.avg_price}"
            if self.avg_price and self.avg_price not in ("0", "")
            else ""
        )

        lines = [
            f"\n{'─' * 50}",
            f"  ✅  ORDER PLACED SUCCESSFULLY",
            f"{'─' * 50}",
            f"  Order ID     : {self.order_id}",
            f"  Symbol       : {self.symbol}",
            f"  Side         : {self.side}",
            f"  Type         : {self.order_type}",
            f"  Status       : {self.status}",
            f"  Orig Qty     : {self.orig_qty}",
            f"  Executed Qty : {self.executed_qty}",
        ]
        if price_line:
            lines.append(price_line)
        if avg_price_line:
            lines.append(avg_price_line)
        lines.append(f"{'─' * 50}")

        return "\n".join(lines)


class OrderManager:
    """
    High-level order management interface.

    Wraps the BinanceClient to provide order placement with
    structured results and detailed logging.

    Usage:
        manager = OrderManager(client)
        result  = manager.place_order(symbol="BTCUSDT", side="BUY",
                                       order_type="MARKET", quantity="0.001")
    """

    def __init__(self, client: BinanceClient) -> None:
        """
        Args:
            client: An authenticated BinanceClient instance.
        """
        self._client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
    ) -> OrderResult:
        """
        Place a MARKET or LIMIT order on Binance Futures Testnet.

        Args:
            symbol:     Trading pair (e.g. 'BTCUSDT').
            side:       'BUY' or 'SELL'.
            order_type: 'MARKET' or 'LIMIT'.
            quantity:   Order quantity as a string.
            price:      Limit price (required for LIMIT orders).

        Returns:
            OrderResult with success status and parsed response fields.
        """
        # ── Build the request parameters ───────────────────────────────────────
        params: dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        # LIMIT orders require a price and a timeInForce policy
        if order_type == "LIMIT":
            if not price:
                return OrderResult(
                    success=False,
                    error_message="price is required for LIMIT orders.",
                )
            params["price"] = price
            params["timeInForce"] = "GTC"  # Good Till Cancelled

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s%s",
            side,
            order_type,
            symbol,
            quantity,
            f" price={price}" if price else "",
        )
        logger.debug("Order request params: %s", params)

        # ── Send the request ───────────────────────────────────────────────────
        try:
            response = self._client.post(ORDER_ENDPOINT, params=params)
        except BinanceClientError as exc:
            logger.error("Order placement failed: %s", exc)
            return OrderResult(success=False, error_message=str(exc))
        except Exception as exc:  # Catch-all for unexpected errors
            logger.exception("Unexpected error during order placement: %s", exc)
            return OrderResult(success=False, error_message=f"Unexpected error: {exc}")

        # ── Parse the response ─────────────────────────────────────────────────
        logger.info(
            "Order accepted | orderId=%s status=%s executedQty=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
        )
        logger.debug("Full order response: %s", response)

        return OrderResult(
            success=True,
            order_id=response.get("orderId"),
            symbol=response.get("symbol", symbol),
            side=response.get("side", side),
            order_type=response.get("type", order_type),
            status=response.get("status", ""),
            orig_qty=response.get("origQty", quantity),
            executed_qty=response.get("executedQty", "0"),
            avg_price=response.get("avgPrice", "0"),
            price=response.get("price", ""),
            raw_response=response,
        )
