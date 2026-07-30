"""
Supabase database interface.
Stores advanced AI + SMC signal data.
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

        "symbol":
        signal.get("symbol"),


        "signal_type":
        signal.get("signal_type"),


        "direction":
        signal.get("direction"),


        "entry_price":
        signal.get("entry_price"),


        "sl":
        signal.get("sl"),


        "tp1":
        signal.get("tp1"),


        "tp2":
        signal.get("tp2"),


        "tp3":
        signal.get("tp3"),


        "confidence_pct":
        signal.get("confidence_pct"),


        "score":
        signal.get("score"),


        "smc":
        signal.get("smc"),


        "ai_details":
        {
            "score": signal.get("score"),
            "reasons": signal.get("reasons", [])
        },


        "reasons":
        ", ".join(
            signal.get("reasons", [])
        ),


        "status":
        "ACTIVE",


        "result":
        None,


        "created_at":
        datetime.now(
            timezone.utc
        ).isoformat(),

    }


    response = requests.post(
        _url(),
        json=payload,
        headers=HEADERS,
        timeout=15
    )


    response.raise_for_status()

    return response.json()





def get_active_signals(signal_type=None):

    params = {
        "status": "eq.ACTIVE"
    }


    if signal_type:

        params["signal_type"] = (
            f"eq.{signal_type}"
        )


    response = requests.get(
        _url(),
        params=params,
        headers=HEADERS,
        timeout=15
    )


    response.raise_for_status()

    return response.json()





def has_active_signal(symbol: str, signal_type: str):

    params = {

        "symbol":
        f"eq.{symbol}",


        "signal_type":
        f"eq.{signal_type}",


        "status":
        "eq.ACTIVE",
    }


    response = requests.get(
        _url(),
        params=params,
        headers=HEADERS,
        timeout=15
    )


    response.raise_for_status()


    return len(
        response.json()
    ) > 0





def deactivate_signal(signal_id, result: str):

    payload = {

        "status":
        "CLOSED",


        "result":
        result,


        "closed_at":
        datetime.now(
            timezone.utc
        ).isoformat(),

    }


    params = {
        "id":
        f"eq.{signal_id}"
    }


    response = requests.patch(
        _url(),
        params=params,
        json=payload,
        headers=HEADERS,
        timeout=15
    )


    response.raise_for_status()


    return response.json()





def get_signals_since(iso_date: str):

    params = {

        "created_at":
        f"gte.{iso_date}"

    }


    response = requests.get(
        _url(),
        params=params,
        headers=HEADERS,
        timeout=15
    )


    response.raise_for_status()


    return response.json()
