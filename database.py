"""
Supabase database interface. Uses Supabase's REST API directly via requests.
"""
import requests
from datetime import datetime, timezone
from config import SUPABASE_URL, SUPABASE_KEY

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

TABLE = "signals"


def _url(path=""):
    return f"{SUPABASE_URL}/rest/v1/{TABLE}{path}"


def insert_signal(signal: dict):
    payload = {
        "symbol": signal["symbol"],
        "signal_type": signal["signal_type"],
        "direction": signal["direction"],
        "entry_price": signal["entry_price"],
        "sl": signal["sl"],
        "tp1": signal["tp1"],
        "tp2": signal.get("tp2"),
        "tp3": signal.get("tp3"),
        "confidence_pct": signal["confidence_pct"],
        "reasons": ", ".join(signal["reasons"]),
        "status": "ACTIVE",
        "result": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = requests.post(_url(), json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_active_signals(signal_type: str = None):
    params = {"status": "eq.ACTIVE"}
    if signal_type:
        params["signal_type"] = f"eq.{signal_type}"
    resp = requests.get(_url(), params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def has_active_signal(symbol: str, signal_type: str) -> bool:
    params = {
        "symbol": f"eq.{symbol}",
        "signal_type": f"eq.{signal_type}",
        "status": "eq.ACTIVE",
    }
    resp = requests.get(_url(), params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return len(resp.json()) > 0


def deactivate_signal(signal_id, result: str):
    payload = {
        "status": "CLOSED",
        "result": result,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }
    params = {"id": f"eq.{signal_id}"}
    resp = requests.patch(_url(), params=params, json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_signals_since(iso_date: str):
    params = {"created_at": f"gte.{iso_date}"}
    resp = requests.get(_url(), params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()
