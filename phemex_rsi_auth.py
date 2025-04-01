import os
import time
import requests
import hmac
import hashlib
import json
from datetime import datetime
import numpy as np

# === Phemex Authentifizierung ===
API_KEY = os.environ.get("PHEMEX_API_KEY")
API_SECRET = os.environ.get("PHEMEX_API_SECRET")
BASE_URL = "https://vapi.phemex.com"  # Authentifizierter Zugang

# === OHLC ABRUFEN ===
def get_ohlc_phemex(symbol):
    try:
        timestamp = int(time.time() * 1000)
        path = "/md/kline"
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

        url = f"{BASE_URL}{path}?{query}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "data" in data and "candles" in data["data"]:
            klines = data["data"]["candles"]
            closes = [float(k[4]) for k in klines]
            timestamps = [datetime.fromtimestamp(k[0] / 1000.0) for k in klines]
            return timestamps, closes
        else:
            print(f"⚠️ {symbol}: Keine gültigen Kline-Daten.")
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

# === HAUPTAUSFÜHRUNG ===
if __name__ == "__main__":
    symbol = "BTCUSD"  # ⚠️ Kein "BTCUSDT" bei Phemex!
    print(f"🔍 Abruf von {symbol} über Phemex...")
    timestamps, closes = get_ohlc_phemex(symbol)
    if closes:
        rsi = calculate_rsi(closes)
        if rsi:
            print(f"📈 Aktueller RSI für {symbol}: {rsi[-1]:.2f}")
        else:
            print("⚠️ Nicht genug RSI-Daten.")
    else:
        print(f"⚠️ Keine Schlusskurse für {symbol} erhalten.")
