"""
Advanced Technical + Smart Money Concepts Indicators

DataFrame required columns:
open, high, low, close, volume
"""

import pandas as pd
import numpy as np


# =========================
# BASIC INDICATORS
# =========================

def rsi(df: pd.DataFrame, period: int = 14):
    delta = df["close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    result = 100 - (100 / (1 + rs))

    return result.fillna(50)


def ema(df: pd.DataFrame, period: int, column="close"):
    return df[column].ewm(
        span=period,
        adjust=False
    ).mean()


def bollinger_bands(df, period=30, std_dev=2.5):

    middle = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return upper, middle, lower


def macd(df, fast=12, slow=26, signal=9):

    fast_ema = ema(df, fast)
    slow_ema = ema(df, slow)

    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(
        span=signal,
        adjust=False
    ).mean()

    return macd_line, signal_line



# =========================
# VOLUME INDICATORS
# =========================


def volume_spike(df, lookback=20, multiplier=1.5):

    avg_volume = df["volume"].rolling(
        lookback
    ).mean()

    return df["volume"] > (
        avg_volume * multiplier
    )



def obv(df):

    direction = np.where(
        df["close"] > df["close"].shift(1),
        1,
        -1
    )

    return (
        df["volume"] * direction
    ).cumsum()



# =========================
# ATR / ADX / VWAP
# =========================


def atr(df, period=14):

    high_low = df["high"] - df["low"]

    high_close = abs(
        df["high"] - df["close"].shift()
    )

    low_close = abs(
        df["low"] - df["close"].shift()
    )

    tr = pd.concat(
        [
            high_low,
            high_close,
            low_close
        ],
        axis=1
    ).max(axis=1)

    return tr.rolling(period).mean()



def vwap(df):

    price = (
        df["high"]
        + df["low"]
        + df["close"]
    ) / 3

    return (
        price * df["volume"]
    ).cumsum() / df["volume"].cumsum()



def adx(df, period=14):

    plus_dm = df["high"].diff()

    minus_dm = (
        -df["low"].diff()
    )

    plus_dm[
        plus_dm < 0
    ] = 0

    minus_dm[
        minus_dm < 0
    ] = 0


    tr = atr(df, period)

    plus_di = (
        100 *
        plus_dm.rolling(period).mean()
        /
        tr
    )

    minus_di = (
        100 *
        minus_dm.rolling(period).mean()
        /
        tr
    )


    dx = (
        abs(plus_di - minus_di)
        /
        (plus_di + minus_di)
    ) * 100


    return dx.rolling(period).mean()



# =========================
# SWING STRUCTURE
# =========================


def swing_lows(df, window=5):

    return (
        df["low"]
        ==
        df["low"]
        .rolling(
            window*2+1,
            center=True
        )
        .min()
    ).fillna(False)



def swing_highs(df, window=5):

    return (
        df["high"]
        ==
        df["high"]
        .rolling(
            window*2+1,
            center=True
        )
        .max()
    ).fillna(False)



def last_swing_low(df):

    swings = swing_lows(df)

    points = df.loc[swings]

    if len(points):

        return points["low"].iloc[-1]

    return df["low"].iloc[-50:].min()



def last_swing_high(df):

    swings = swing_highs(df)

    points = df.loc[swings]

    if len(points):

        return points["high"].iloc[-1]

    return df["high"].iloc[-50:].max()



# =========================
# RSI DIVERGENCE
# =========================


def bullish_divergence(df, rsi_series):

    lows = swing_lows(df)

    points = df[lows]

    if len(points) < 2:
        return False


    p1 = points["low"].iloc[-2]
    p2 = points["low"].iloc[-1]


    r1 = rsi_series.loc[
        points.index[-2]
    ]

    r2 = rsi_series.loc[
        points.index[-1]
    ]


    return (
        p2 < p1
        and
        r2 > r1
    )



def bearish_divergence(df, rsi_series):

    highs = swing_highs(df)

    points = df[highs]

    if len(points) < 2:
        return False


    p1 = points["high"].iloc[-2]
    p2 = points["high"].iloc[-1]


    r1 = rsi_series.loc[
        points.index[-2]
    ]

    r2 = rsi_series.loc[
        points.index[-1]
    ]


    return (
        p2 > p1
        and
        r2 < r1
    )



# =========================
# SMART MONEY CONCEPTS
# =========================


def detect_bos(df):

    last_high = last_swing_high(df)

    last_close = df["close"].iloc[-1]


    return bool(
        last_close > last_high
    )



def detect_choch(df):

    last_low = last_swing_low(df)

    last_close = df["close"].iloc[-1]


    return bool(
        last_close < last_low
    )



def detect_order_block(df):

    last = df.iloc[-2]

    current = df.iloc[-1]


    bullish = (
        last["close"] < last["open"]
        and
        current["close"] > last["high"]
    )


    bearish = (
        last["close"] > last["open"]
        and
        current["close"] < last["low"]
    )


    return {
        "bullish": bool(bullish),
        "bearish": bool(bearish)
    }



def detect_fvg(df):

    if len(df) < 3:
        return False


    c1 = df.iloc[-3]
    c3 = df.iloc[-1]


    bullish_gap = (
        c1["high"] < c3["low"]
    )


    bearish_gap = (
        c1["low"] > c3["high"]
    )


    return bool(
        bullish_gap or bearish_gap
    )



def detect_liquidity_sweep(df):

    low_sweep = (
        df["low"].iloc[-1]
        <
        df["low"].iloc[-10:-1].min()
    )


    high_sweep = (
        df["high"].iloc[-1]
        >
        df["high"].iloc[-10:-1].max()
    )


    return {
        "bullish": bool(low_sweep),
        "bearish": bool(high_sweep)
    }



def premium_discount_zone(df):

    high = df["high"].iloc[-50:].max()
    low = df["low"].iloc[-50:].min()

    mid = (
        high + low
    ) / 2


    price = df["close"].iloc[-1]


    return {
        "premium": price > mid,
        "discount": price < mid,
        "equilibrium": price == mid
    }



# =========================
# CANDLE PATTERN
# =========================


def bullish_candle_pattern(df):

    last = df.iloc[-1]
    prev = df.iloc[-2]


    body = abs(
        last["close"]
        -
        last["open"]
    )


    candle_range = (
        last["high"]
        -
        last["low"]
    )


    lower_wick = (
        min(
            last["open"],
            last["close"]
        )
        -
        last["low"]
    )


    hammer = (
        candle_range > 0
        and
        lower_wick > body*2
    )


    engulfing = (
        prev["close"] < prev["open"]
        and
        last["close"] > last["open"]
        and
        last["close"] > prev["open"]
    )


    return bool(
        hammer or engulfing
    )
