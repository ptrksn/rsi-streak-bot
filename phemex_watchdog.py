import os
import time
import requests

print("✅ Watchdog-Skript gestartet...")

PHEMEX_BASE_URL = "https://api.phemex.com"
TOP_SYMBOLS = ["BTCUSD", "ETHUSD", "XRPUSD", "LINKUSD", "LTCUSD"]
VOLUME_SPIKE_THRESHOLD = 2.0  # Faktor

def get_recent_volume(symbol):
    try:
        url = f"{PHEMEX_BASE_URL}/md/kline?symbol={symbol}&resolution=3600&limit=2"
        response = requests.get(url)
        data = response.json()

        candles = data.get("data")
        if candles and len(candles) >= 2:
            prev_vol = float(candles[-2][5])
            curr_vol = float(candles[-1][5])
            return prev_vol, curr_vol
        else:
            print(f"⚠️ Nicht genügend OHLC-Daten für {symbol}")
            return None, None
    except Exception as e:
        print(f"❌ Fehler beim Abruf von OHLC-Daten für {symbol}: {e}")
        return None, None

def send_telegram_alert(symbol, factor):
    message = f"🚨 Volumen-Spike bei {symbol}! Faktor: {factor:.2f}"
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

def main():
    print("🔍 Überwache OHLC-Volumen...")
    for symbol in TOP_SYMBOLS:
        prev_vol, curr_vol = get_recent_volume(symbol)
        if prev_vol and curr_vol:
            factor = curr_vol / prev_vol if prev_vol > 0 else 0
            print(f"📊 {symbol}: Vorher: {prev_vol:.2f}, Jetzt: {curr_vol:.2f}, Faktor: {factor:.2f}")
            if factor >= VOLUME_SPIKE_THRESHOLD:
                send_telegram_alert(symbol, factor)
        time.sleep(1)
    print("✅ Watchdog abgeschlossen.")

if __name__ == "__main__":
    main()
