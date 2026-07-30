"""
Telegram alert sender
"""

import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send_signal(message: str):

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }

        response = requests.post(
            url,
            data=payload,
            timeout=10
        )

        response.raise_for_status()

        print("Telegram message sent")

    except Exception as e:
        print("Telegram error:", e)
