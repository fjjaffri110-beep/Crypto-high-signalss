"""
Signal Type C
5 Minute EMA400 + Bollinger Reversal

BUY
- Fresh EMA400 Bullish Cross
- EMA400 Slope Up
- 2 Consecutive Green Candles
- Both candles touch BB Upper Band

SELL
- Fresh EMA400 Bearish Cross
- EMA400 Slope Down
- 2 Consecutive Red Candles
- Both candles touch BB Lower Band
"""

import indicators as ind

from config import RISK_REWARD_RATIO

EMA_PERIOD = 400
BB_PERIOD = 25
BB_STD = 3.0

MIN_SCORE = 70


def analyze_5m(symbol, df):

    if len(df) < EMA_PERIOD + 30:
        return None

    ema = ind.ema(df, EMA_PERIOD)

    bb_upper, bb_middle, bb_lower = ind.bollinger_bands(
        df,
        BB_PERIOD,
        BB_STD
    )

    close = df["close"]
    open_ = df["open"]
    high = df["high"]
    low = df["low"]

    last = len(df) - 1

    score = 0
    reasons = []

    direction = None

    # =====================================
    # Fresh Bullish Cross
    # =====================================

    bullish_cross = (
        close.iloc[last - 1] < ema.iloc[last - 1]
        and
        close.iloc[last] > ema.iloc[last]
    )

    # =====================================
    # Fresh Bearish Cross
    # =====================================

    bearish_cross = (
        close.iloc[last - 1] > ema.iloc[last - 1]
        and
        close.iloc[last] < ema.iloc[last]
    )

    # =====================================
    # Duplicate Filter (20 candles)
    # =====================================

    fresh = True

    for i in range(max(1, last - 20), last):

        if bullish_cross:

            if (
                close.iloc[i - 1] < ema.iloc[i - 1]
                and
                close.iloc[i] > ema.iloc[i]
            ):
                fresh = False
                break

        if bearish_cross:

            if (
                close.iloc[i - 1] > ema.iloc[i - 1]
                and
                close.iloc[i] < ema.iloc[i]
            ):
                fresh = False
                break

    if not fresh:
        return None

    # =====================================
    # BUY SETUP
    # =====================================

    if bullish_cross:

        direction = "BUY"

        score += 20
        reasons.append("Fresh EMA400 Bullish Cross")

        if ema.iloc[last] > ema.iloc[last - 5]:

            score += 10
            reasons.append("EMA400 Slope Up")

        green1 = close.iloc[last - 1] > open_.iloc[last - 1]
        green2 = close.iloc[last] > open_.iloc[last]

        if green1 and green2:

            score += 20
            reasons.append("Two Green Candles")

        touch1 = high.iloc[last - 1] >= bb_upper.iloc[last - 1]
        touch2 = high.iloc[last] >= bb_upper.iloc[last]

        if touch1 and touch2:

            score += 20
            reasons.append("Upper Band Touch")

    # =====================================
    # SELL SETUP
    # =====================================

    elif bearish_cross:

        direction = "SHORT"

        score += 20
        reasons.append("Fresh EMA400 Bearish Cross")

        if ema.iloc[last] < ema.iloc[last - 5]:

            score += 10
            reasons.append("EMA400 Slope Down")

        red1 = close.iloc[last - 1] < open_.iloc[last - 1]
        red2 = close.iloc[last] < open_.iloc[last]

        if red1 and red2:

            score += 20
            reasons.append("Two Red Candles")

        touch1 = low.iloc[last - 1] <= bb_lower.iloc[last - 1]
        touch2 = low.iloc[last] <= bb_lower.iloc[last]

        if touch1 and touch2:

            score += 20
            reasons.append("Lower Band Touch")

    else:

        return None    # =====================================
    # SCORE FILTER
    # =====================================

    if score < MIN_SCORE:
        return None

    confidence = min(score, 100)

    # =====================================
    # STOP LOSS / TAKE PROFIT
    # =====================================

    if direction == "BUY":

        sl = ind.last_swing_low(df)

        risk = close.iloc[last] - sl

        if risk <= 0:
            return None

        tp1 = close.iloc[last] + (risk * 2)
        tp2 = close.iloc[last] + (risk * 3)
        tp3 = close.iloc[last] + (risk * RISK_REWARD_RATIO)

    else:

        sl = ind.last_swing_high(df)

        risk = sl - close.iloc[last]

        if risk <= 0:
            return None

        tp1 = close.iloc[last] - (risk * 2)
        tp2 = close.iloc[last] - (risk * 3)
        tp3 = close.iloc[last] - (risk * RISK_REWARD_RATIO)

    # =====================================
    # RETURN SIGNAL
    # =====================================

    return {

        "symbol": symbol,

        "signal_type":
        "5M_EMA400_BB_REVERSAL",

        "direction":
        direction,

        "entry_price":
        round(close.iloc[last], 8),

        "sl":
        round(sl, 8),

        "tp1":
        round(tp1, 8),

        "tp2":
        round(tp2, 8),

        "tp3":
        round(tp3, 8),

        "confidence_pct":
        confidence,

        "score":
        score,

        "reasons":
        reasons
    }
