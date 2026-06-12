"""
trading_bot/bot/client.py

Binance Futures Testnet REST API client (API / transport layer).
Handles authentication (HMAC-SHA256 signatures), request signing,
and raw HTTP communication with the testnet endpoint.

All callers receive plain Python dicts — no Binance SDK dependency required.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

# ── Testnet base URL ───────────────────────────────────────────────────────────
TESTNET_BASE_URL = "https://demo-fapi.binance.com"

# How long to wait for a response before raising a timeout error (seconds)
REQUEST_TIMEOUT = 10


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""


class BinanceClient:
    """
    Lightweight wrapper around the Binance Futures Testnet REST API.

    Handles:
    - HMAC-SHA256 request signing
    - Timestamping every signed request
    - GET / POST helpers
    - Structured error handling

    Usage:
        client = BinanceClient(api_key="...", api_secret="...")
        result = client.post("/fapi/v1/order", params={...})
    """

    def __init__(self, api_key: str, api_secret: str) -> None:
        """
        Initialise the client with Binance Futures Testnet credentials.

        Args:
            api_key:    Your testnet API key.
            api_secret: Your testnet API secret.
        """
        if not api_key or not api_secret:
            raise ValueError("Both api_key and api_secret must be non-empty strings.")

        self._api_key = api_key
        self._api_secret = api_secret
        self._session = requests.Session()
        # The API key goes in every request header
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        logger.info("BinanceClient initialised (testnet: %s)", TESTNET_BASE_URL)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a timestamp and HMAC-SHA256 signature to *params* (in-place copy).

        Args:
            params: Request parameters dict.

        Returns:
            New dict with 'timestamp' and 'signature' appended.
        """
        signed = dict(params)
        signed["timestamp"] = int(time.time() * 1000)  # milliseconds

        query_string = urlencode(signed)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signed["signature"] = signature
        return signed

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse the HTTP response and raise on error.

        Args:
            response: Raw requests.Response object.

        Returns:
            Parsed JSON body as a dict.

        Raises:
            BinanceClientError: If the API returned a non-2xx status or error body.
        """
        logger.debug("HTTP %s %s", response.status_code, response.url)

        try:
            data: Dict[str, Any] = response.json()
        except ValueError:
            logger.error("Non-JSON response: %s", response.text)
            raise BinanceClientError(f"Non-JSON response (HTTP {response.status_code}): {response.text}")

        # Binance returns error details in a 'code' / 'msg' envelope
        if not response.ok or (isinstance(data, dict) and "code" in data and data["code"] != 200):
            error_code = data.get("code", response.status_code)
            error_msg = data.get("msg", "Unknown error")
            logger.error("Binance API error %s: %s", error_code, error_msg)
            raise BinanceClientError(f"Binance API error {error_code}: {error_msg}")

        logger.debug("API response: %s", data)
        return data

    # ── Public interface ───────────────────────────────────────────────────────

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Send a signed or unsigned GET request.

        Args:
            path:   API path, e.g. '/fapi/v1/exchangeInfo'.
            params: Query parameters.
            signed: If True, adds timestamp + HMAC signature.

        Returns:
            Parsed response dict.
        """
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{TESTNET_BASE_URL}{path}"
        logger.debug("GET %s params=%s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            raise BinanceClientError(f"Request timed out after {REQUEST_TIMEOUT}s: GET {path}")
        except requests.exceptions.ConnectionError as exc:
            raise BinanceClientError(f"Network connection failed: {exc}")

        return self._handle_response(response)

    def post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a signed POST request (all order endpoints require signing).

        Args:
            path:   API path, e.g. '/fapi/v1/order'.
            params: Request body parameters.

        Returns:
            Parsed response dict.
        """
        params = params or {}
        signed_params = self._sign(params)

        url = f"{TESTNET_BASE_URL}{path}"
        # Log without the signature for brevity
        safe_params = {k: v for k, v in signed_params.items() if k not in ("signature",)}
        logger.debug("POST %s params=%s", url, safe_params)

        try:
            response = self._session.post(
                url,
                data=urlencode(signed_params),
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            raise BinanceClientError(f"Request timed out after {REQUEST_TIMEOUT}s: POST {path}")
        except requests.exceptions.ConnectionError as exc:
            raise BinanceClientError(f"Network connection failed: {exc}")

        return self._handle_response(response)

    def test_connectivity(self) -> bool:
        """
        Ping the testnet to verify the connection is alive.

        Returns:
            True if the testnet is reachable, False otherwise.
        """
        try:
            self.get("/fapi/v1/ping")
            logger.info("Testnet connectivity check: OK")
            return True
        except BinanceClientError as exc:
            logger.error("Testnet connectivity check failed: %s", exc)
            return False
