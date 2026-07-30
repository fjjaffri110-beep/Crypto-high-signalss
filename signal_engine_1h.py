"""
Signal Type A: 1H Advanced Smart Money Reversal Signal

Filters:
- RSI Oversold Recovery
- RSI Divergence
- Volume Spike
- Support Zone
- Bullish Candle Pattern
- MACD Cross
- BOS (Break of Structure)
- CHoCH (Change of Character)
- Order Block
- Fair Value Gap
- AI Score System

Signal only if score >= 60
"""

import indicators as ind
from config import RSI_PERIOD, RSI_OVERSOLD, SL_BUFFER_PCT


MIN_AI_SCORE = 60


def analyze_1h(symbol: str, df):

    if len(df) < 100:
        return None


    rsi_series = ind.rsi(df, RSI_PERIOD)
    macd_line, signal_line = ind.macd(df)

    vol_spike = ind.volume_spike(df)

    last_close = df["close"].iloc[-1]
    last_rsi = rsi_series.iloc[-1]
    prev_rsi = rsi_series.iloc[-2]


    score = 0
    reasons = []
    smc = {}


    # RSI Recovery
    if prev_rsi < RSI_OVERSOLD and last_rsi > RSI_OVERSOLD:
        score += 10
        reasons.append("RSI oversold recovery")


    # RSI Divergence
    if ind.bullish_divergence(df, rsi_series):
        score += 15
        reasons.append("Bullish RSI divergence")


    # Volume
    if bool(vol_spike.iloc[-1]):
        score += 10
        reasons.append("Volume spike")


    # Support
    supports, resistances = ind.support_resistance_zones(df)

    if supports:

        nearest_support = min(
            supports,
            key=lambda x: abs(x-last_close)
        )

        if abs(last_close-nearest_support)/last_close < 0.025:
            score += 10
            reasons.append("Near support zone")


    # Candle confirmation
    if ind.bullish_candle_pattern(df):
        score += 10
        reasons.append("Bullish candle confirmation")


    # MACD
    if (
        macd_line.iloc[-2] < signal_line.iloc[-2]
        and
        macd_line.iloc[-1] >= signal_line.iloc[-1]
    ):
        score += 10
        reasons.append("MACD bullish cross")


    # ===== SMC =====

    # BOS
    previous_high = df["high"].iloc[-20:-1].max()

    if last_close > previous_high:
        score += 10
        reasons.append("Break of Structure")
        smc["BOS"] = True
    else:
        smc["BOS"] = False


    # CHoCH
    if (
        df["close"].iloc[-1] >
        df["close"].iloc[-10]
    ):
        score += 5
        reasons.append("CHoCH bullish")
        smc["CHoCH"] = True
    else:
        smc["CHoCH"] = False


    # Fair Value Gap simple check
    if (
        df["low"].iloc[-1] >
        df["high"].iloc[-3]
    ):
        score += 5
        reasons.append("Bullish FVG")
        smc["FVG"] = True
    else:
        smc["FVG"] = False


    # Order Block approximation
    last_red = (
        df["close"].iloc[-2]
        <
        df["open"].iloc[-2]
    )

    if last_red:
        score += 5
        reasons.append("Bullish Order Block")
        smc["Order_Block"] = True
    else:
        smc["Order_Block"] = False



    if score < MIN_AI_SCORE:
        return None



    confidence = min(score,100)


    swing_low = ind.last_swing_low(df)

    sl = swing_low * (1-SL_BUFFER_PCT)


    risk = last_close-sl

    if risk <= 0:
        return None


    tp1 = last_close + risk*2
    tp2 = last_close + risk*3
    tp3 = last_close + risk*4



    return {

        "symbol": symbol,

        "signal_type":
        "1H_SMART_MONEY_REVERSAL",

        "direction":
        "BUY",

        "entry_price":
        round(last_close,8),

        "sl":
        round(sl,8),

        "tp1":
        round(tp1,8),

        "tp2":
        round(tp2,8),

        "tp3":
        round(tp3,8),


        "confidence_pct":
        confidence,


        "score":
        score,


        "smc":
        smc,


        "ai_details":
        {
            "strategy":
            "SMC + Technical Confluence",

            "reasons":
            reasons
        },


        "reasons":
        reasons
    }
