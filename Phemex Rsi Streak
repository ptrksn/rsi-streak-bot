import requests
import time
import numpy as np
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PHEMEX_API_URL = "https://api.phemex.com/md/kline"

# Nur Perpetual-Symbole von Phemex (Beispiel)
PHEMEX_SYMBOLS = [
    "BTCUSD", "ETHUSD", "XRPUSD", "LINKUSD", "LTCUSD",
    "ADAUSD", "DOTUSD", "UNIUSD", "AAVEUSD", "BCHUSD"
]

# RSI-Berechnung (ohne pandas_ta)
def compute_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
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

# Telegram-Nachricht senden
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Token oder Chat-ID fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"❌ Fehler beim Senden: {e}")

# OHLC abrufen (je 4h-Kerze)
def fetch_ohlc(symbol):
    try:
        url = f"{PHEMEX_API_URL}?symbol={symbol}&resolution=4h&limit=20"
        response = requests.get(url)
        data = response.json()
        candles = data.get("data")
        if candles and len(candles) >= 20:
            close_prices = [float(c[4]) for c in candles]
            return close_prices
    except Exception as e:
        print(f"❌ {symbol} Fehler bei OHLC: {e}")
    return None

# Hauptfunktion
def main():
    print("🔍 RSI-Streak-Analyse für Phemex...")
    summary = "✨ RSI-Streak-Report (Phemex)\n"

    for symbol in PHEMEX_SYMBOLS:
        prices = fetch_ohlc(symbol)
        if prices:
            rsi_values = compute_rsi(prices)
            last_rsi = rsi_values[-1]
            streak_under = sum(1 for r in rsi_values[-4:] if r < 30)
            streak_over = sum(1 for r in rsi_values[-4:] if r > 70)

            summary += f"\n▶ï¸ {symbol} | RSI: {last_rsi:.2f} | Kerzen: {len(prices)}"
            if streak_under == 4:
                summary += "\n⬆️ Mögliches LONG-Setup (4x RSI < 30)"
            elif streak_over == 4:
                summary += "\n🔽 Mögliches SHORT-Setup (4x RSI > 70)"
            else:
                summary += f"\n⏳ Noch kein klares Setup (RSI-Streak unter/ober: {streak_under}/{streak_over})"
        else:
            summary += f"\n❌ {symbol}: Keine OHLC-Daten."
        time.sleep(1)

    print(summary)
    send_telegram_message(summary)

if __name__ == "__main__":
    main()
