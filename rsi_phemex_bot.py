import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# === PHEMEX RSI-BOT ===
PH_ENDPOINT = "https://api.phemex.com/md/kline"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Coin-Auswahl ===
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT",
    "AVAXUSDT", "LINKUSDT", "UNIUSDT", "AAVEUSDT"
]

# === RSI ===
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# === Telegram ===
def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

# === Daten holen ===
def get_ohlc_phemex(symbol):
    ph_symbol = symbol + ".perp"
    params = {
        "symbol": ph_symbol,
        "resolution": "4h",
        "limit": 100
    }
    try:
        res = requests.get(PH_ENDPOINT, params=params)
        res.raise_for_status()
        data = res.json()
        rows = data.get("data")
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=["ts","o","h","l","c","v"])
        df["timestamp"] = pd.to_datetime(df["ts"], unit="ms")
        df["close"] = df["c"].astype(float)
        return df[["timestamp", "close"]]
    except Exception as e:
        print(f"❌ {symbol} Fehler bei OHLC: {e}")
        return pd.DataFrame()

# === Analyse ===
def check_rsi_streak(symbol):
    df = get_ohlc_phemex(symbol)
    if df.empty or len(df) < 20:
        print(f"⚠️ {symbol}: Nicht genug Daten.")
        return

    df["rsi"] = compute_rsi(df["close"])
    recent_rsi = df[["timestamp", "rsi"]].dropna().tail(4)

    if recent_rsi.empty:
        print(f"⚠️ {symbol}: RSI-Daten fehlen.")
        return

    rsi_values = recent_rsi["rsi"].tolist()
    streak_under = sum(r < 30 for r in rsi_values)
    streak_over = sum(r > 70 for r in rsi_values)
    latest_time = recent_rsi["timestamp"].iloc[-1]
    latest_rsi = rsi_values[-1]

    print(f"📊 {symbol} letzte 4h RSI: {[round(r,2) for r in rsi_values]}")

    if streak_under == 4:
        send_telegram_message(f"🔻 {symbol}: RSI < 30 seit 4x 4h (zuletzt {latest_rsi:.2f})\n📅 {latest_time}\n➡️ Long Setup möglich")
    elif streak_over == 4:
        send_telegram_message(f"🔺 {symbol}: RSI > 70 seit 4x 4h (zuletzt {latest_rsi:.2f})\n📅 {latest_time}\n➡️ Short Setup denkbar")
    else:
        print(f"✅ {symbol}: Kein RSI-Streak-Signal.")

# === MAIN ===
def main():
    print("\n🔍 RSI-Streak-Analyse (Phemex 4h):\n")
    for symbol in SYMBOLS:
        check_rsi_streak(symbol)
        time.sleep(1.2)  # Rate Limit Schutz

if __name__ == "__main__":
    main()
