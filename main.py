"""
trading_bot/main.py

Application entry point.
Run this file directly:
    python main.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
"""

from bot.cli import run

if __name__ == "__main__":
    run()
