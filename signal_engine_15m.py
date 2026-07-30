"""
Signal Type B: Advanced 15-Minute SMC AI Signal Engine

Base Trigger:
- Bollinger Middle Line Cross EMA800 = BUY
- Bollinger Upper Line Cross EMA800 = SHORT

AI Score:
SMC              35
Trend            20
Momentum         15
Volume           15
Entry            15
Total            100

Minimum Score:
Below 60 = Ignore
"""

import indicators as ind

from config import (
    EMA_PERIOD,
    BB_PERIOD,
    BB_STD_DEV,
    RISK_REWARD_RATIO
)



MIN_SCORE = 60



def analyze_15m(symbol: str, df):

    if len(df) < EMA_PERIOD + 50:
        return None


    # Indicators

    ema800 = ind.ema(df, EMA_PERIOD)

    bb_upper, bb_middle, bb_lower = ind.bollinger_bands(
        df,
        BB_PERIOD,
        BB_STD_DEV
    )

    rsi_series = ind.rsi(df)

    volume = ind.volume_spike(df)

    adx_series = ind.adx(df)

    vwap_series = ind.vwap(df)


    close = df["close"].iloc[-1]



    # Base Trigger

    buy_trigger = (
        bb_middle.iloc[-2] < ema800.iloc[-2]
        and
        bb_middle.iloc[-1] >= ema800.iloc[-1]
    )


    short_trigger = (
        bb_upper.iloc[-2] > ema800.iloc[-2]
        and
        bb_upper.iloc[-1] <= ema800.iloc[-1]
    )



    if buy_trigger:

        return generate_signal(
            symbol,
            "BUY",
            df,
            rsi_series,
            volume,
            adx_series,
            vwap_series,
            close
        )


    if short_trigger:

        return generate_signal(
            symbol,
            "SHORT",
            df,
            rsi_series,
            volume,
            adx_series,
            vwap_series,
            close
        )


    return None





def generate_signal(
    symbol,
    direction,
    df,
    rsi,
    volume,
    adx,
    vwap,
    entry
):

    score = 0

    reasons = []

    smc_data = {}



    # =====================
    # SMC SCORE 35
    # =====================


    bos = ind.detect_bos(df)

    choch = ind.detect_choch(df)

    ob = ind.detect_order_block(df)

    fvg = ind.detect_fvg(df)

    liquidity = ind.detect_liquidity_sweep(df)



    smc_score = 0



    if direction == "BUY":

        if bos:
            smc_score += 10
            reasons.append("Bullish BOS")


        if choch:
            smc_score += 10
            reasons.append("CHoCH detected")


        if ob["bullish"]:
            smc_score += 8
            reasons.append("Bullish Order Block")


        if fvg:
            smc_score += 4
            reasons.append("FVG detected")


        if liquidity["bullish"]:
            smc_score += 3
            reasons.append("Liquidity sweep")



    else:

        if bos:
            smc_score += 10
            reasons.append("Structure break")


        if choch:
            smc_score += 10
            reasons.append("CHoCH detected")


        if ob["bearish"]:
            smc_score += 8
            reasons.append("Bearish Order Block")


        if fvg:
            smc_score += 4
            reasons.append("FVG detected")


        if liquidity["bearish"]:
            smc_score += 3
            reasons.append("Liquidity sweep")



    score += min(smc_score,35)



    smc_data = {
        "BOS": bos,
        "CHoCH": choch,
        "Order_Block": ob,
        "FVG": fvg,
        "Liquidity": liquidity
    }




    # =====================
    # TREND SCORE 20
    # =====================


    trend_score = 0


    if direction == "BUY":

        if entry > vwap.iloc[-1]:
            trend_score += 10
            reasons.append("Above VWAP")


    else:

        if entry < vwap.iloc[-1]:
            trend_score += 10
            reasons.append("Below VWAP")



    if adx.iloc[-1] > 20:

        trend_score += 10
        reasons.append("Strong trend ADX")



    score += trend_score




    # =====================
    # MOMENTUM SCORE 15
    # =====================


    momentum = 0


    if direction == "BUY":

        if 30 <= rsi.iloc[-1] <= 55:
            momentum += 8
            reasons.append("RSI recovery")


        if ind.bullish_divergence(df,rsi):
            momentum += 7
            reasons.append("Bullish divergence")



    else:

        if 45 <= rsi.iloc[-1] <= 70:
            momentum += 8
            reasons.append("RSI rejection")


        if ind.bearish_divergence(df,rsi):
            momentum += 7
            reasons.append("Bearish divergence")



    score += momentum




    # =====================
    # VOLUME SCORE 15
    # =====================


    if bool(volume.iloc[-1]):

        score += 15
        reasons.append("Volume spike")



    # =====================
    # ENTRY SCORE 15
    # =====================


    if ind.bullish_candle_pattern(df) and direction=="BUY":

        score += 15
        reasons.append("Bullish candle confirmation")


    elif direction=="SHORT":

        score += 10
        reasons.append("Short entry confirmation")



    # =====================
    # FILTER
    # =====================


    if score < MIN_SCORE:

        return None



    # Risk

    atr = ind.atr(df).iloc[-1]


    if direction=="BUY":

        sl = min(
            ind.last_swing_low(df),
            entry - atr
        )

        risk = entry-sl

        tp1 = entry + risk*2
        tp2 = entry + risk*3
        tp3 = entry + risk*4



    else:

        sl = max(
            ind.last_swing_high(df),
            entry + atr
        )

        risk = sl-entry

        tp1 = entry - risk*2
        tp2 = entry - risk*3
        tp3 = entry - risk*4




    return {

        "symbol":symbol,

        "signal_type":
        "15M_SMC_AI_SIGNAL",

        "direction":direction,

        "entry_price":
        round(entry,8),

        "sl":
        round(sl,8),

        "tp1":
        round(tp1,8),

        "tp2":
        round(tp2,8),

        "tp3":
        round(tp3,8),

        "confidence_pct":
        round(score,1),

        "score":
        score,

        "smc":
        smc_data,

        "reasons":
        reasons
    }
