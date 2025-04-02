import os
import time
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PHEMEX_BASE_URL = "https://api.phemex.com"

TOP_SYMBOLS = ["BTCUSD", "ETHUSD", "XRPUSD", "LINKUSD", "LTCUSD"]
VOLUME_SPIKE_THRESHOLD = 2.0  # Volumen muss doppelt so hoch wie vorher sein

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        print("❌ Fehler bei Telegram:", e)

def get_ohlc_volume(symbol):
    try:
        url = f"{PHEMEX_BASE_URL}/md/kline?symbol={symbol}&resolution=3600&limit=2"
        response = requests.get(url)
        data = response.json()
        if "data" in data and "rows" in data["data"]:
            rows = data["data"]["rows"]
            if len(rows) < 2:
                return None, None
            vol_old = float(rows[0][5])
            vol_new = float(rows[1][5])
            return vol_old, vol_new
        else:
            return None, None
    except Exception as e:
        print(f"⚠️ Fehler bei Volumenabruf für {symbol}: {e}")
        return None, None

def main():
    print("✅ Watchdog-Skript gestartet...")
    print("🔍 Überwache OHLC-Volumen...")

    messages = []

    for symbol in TOP_SYMBOLS:
        vol_old, vol_new = get_ohlc_volume(symbol)
        if vol_old is None or vol_new is None:
            print(f"⚠️ Nicht genügend OHLC-Daten für {symbol}")
            continue

        factor = vol_new / vol_old if vol_old > 0 else 0
        print(f"📊 {symbol}: Vorher: {vol_old:.2f}, Jetzt: {vol_new:.2f}, Faktor: {factor:.2f}")
        if factor >= VOLUME_SPIKE_THRESHOLD:
            msg = f"🚨 Volumen-Spike bei {symbol}! Anstieg um Faktor {factor:.2f}"
            messages.append(msg)

    if messages:
        final_message = "📈 Volume Watchdog Report:\n\n" + "\n\n".join(messages)
        send_telegram_message(final_message)
    else:
        print("ℹ️ Kein Volumenanstieg erkannt.")

    print("✅ Watchdog abgeschlossen.")

if __name__ == "__main__":
    main()
