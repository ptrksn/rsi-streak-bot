import os
import time
import requests
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TV_INTERVAL = Interval.INTERVAL_4_HOURS
RSI_PERIOD = 14
CMC_LIMIT = 50

# Hole Top-Coins von CoinMarketCap
def get_top_symbols():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"limit": CMC_LIMIT, "sort": "volume_24h"}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        symbols = [item["symbol"] + "USDT" for item in data["data"]]
        return symbols
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Top-Coins: {e}")
        return []

# Prüfe ob Symbol über TradingView analysierbar ist
def is_valid_symbol(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="PHEMEX",
            interval=TV_INTERVAL
        )
        _ = handler.get_analysis()
        return True
    except:
        return False

# RSI-Werte abrufen
def get_rsi_values(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange="PHEMEX",
            interval=TV_INTERVAL
        )
        rsi_series = handler.get_analysis().indicators
        return rsi_series["RSI"] if "RSI" in rsi_series else None
    except Exception as e:
        print(f"❌ Fehler bei {symbol}: {e}")
        return None

# Telegram senden
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram-Konfiguration fehlt.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        print("❌ Fehler beim Telegram-Versand:", e)

# Hauptlogik
def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    message_lines = [f"📊 RSI-Streak-Report ({now})\n"]

    all_symbols = get_top_symbols()
    valid_symbols = []
    print(f"📈 Prüfe {len(all_symbols)} CMC-Symbole auf Phemex-Verfügbarkeit...")
    for symbol in all_symbols:
        if is_valid_symbol(symbol):
            valid_symbols.append(symbol)
            time.sleep(1)

    print(f"✅ {len(valid_symbols)} gültige Symbole: {valid_symbols}")

    streaks = []
    for symbol in valid_symbols:
        rsi = get_rsi_values(symbol)
        if rsi is None:
            streaks.append(f"❌ {symbol}: Fehler bei RSI")
            continue

        status = "❌ Kein RSI-Streak"
        if rsi < 30:
            status = f"⚠️ {symbol}: RSI unter 30 – Long Setup denkbar"
        elif rsi > 70:
            status = f"⚠️ {symbol}: RSI über 70 – Short Setup denkbar"
        streaks.append(status)
        time.sleep(1)

    message_lines.append("\n".join(streaks))
    send_telegram("\n".join(message_lines))
    print("✅ RSI-Streak-Bericht gesendet.")

if __name__ == "__main__":
    main()
