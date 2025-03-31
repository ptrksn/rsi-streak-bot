import os
import time
import requests
import pandas as pd
import numpy as np
from collections import deque

# === ENV VARS ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")

# === CMC Top 50 Symbols ===
def get_top_50_cmc_symbols():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {
        "start": "1",
        "limit": "50",
        "convert": "USDT",
        "sort": "volume_24h"
    }
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        symbols = [coin["symbol"] + "USDT" for coin in data["data"]]
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der CMC-Daten: {e}")
        return []

# === RSI berechnen ===
def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# === Binance OHLC abrufen ===
def get_4h_rsi(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "4h", "limit": 100}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        closes = [float(c[4]) for c in data]
        df = pd.DataFrame({"close": closes})
        df["rsi"] = compute_rsi(df["close"])
        return df["rsi"].dropna().iloc[-1]
    except Exception as e:
        print(f"❌ {symbol} Fehler bei RSI: {e}")
        return None

# === Telegram Push ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram-Fehler: {e}")

# === State speichern ===
def get_rsi_history(symbol):
    path = f"rsi_{symbol}.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            values = f.read().strip().split(",")
            return deque([float(v) for v in values if v], maxlen=4)
    return deque(maxlen=4)

def save_rsi_history(symbol, rsi_history):
    with open(f"rsi_{symbol}.txt", "w") as f:
        f.write(",".join([str(r) for r in rsi_history]))

def get_state(symbol):
    path = f"state_{symbol}.txt"
    return open(path).read().strip() if os.path.exists(path) else "neutral"

def set_state(symbol, state):
    with open(f"state_{symbol}.txt", "w") as f:
        f.write(state)

# === RSI-Streak prüfen ===
def check_rsi_streak(symbol):
    current_rsi = get_4h_rsi(symbol)
    if current_rsi is None:
        return

    print(f"📊 {symbol} aktueller RSI: {current_rsi:.2f}")
    rsi_history = get_rsi_history(symbol)
    rsi_history.append(current_rsi)
    save_rsi_history(symbol, rsi_history)

    if len(rsi_history) < 4:
        print(f"⏳ {symbol}: Warte auf 4 RSI-Werte...")
        return

    state = get_state(symbol)
    streak_under = sum(1 for r in rsi_history if r < 30)
    streak_over = sum(1 for r in rsi_history if r > 70)

    if streak_under == 4 and state != "under_30_4":
        msg = f"⚠️ {symbol} RSI < 30 seit 4x 4h-Kerzen\nLetzter RSI: {current_rsi:.2f}\n🔎 Long Setup möglich"
        send_telegram_message(msg)
        set_state(symbol, "under_30_4")

    elif streak_over == 4 and state != "over_70_4":
        msg = f"⚠️ {symbol} RSI > 70 seit 4x 4h-Kerzen\nLetzter RSI: {current_rsi:.2f}\n🔎 Short Setup denkbar"
        send_telegram_message(msg)
        set_state(symbol, "over_70_4")

    elif 1 <= streak_under < 4 and state != f"under_30_{streak_under}":
        msg = f"⚠️ {symbol} RSI < 30 seit {streak_under}x 4h-Kerzen\nLetzter RSI: {current_rsi:.2f}"
        send_telegram_message(msg)
        set_state(symbol, f"under_30_{streak_under}")

    elif 1 <= streak_over < 4 and state != f"over_70_{streak_over}":
        msg = f"⚠️ {symbol} RSI > 70 seit {streak_over}x 4h-Kerzen\nLetzter RSI: {current_rsi:.2f}"
        send_telegram_message(msg)
        set_state(symbol, f"over_70_{streak_over}")

    elif streak_under == 0 and streak_over == 0 and state != "neutral":
        print(f"ℹ️ {symbol}: RSI neutral – zurückgesetzt.")
        set_state(symbol, "neutral")
    else:
        print(f"✅ {symbol}: Kein neues Signal.")

# === MAIN LOOP ===
def run():
    print("\n🔍 RSI-Streak-Check für CMC-Top-Coins via Binance...\n")
    symbols = get_top_50_cmc_symbols()
    print(f"📈 {len(symbols)} Symbole geladen: {symbols[:5]}...")
    for symbol in symbols:
        check_rsi_streak(symbol)
        time.sleep(1.2)

if __name__ == "__main__":
    run()
