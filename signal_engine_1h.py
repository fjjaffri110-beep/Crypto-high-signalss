"""
Signal Type A: 1-Hour Bottom Reversal Signal
Confluence of: RSI oversold+recovery, Bullish Divergence, Volume Spike,
Support proximity, Bullish Candle Pattern, MACD bullish cross.
"""
import indicators as ind
from config import RSI_PERIOD, RSI_OVERSOLD, MIN_CONFLUENCE_SCORE, SL_BUFFER_PCT


def analyze_1h(symbol: str, df):
    if len(df) < 60:
        return None

    rsi_series = ind.rsi(df, RSI_PERIOD)
    macd_line, signal_line = ind.macd(df)
    vol_spike = ind.volume_spike(df)
    supports, resistances = ind.support_resistance_zones(df)

    last_close = df["close"].iloc[-1]
    last_rsi = rsi_series.iloc[-1]
    prev_rsi = rsi_series.iloc[-2]

    score = 0
    reasons = []

    if prev_rsi < RSI_OVERSOLD and last_rsi >= RSI_OVERSOLD:
        score += 1
        reasons.append("RSI recovering from oversold")

    if ind.bullish_divergence(df, rsi_series):
        score += 1
        reasons.append("Bullish RSI divergence")

    if bool(vol_spike.iloc[-1]):
        score += 1
        reasons.append("Volume spike")

    if supports:
        nearest_support = min(supports, key=lambda s: abs(s - last_close))
        if abs(last_close - nearest_support) / last_close < 0.02:
            score += 1
            reasons.append("Price near support zone")

    if ind.bullish_candle_pattern(df):
        score += 1
        reasons.append("Bullish candle pattern")

    if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] >= signal_line.iloc[-1]:
        score += 1
        reasons.append("MACD bullish cross")

    if score < MIN_CONFLUENCE_SCORE:
        return None

    confidence_pct = round((score / 6) * 100, 1)
    swing_low = ind.last_swing_low(df)
    sl = swing_low * (1 - SL_BUFFER_PCT)

    if len(resistances) >= 3:
        tps = resistances[:3]
    else:
        tps = [last_close * (1 + pct) for pct in (0.05, 0.10, 0.18)]

    return {
        "symbol": symbol,
        "signal_type": "1H_BOTTOM_REVERSAL",
        "direction": "BUY",
        "entry_price": last_close,
        "sl": round(sl, 8),
        "tp1": round(tps[0], 8),
        "tp2": round(tps[1], 8),
        "tp3": round(tps[2], 8),
        "confidence_pct": confidence_pct,
        "score": score,
        "reasons": reasons,
    }
