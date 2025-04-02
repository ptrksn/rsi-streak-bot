import os
import requests
from tradingview_ta import TA_Handler, Interval
import time

# === Telegram ===
def send_telegram_message(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# === Konfiguration ===
COINS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT"
]
INTERVAL = Interval.INTERVAL_4_HOURS

print("\U0001F50D RSI-Streak-Check via TradingView...")

# === Funktion zur RSI-Streak-Prüfung ===
def is_rsi_streak(rsi_values, oversold=True, streak_len=4):
    threshold = 30 if oversold else 70
    cmp = (lambda x: x < threshold) if oversold else (lambda x: x > threshold)
    return all(cmp(val) for val in rsi_values[-streak_len:])

# === Analyse ===
for symbol in COINS:
    print(f"\n📊 {symbol}...")
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="BINANCE",
            interval=INTERVAL
        )
        analysis = handler.get_analysis()
        rsi_values = analysis.indicators.get("RSI", None)

        if rsi_values is None:
            print("⚠️ Kein RSI-Wert gefunden.")
            continue

        print(f"Aktueller RSI: {rsi_values:.2f}")

        # Streak-Prüfung
        hist = handler.get_analysis().oscillators["COMPUTE"]
        rsi_list = [ind["RSI"] for ind in handler.get_analysis().indicators_list[-4:]] if hasattr(handler.get_analysis(), 'indicators_list') else []

        if len(rsi_list) >= 4:
            if is_rsi_streak(rsi_list, oversold=True):
                msg = f"🚨 RSI-Streak erkannt bei {symbol} (RSI < 30, letzte 4x 4h)"
                print(msg)
                send_telegram_message(msg)
            elif is_rsi_streak(rsi_list, oversold=False):
                msg = f"🚨 RSI-Streak erkannt bei {symbol} (RSI > 70, letzte 4x 4h)"
                print(msg)
                send_telegram_message(msg)
            else:
                print("ℹ️ Kein RSI-Streak.")
        else:
            print("⏳ Warte auf 4 RSI-Werte...")

        time.sleep(1)

    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")

print("✅ RSI-Analyse abgeschlossen.")
