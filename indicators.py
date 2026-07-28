"""
All technical indicator calculations used by both signal engines.
Works on a pandas DataFrame with columns: open, high, low, close, volume
"""
import pandas as pd
import numpy as np


def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.fillna(50)


def ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    return df[column].ewm(span=period, adjust=False).mean()


def bollinger_bands(df: pd.DataFrame, period: int = 30, std_dev: float = 2.5):
    middle = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def volume_spike(df: pd.DataFrame, lookback: int = 20, multiplier: float = 1.5) -> pd.Series:
    avg_vol = df["volume"].rolling(window=lookback).mean()
    return df["volume"] > (avg_vol * multiplier)


def swing_lows(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """Returns True where a candle's low is a local minimum (swing low)."""
    lows = df["low"]
    is_swing = (lows == lows.rolling(window=window * 2 + 1, center=True).min())
    return is_swing.fillna(False)


def swing_highs(df: pd.DataFrame, window: int = 5) -> pd.Series:
    highs = df["high"]
    is_swing = (highs == highs.rolling(window=window * 2 + 1, center=True).max())
    return is_swing.fillna(False)


def last_swing_low(df: pd.DataFrame, window: int = 5, lookback_candles: int = 50):
    sw = swing_lows(df, window)
    recent = df.iloc[-lookback_candles:]
    recent_sw = sw.iloc[-lookback_candles:]
    matches = recent.loc[recent_sw]
    if len(matches) == 0:
        return df["low"].iloc[-lookback_candles:].min()
    return matches["low"].iloc[-1]


def last_swing_high(df: pd.DataFrame, window: int = 5, lookback_candles: int = 50):
    sw = swing_highs(df, window)
    recent = df.iloc[-lookback_candles:]
    recent_sw = sw.iloc[-lookback_candles:]
    matches = recent.loc[recent_sw]
    if len(matches) == 0:
        return df["high"].iloc[-lookback_candles:].max()
    return matches["high"].iloc[-1]


def support_resistance_zones(df: pd.DataFrame, window: int = 5, lookback_candles: int = 100, num_zones: int = 3):
    """Rough support/resistance levels from recent swing points, sorted by proximity to current price."""
    sw_low = swing_lows(df, window)
    sw_high = swing_highs(df, window)
    recent = df.iloc[-lookback_candles:]
    supports = sorted(recent.loc[sw_low.iloc[-lookback_candles:], "low"].tolist())
    resistances = sorted(recent.loc[sw_high.iloc[-lookback_candles:], "high"].tolist())
    return supports[-num_zones:] if supports else [], resistances[:num_zones] if resistances else []


def bullish_divergence(df: pd.DataFrame, rsi_series: pd.Series, lookback: int = 30) -> bool:
    """
    Price makes a new (lower) low while RSI makes a higher low -> bullish divergence.
    Simple check comparing the last two swing lows in the lookback window.
    """
    sw = swing_lows(df, window=3)
    recent_idx = df.iloc[-lookback:].index
    sw_recent = sw.loc[sw.index.isin(recent_idx) & sw]
    if len(sw_recent) < 2:
        return False
    idx1, idx2 = sw_recent.index[-2], sw_recent.index[-1]
    price1, price2 = df.loc[idx1, "low"], df.loc[idx2, "low"]
    rsi1, rsi2 = rsi_series.loc[idx1], rsi_series.loc[idx2]
    return bool(price2 < price1 and rsi2 > rsi1)


def bearish_divergence(df: pd.DataFrame, rsi_series: pd.Series, lookback: int = 30) -> bool:
    sw = swing_highs(df, window=3)
    recent_idx = df.iloc[-lookback:].index
    sw_recent = sw.loc[sw.index.isin(recent_idx) & sw]
    if len(sw_recent) < 2:
        return False
    idx1, idx2 = sw_recent.index[-2], sw_recent.index[-1]
    price1, price2 = df.loc[idx1, "high"], df.loc[idx2, "high"]
    rsi1, rsi2 = rsi_series.loc[idx1], rsi_series.loc[idx2]
    return bool(price2 > price1 and rsi2 < rsi1)


def bullish_candle_pattern(df: pd.DataFrame) -> bool:
    """Checks last closed candle for hammer or bullish engulfing pattern."""
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]
    lower_wick = min(last["open"], last["close"]) - last["low"]

    is_hammer = candle_range > 0 and lower_wick > body * 2 and body < candle_range * 0.35

    is_engulfing = (
        prev["close"] < prev["open"] and
        last["close"] > last["open"] and
        last["close"] > prev["open"] and
        last["open"] < prev["close"]
    )
    return bool(is_hammer or is_engulfing)
