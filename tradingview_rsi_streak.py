import os
import time
from tradingview_ta import TA_Handler, Interval
import datetime
import requests

# ==== Telegram Setup ====
def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("⚠️ Telegram-Umgebungsvariablen fehlen.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"❌ Telegram-Fehler: {response.text}")
    except Exception as e:
        print(f"❌ Telegram-Exception: {e}")

# ==== Coin-Liste ====
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT"
]

print("🔍 RSI-Streak-Check via TradingView...")

for symbol in SYMBOLS:
    print(f"📊 {symbol}...")
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange="BINANCE",
            screener="crypto",
            interval=Interval.INTERVAL_4_HOURS
        )
        analysis = handler.get_analysis()
        rsi_values = analysis.indicators.get("RSI", None)

        if rsi_values is None:
            print("⚠️ Kein RSI gefunden.")
            continue

        rsi = float(rsi_values)
        print(f"Aktueller RSI: {rsi:.2f}")

        # Streak-Erkennung
        if rsi < 30:
            print("⚠️ RSI unter 30 – mögliche Long-Situation")
            send_telegram(f"📉 {symbol} RSI < 30 – mögliche Long-Situation (RSI: {rsi:.2f})")
        elif rsi > 70:
            print("⚠️ RSI über 70 – mögliche Short-Situation")
            send_telegram(f"📈 {symbol} RSI > 70 – mögliche Short-Situation (RSI: {rsi:.2f})")
        else:
            print("ℹ️ Kein RSI-Streak.")
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")

print("✅ RSI-Analyse abgeschlossen.")
send_telegram("✅ Testnachricht vom RSI-Streak-Bot.")
