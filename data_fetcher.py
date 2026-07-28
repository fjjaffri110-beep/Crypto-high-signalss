"""
Fetches live market data from Binance's public API (no API key needed for market data).
"""
import requests
import pandas as pd
from config import BINANCE_BASE_URL, TOP_N_COINS, CANDLE_LIMIT


def get_top_coins(n: int = TOP_N_COINS):
    """Returns top N USDT trading pairs by 24h quote volume."""
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/24hr"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    usdt_pairs = [d for d in data if d["symbol"].endswith("USDT") and "UP" not in d["symbol"] and "DOWN" not in d["symbol"]]
    sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True)
    return [p["symbol"] for p in sorted_pairs[:n]]


def get_klines(symbol: str, interval: str, limit: int = CANDLE_LIMIT) -> pd.DataFrame:
    """Fetch OHLCV candles for a symbol/interval and return as a DataFrame."""
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    raw = resp.json()

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    return df[["open", "high", "low", "close", "volume"]]


def get_current_price(symbol: str) -> float:
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/price"
    resp = requests.get(url, params={"symbol": symbol}, timeout=10)
    resp.raise_for_status()
    return float(resp.json()["price"])
