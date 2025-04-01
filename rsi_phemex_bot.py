import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# === TELEGRAM KONFIGURATION ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === SYMBOLLISTE VON PHEMEX (gültige Perpetuals) ===
SYMBOLS = [
    "BTCUSD", "ETHUSD", "XRPUSD", "LINKUSD", "ADAUSD",
    "DOTUSD", "UNIUSD", "LTCUSD", "BCHUSD", "AVAXUSD"
]

# === Phemex API Endpoint ===
PH_ENDPOINT = "https://api.phemex.com/md/kline"

# === RSI BERECHNUNG ===
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# === TELEGRAM SENDEN ===
def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram-Fehler: {e}")

# === OHLC ABRUFEN ===
def get_ohlc_phemex(symbol):
    params = {
        "symbol": symbol,
        "resolution": "14400",  # 4h in Sekunden
        "limit": 100
    }
    try:
        res = requests.get(PH_ENDPOINT, params=params)
        res.raise_for_status()
        data = res.json().get("data")
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data, columns=["ts","o","h","l","c","v"])
        df["timestamp"] = pd.to_datetime(df["ts"], unit="ms")
        df["close"] = df["c"].astype(float)
        return df[["timestamp", "close"]]
    except Exception as e:
        print(f"❌ {symbol} Fehler bei OHLC: {e}")
        return pd.DataFrame()

# === RSI ANALYSE ===
def check_rsi_streak(symbol):
    df = get_ohlc_phemex(symbol)
    if df.empty or len(df) < 20:
        print(f"⚠️ {symbol}: Nicht genug Daten.")
        return

    df["rsi"] = compute_rsi(df["close"])
    recent = df.dropna().tail(4)

    if recent.empty:
        print(f"⚠️ {symbol}: Keine RSI-Daten.")
        return

    rsi_vals = recent["rsi"].tolist()
    streak_under = sum(r < 30 for r in rsi_vals)
    streak_over = sum(r > 70 for r in rsi_vals)
    latest_ts = recent["timestamp"].iloc[-1]
    latest_rsi = rsi_vals[-1]

    print(f"📊 {symbol} RSI-Werte: {[round(r, 2) for r in rsi_vals]}")

    if streak_under == 4:
        send_telegram_message(f"🔻 {symbol}: RSI < 30 seit 4x 4h\n📅 {latest_ts}\n📈 Long Setup möglich")
    elif streak_over == 4:
        send_telegram_message(f"🔺 {symbol}: RSI > 70 seit 4x 4h\n📅 {latest_ts}\n📉 Short Setup denkbar")
    else:
        print(f"✅ {symbol}: Kein RSI-Streak-Signal.")

# === MAIN ===
def main():
    print("\n🔍 RSI-Streak-Check für Phemex-Perpetuals:\n")
    for sym in SYMBOLS:
        check_rsi_streak(sym)
        time.sleep(1.1)

if __name__ == "__main__":
    main()
