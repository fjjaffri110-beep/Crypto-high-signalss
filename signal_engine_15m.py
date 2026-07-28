"""
Signal Type B: 15-Minute "Super Signal"
Base trigger: Bollinger middle line crosses EMA800 (buy) / BB upper line crosses EMA800 (short)
Confirmations: RSI zone, Divergence, Volume Spike
SL: last swing low/high, Target: 1:4 risk-reward
"""
import indicators as ind
from config import EMA_PERIOD, BB_PERIOD, BB_STD_DEV, RISK_REWARD_RATIO, MIN_SUPER_SIGNAL_SCORE


def analyze_15m(symbol: str, df):
    if len(df) < EMA_PERIOD + 5:
        return None

    ema800 = ind.ema(df, EMA_PERIOD)
    bb_upper, bb_middle, bb_lower = ind.bollinger_bands(df, BB_PERIOD, BB_STD_DEV)
    rsi_series = ind.rsi(df)
    vol_spike = ind.volume_spike(df)

    last_close = df["close"].iloc[-1]
    last_rsi = rsi_series.iloc[-1]

    mid_prev, mid_now = bb_middle.iloc[-2], bb_middle.iloc[-1]
    ema_prev, ema_now = ema800.iloc[-2], ema800.iloc[-1]
    buy_base_trigger = mid_prev < ema_prev and mid_now >= ema_now

    up_prev, up_now = bb_upper.iloc[-2], bb_upper.iloc[-1]
    short_base_trigger = up_prev > ema_prev and up_now <= ema_now

    if buy_base_trigger:
        score = 1
        reasons = ["BB middle line crossed EMA800 upside"]
        if 30 <= last_rsi <= 50:
            score += 1
            reasons.append("RSI in bullish recovery zone (30-50)")
        if ind.bullish_divergence(df, rsi_series):
            score += 1
            reasons.append("Bullish divergence")
        if bool(vol_spike.iloc[-1]):
            score += 1
            reasons.append("Volume spike")

        if score < MIN_SUPER_SIGNAL_SCORE:
            return None

        swing_low = ind.last_swing_low(df)
        sl = swing_low
        risk = last_close - sl
        if risk <= 0:
            return None
        tp = last_close + (risk * RISK_REWARD_RATIO)

        return _build_result(symbol, "BUY", last_close, sl, tp, score, reasons)

    if short_base_trigger:
        score = 1
        reasons = ["BB upper line crossed EMA800 downside"]
        if 50 <= last_rsi <= 70:
            score += 1
            reasons.append("RSI in bearish rejection zone (50-70)")
        if ind.bearish_divergence(df, rsi_series):
            score += 1
            reasons.append("Bearish divergence")
        if bool(vol_spike.iloc[-1]):
            score += 1
            reasons.append("Volume spike")

        if score < MIN_SUPER_SIGNAL_SCORE:
            return None

        swing_high = ind.last_swing_high(df)
        sl = swing_high
        risk = sl - last_close
        if risk <= 0:
            return None
        tp = last_close - (risk * RISK_REWARD_RATIO)

        return _build_result(symbol, "SHORT", last_close, sl, tp, score, reasons)

    return None


def _build_result(symbol, direction, entry, sl, tp, score, reasons):
    confidence_pct = round((score / 4) * 100, 1)
    return {
        "symbol": symbol,
        "signal_type": "15M_SUPER_SIGNAL",
        "direction": direction,
        "entry_price": round(entry, 8),
        "sl": round(sl, 8),
        "tp1": round(tp, 8),
        "tp2": None,
        "tp3": None,
        "confidence_pct": confidence_pct,
        "score": score,
        "reasons": reasons,
    }
