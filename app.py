"""
Dashboard web app.
"""

from flask import Flask, render_template
from datetime import datetime, timedelta, timezone

import database as db

app = Flask(__name__)


def compute_stats(signal_type=None):

    week_ago = (
        datetime.now(timezone.utc)
        - timedelta(days=7)
    ).isoformat()

    signals = db.get_signals_since(week_ago)

    if signal_type:
        signals = [
            s for s in signals
            if s.get("signal_type") == signal_type
        ]

    total = len(signals)

    sl_hits = len(
        [s for s in signals if s.get("result") == "SL_HIT"]
    )

    tp_hits = len(
        [s for s in signals if s.get("result") == "TP_HIT"]
    )

    active = len(
        [s for s in signals if s.get("status") == "ACTIVE"]
    )

    closed = sl_hits + tp_hits

    win_ratio = (
        round((tp_hits / closed) * 100, 1)
        if closed > 0
        else 0.0
    )

    return {
        "total": total,
        "sl_hits": sl_hits,
        "tp_hits": tp_hits,
        "active": active,
        "win_ratio": win_ratio,
        "signals": sorted(
            signals,
            key=lambda s: s.get("created_at", ""),
            reverse=True,
        ),
    }


@app.route("/")
def dashboard():

    overall = compute_stats()

    # OLD STRATEGIES
    old_1h = compute_stats("1H_BOTTOM_REVERSAL")
    old_15m = compute_stats("15M_SUPER_SIGNAL")

    # NEW STRATEGIES
    new_1h = compute_stats("1H_SMART_MONEY_REVERSAL")
    new_15m = compute_stats("15M_SUPER_SIGNAL_NEW")

    return render_template(
        "dashboard.html",
        overall=overall,
        old_1h=old_1h,
        old_15m=old_15m,
        new_1h=new_1h,
        new_15m=new_15m,
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )
