import os
import time
import requests
import hmac
import hashlib
import base64
import json
from datetime import datetime
import numpy as np

# === Phemex Authentifizierung ===
API_KEY = os.environ.get("PHEMEX_API_KEY")
API_SECRET = os.environ.get("PHEMEX_API_SECRET")

# === OHLC ABRUFEN ===
def get_ohlc_phemex(symbol):
    try:
        timestamp = int(time.time() * 1000)
        path = f"/md/kline"
        query = f"symbol={symbol}&resolution=14400&limit=100"
        message = f"{path}{timestamp}{query}"
        signature = hmac.new(
            API_SECRET.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "x-phemex-access-token": API_KEY,
            "x-phemex-request-expiry": str(timestamp),
            "x-phemex-request-signature": signature
        }

        url = f"https://api.phemex.com{path}?{query}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "data" in data:
            klines = data["data"]["rows"]
            closes = [float(k[4]) for k in klines]
            timestamps = [datetime.fromtimestamp(k[0] / 1000.0) for k in klines]
            return timestamps, closes
        else:
            print(f"⚠️ {symbol}: Keine Daten vorhanden.")
            return [], []
    except Exception as e:
        print(f"❌ {symbol} Fehler bei OHLC: {e}")
        return [], []

# === RSI-BERECHNUNG ===
def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return []

    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed > 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = [100. - 100. / (1. + rs)]

    for delta in deltas[period:]:
        upval = max(delta, 0)
        downval = -min(delta, 0)
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi.append(100. - 100. / (1. + rs))

    return rsi

# === BEISPIEL ===
if __name__ == "__main__":
    symbol = "BTCUSD"
    print(f"🔍 Abruf von {symbol}...")
    timestamps, closes = get_ohlc_phemex(symbol)
    if closes:
        rsi = calculate_rsi(closes)
        print(f"📈 Aktueller RSI für {symbol}: {rsi[-1]:.2f}" if rsi else "⚠️ Nicht genug RSI-Daten.")
