import os
import requests
import time
import math
import numpy as np

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CMC_API_KEY = os.getenv("CMC_API_KEY")
PHEMEX_BASE_URL = "https://api.phemex.com"

INTERVAL = "4h"
LIMIT = 100
RSI_PERIOD = 14

HEADERS_CMC = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        print("❌ Fehler bei Telegram:", e)

def get_top_symbols_from_cmc(limit=30):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={limit}"
    try:
        response = requests.get(url, headers=HEADERS_CMC)
        data = response.json()
        symbols = [entry["symbol"] + "USD" for entry in data["data"]]
        return symbols
    except Exception as e:
        print("❌ Fehler beim Abruf der CMC-Daten:", e)
        return []

def get_ohlc_data(symbol):
    try:
        url = f"{PHEMEX_BASE_URL}/md/kline?symbol={symbol}&resolution=14400&limit={LIMIT}"
        response = requests.get(url)
        data = response.json()
        return [float(c[4]) for c in data["data"]["rows"]] if "data" in data else []
    except Exception as e:
        print(f"❌ Fehler bei OHLC für {symbol}:", e)
        return []

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return []

    deltas = np.diff(closes)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period if seed[seed < 0].sum() != 0 else 0.0001
    rs = up / down
    rsi = [100 - (100 / (1 + rs))]

    for delta in deltas[period:]:
        up = max(delta, 0)
        down = -min(delta, 0)
        rs = ((rs * (period - 1)) + (up / down if down != 0 else 0)) / period
        rsi.append(100 - (100 / (1 + rs)))

    return rsi

def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    symbols = get_top_symbols_from_cmc()
    print(f"📈 Analysiere {len(symbols)} Symbole: {symbols[:5]}...")

    messages = []
    for symbol in symbols:
        if not symbol.endswith("USD"):
            continue
        closes = get_ohlc_data(symbol)
        if len(closes) < RSI_PERIOD + 4:
            print(f"⚠️ Nicht genug OHLC-Daten für {symbol}")
            continue

        rsi_values = calculate_rsi(closes)
        last_rsi = rsi_values[-1]
        streak = 0
        for rsi in reversed(rsi_values[-4:]):
            if rsi < 30:
                streak -= 1
            elif rsi > 70:
                streak += 1
            else:
                break

        msg = f"📊 {symbol}...\nAktueller RSI: {last_rsi:.2f}"
        if streak <= -4:
            msg += f"\n📉 RSI-Streak unter 30 ({abs(streak)}x) – Long Setup denkbar."
        elif streak >= 4:
            msg += f"\n📈 RSI-Streak über 70 ({streak}x) – Short Setup denkbar."
        else:
            msg += f"\nℹ️ Kein RSI-Streak."

        print(msg)
        messages.append(msg)

    # Telegram-Nachricht zusammenfassen
    final_msg = "📣 RSI-Streak Report:\n\n" + "\n\n".join(messages)
    send_telegram_message(final_msg)
    print("✅ RSI-Analyse abgeschlossen.")

if __name__ == "__main__":
    main()
