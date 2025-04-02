import os
from tradingview_ta import TA_Handler, Interval
import time
import datetime
import requests

# === Telegram Setup ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Liste relevanter Symbole ===
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT"
]

# === Funktion: Telegram senden ===
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"❌ Fehler beim Senden der Telegram-Nachricht: {e}")

# === Hauptfunktion ===
def check_rsi_streak():
    print("\U0001F50D RSI-Streak-Check via TradingView...")
    for symbol in SYMBOLS:
        print(f"\n\U0001F4CA {symbol}...")
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="crypto",
                exchange="BINANCE",
                interval=Interval.INTERVAL_4_HOURS
            )
            analysis = handler.get_analysis()
            rsi_values = analysis.indicators.get("RSI")

            if isinstance(rsi_values, list):
                current_rsi = rsi_values[-1]
            else:
                current_rsi = rsi_values

            print(f"Aktueller RSI: {current_rsi:.2f}")

            # RSI-Streak analysieren
            rsi_streak = analysis.indicators.get("RSI")
            candles = analysis.indicators.get("RSI")[-4:] if isinstance(rsi_values, list) else [current_rsi]
            streak_count = 0
            direction = None

            for val in reversed(candles):
                if val < 30:
                    if direction == "short":
                        break
                    direction = "long"
                    streak_count += 1
                elif val > 70:
                    if direction == "long":
                        break
                    direction = "short"
                    streak_count += 1
                else:
                    break

            # Telegram-Benachrichtigung
            if streak_count >= 4:
                if direction == "long":
                    msg = f"\U0001F4CA {symbol}\nAktueller RSI: {current_rsi:.2f}\n\u2B07\uFE0F RSI < 30 seit {streak_count} Kerzen → Long-Szenario denkbar"
                else:
                    msg = f"\U0001F4CA {symbol}\nAktueller RSI: {current_rsi:.2f}\n\u2B06\uFE0F RSI > 70 seit {streak_count} Kerzen → Short-Szenario denkbar"
                print(msg)
                send_telegram(msg)
            else:
                print("ℹ️ Kein RSI-Streak.")

        except Exception as e:
            print(f"❌ Fehler bei {symbol}: {e}")

    print("\n✅ RSI-Analyse abgeschlossen.")

# === Ausführen ===
if __name__ == "__main__":
    check_rsi_streak()
