import os
import time
import requests
from tradingview_ta import TA_Handler, Interval

CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

INTERVAL = Interval.INTERVAL_4_HOURS
RSI_THRESHOLD_LOW = 30
RSI_THRESHOLD_HIGH = 70
RSI_STREAK_COUNT = 4

# === Funktion: Telegram senden ===
def send_telegram(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"⚠️ Telegram-Fehler: {e}")

# === Funktion: CMC Top Coins holen ===
def get_top_30_symbols():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"limit": 30, "sort": "volume_24h", "convert": "USD"}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        symbols = [entry["symbol"] + "USDT" for entry in data["data"] if entry["symbol"] != "USDT"]
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Abruf der CMC Top 30: {e}")
        return ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT"]

# === Funktion: RSI-Daten analysieren ===
def analyze_rsi_streak(symbol):
    handler = TA_Handler(
        symbol=symbol,
        screener="crypto",
        exchange="BINANCE",
        interval=INTERVAL
    )
    try:
        analysis = handler.get_analysis()
        rsi_series = analysis.indicators["RSI"]
        current_rsi = rsi_series
        print(f"📊 {symbol}...")
        print(f"Aktueller RSI: {current_rsi:.2f}")

        # RSI-Streak prüfen
        streak_direction = ""  # up/down
        streak_length = 0

        hist = analysis.indicators
        if "RSI[1]" in hist and "RSI[2]" in hist and "RSI[3]" in hist:
            rsi_values = [hist.get(f"RSI[{i}]", current_rsi) for i in range(3, -1, -1)]
            if all(r < RSI_THRESHOLD_LOW for r in rsi_values):
                streak_direction = "down"
                streak_length = 4
            elif all(r > RSI_THRESHOLD_HIGH for r in rsi_values):
                streak_direction = "up"
                streak_length = 4
            else:
                for i in range(3, -1, -1):
                    rsi = rsi_values[i]
                    if rsi < RSI_THRESHOLD_LOW:
                        if streak_direction == "down":
                            streak_length += 1
                        else:
                            streak_direction = "down"
                            streak_length = 1
                    elif rsi > RSI_THRESHOLD_HIGH:
                        if streak_direction == "up":
                            streak_length += 1
                        else:
                            streak_direction = "up"
                            streak_length = 1
                    else:
                        break

        # Ergebnis senden
        if streak_length >= RSI_STREAK_COUNT:
            msg = f"⚠️ {symbol} RSI {streak_direction} {streak_length}x in Folge. Setup denkbar."
            print(msg)
            send_telegram(msg)
        else:
            print(f"ℹ️ Kein RSI-Streak.")
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")

# === Hauptfunktion ===
def main():
    print("🔍 RSI-Streak-Check via TradingView...")
    symbols = get_top_30_symbols()
    print(f"📈 Analysiere {len(symbols)} Symbole: {symbols[:5]}...")
    for symbol in symbols:
        analyze_rsi_streak(symbol)
        time.sleep(1)  # zur Schonung der API
    print("✅ RSI-Analyse abgeschlossen.")

if __name__ == "__main__":
    main()
