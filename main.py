"""
Main monitoring loop. Run this continuously on Render as a Background Worker.
"""
import time
import traceback
from datetime import datetime

import data_fetcher as fetcher
import database as db
from signal_engine_1h import analyze_1h
from signal_engine_15m import analyze_15m
from config import TIMEFRAME_1H, TIMEFRAME_15M, SCAN_INTERVAL_SECONDS
from telegram_alert import send_signal

def scan_for_new_signals():
    print(f"[{datetime.utcnow()}] Scanning for new signals...")
    coins = fetcher.get_top_coins()

    for symbol in coins:
        try:
            if not db.has_active_signal(symbol, "1H_BOTTOM_REVERSAL"):
                df_1h = fetcher.get_klines(symbol, TIMEFRAME_1H)
                result = analyze_1h(symbol, df_1h)
                if result:
                    db.insert_signal(result)
                    print(f"  NEW 1H signal: {symbol} {result['direction']} conf={result['confidence_pct']}%")
        except Exception as e:
            print(f"  1H error on {symbol}: {e}")

        try:
            if not db.has_active_signal(symbol, "15M_SUPER_SIGNAL"):
                df_15m = fetcher.get_klines(symbol, TIMEFRAME_15M)
                result = analyze_15m(symbol, df_15m)
                if result:
                    db.insert_signal(result)
                    print(f"  NEW 15M signal: {symbol} {result['direction']} conf={result['confidence_pct']}%")
        except Exception as e:
            print(f"  15M error on {symbol}: {e}")


def check_active_signals():
    print(f"[{datetime.utcnow()}] Checking active signals for SL/TP...")
    active = db.get_active_signals()

    for sig in active:
        try:
            price = fetcher.get_current_price(sig["symbol"])
            direction = sig["direction"]
            is_buy = direction == "BUY"

            sl_hit = (price <= sig["sl"]) if is_buy else (price >= sig["sl"])
            if sl_hit:
                db.deactivate_signal(sig["id"], "SL_HIT")
                print(f"  {sig['symbol']} SL HIT -> deactivated")
                continue

            last_tp = sig.get("tp3") or sig.get("tp1")
            if last_tp:
                tp_hit = (price >= last_tp) if is_buy else (price <= last_tp)
                if tp_hit:
                    db.deactivate_signal(sig["id"], "TP_HIT")
                    print(f"  {sig['symbol']} TP HIT -> deactivated")
        except Exception as e:
            print(f"  Error checking {sig.get('symbol')}: {e}")


def run_forever():
    while True:
        try:
            scan_for_new_signals()
            check_active_signals()
        except Exception:
            traceback.print_exc()
        print(f"Sleeping {SCAN_INTERVAL_SECONDS}s...\n")
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_forever()
