# === Phemex RSI-Streak-Bot ===

import requests
import time
from datetime import datetime
import numpy as np

# === RSI-Berechnung ===
def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed > 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = [100. - 100. / (1. + rs)]

    for delta in deltas[period:]:
        up_val = max(delta, 0)
        down_val = -min(delta, 0)
        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period
        rs = up / down if down != 0 else 0
        rsi.append(100. - 100. / (1. + rs))
    return rsi

# === OHLC ABRUFEN ===
def get_ohlc_phemex(symbol):
    url = f"https://api.phemex.com/md/kline"
    params = {
        "symbol": symbol,
        "resolution": "14400",  # 4h
        "limit": 100
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if "data" not in data or not data["data"]:
            raise ValueError("Keine Daten erhalten")
        closes = [float(item[4]) for item in data["data"]]  # Schlusskurse
        return closes
    except Exception as e:
        print(f"❌ {symbol} Fehler bei OHLC: {e}")
        return []

# === SYMBOLLISTE LADEN ===
def get_phemex_perpetual_symbols():
    url = "https://api.phemex.com/exchange/public/products"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        symbols = [item['symbol'] for item in data['data'] if item.get('type') == 'Perpetual']
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Laden der Symbole: {e}")
        return []

# === RSI-Streak Check ===
def check_rsi_streak(symbol):
    closes = get_ohlc_phemex(symbol)
    if len(closes) < 20:
        print(f"⚠️ {symbol}: Nicht genug Daten.")
        return

    rsi_values = calculate_rsi(closes)[-4:]
    print(f"📊 {symbol} letzte RSI-Werte: {rsi_values}")
    
    if all(rsi < 30 for rsi in rsi_values):
        print(f"🚀 {symbol}: Möglicher LONG-Setup (4x RSI < 30)")
    elif all(rsi > 70 for rsi in rsi_values):
        print(f"🔻 {symbol}: Möglicher SHORT-Setup (4x RSI > 70)")
    else:
        print(f"✅ {symbol}: Kein RSI-Signal.")

# === MAIN ===
print("🔍 RSI-Streak-Check für Phemex Perpetuals...")
symbols = get_phemex_perpetual_symbols()
for symbol in symbols:
    check_rsi_streak(symbol)
    time.sleep(1.5)  # Phemex API nicht überlasten
