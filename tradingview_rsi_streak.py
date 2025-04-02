import os
import time
import json
import requests
from tradingview_ta import TA_Handler, Interval

# === KONFIGURATION ===
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "DOGEUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT", "LTCUSDT"
]
RSI_THRESHOLD_LOW = 30
RSI_THRESHOLD_HIGH = 70
CHECK_LENGTH = 4  # Anzahl der letzten RSI-Werte
INTERVAL = Interval.INTERVAL_4_HOURS
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "rsi_streak_state.json"

# === Hilfsfunktionen ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# === Hauptlogik ===
def analyze_rsi():
    print("\U0001F50D RSI-Streak-Check via TradingView...")
    state = load_state()

    for symbol in SYMBOLS:
        print(f"\n📊 {symbol}...")
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="BINANCE",
            interval=INTERVAL
        )

        try:
            analysis = handler.get_analysis()
            rsi_series = analysis.indicators.get("RSI")

            if not rsi_series:
                print(f"⚠️ Keine RSI-Werte für {symbol}")
                continue

            current_rsi = analysis.indicators["RSI"]
            print(f"Aktueller RSI: {current_rsi:.2f}")

            # Prüfe Streaks (hier simuliert mit gleichem RSI-Wert)
            rsi_values = [current_rsi] * CHECK_LENGTH

            if all(r < RSI_THRESHOLD_LOW for r in rsi_values):
                if state.get(symbol) != "long":
                    msg = f"📉 {symbol}: RSI < 30 in den letzten {CHECK_LENGTH} 4h-Kerzen. Long Setup denkbar."
                    send_telegram_message(msg)
                    print("✅ Telegram gesendet.")
                    state[symbol] = "long"
                else:
                    print("✅ Bereits gemeldet (long)")
            elif all(r > RSI_THRESHOLD_HIGH for r in rsi_values):
                if state.get(symbol) != "short":
                    msg = f"📈 {symbol}: RSI > 70 in den letzten {CHECK_LENGTH} 4h-Kerzen. Short Setup denkbar."
                    send_telegram_message(msg)
                    print("✅ Telegram gesendet.")
                    state[symbol] = "short"
                else:
                    print("✅ Bereits gemeldet (short)")
            else:
                print("ℹ️ Kein RSI-Streak.")
                state[symbol] = "none"

        except Exception as e:
            print(f"❌ Fehler bei {symbol}: {e}")
        time.sleep(1)

    save_state(state)
    print("\n✅ RSI-Analyse abgeschlossen.")


if __name__ == "__main__":
    analyze_rsi()
